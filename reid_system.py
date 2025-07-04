import numpy as np
import cv2
from datetime import datetime, timedelta
from collections import defaultdict
import pickle
import os

class ReIdentificationSystem:
    def __init__(self, max_exit_time=30, similarity_threshold=0.7):
        self.max_exit_time = max_exit_time  # segundos
        self.similarity_threshold = similarity_threshold
        self.exited_persons = {}  # {track_id: person_data}
        self.person_history = defaultdict(list)  # Histórico de características por pessoa
        self.reid_matches = []  # Registro de re-identificações
        
    def extract_appearance_features(self, frame, bbox):
        """Extrai características visuais da pessoa"""
        x1, y1, x2, y2 = map(int, bbox)
        
        # Garantir que as coordenadas estão dentro dos limites da imagem
        h, w = frame.shape[:2]
        x1 = max(0, min(x1, w-1))
        y1 = max(0, min(y1, h-1))
        x2 = max(0, min(x2, w-1))
        y2 = max(0, min(y2, h-1))
        
        if x2 <= x1 or y2 <= y1:
            return None
            
        # Recortar a região da pessoa
        person_roi = frame[y1:y2, x1:x2]
        
        if person_roi.size == 0:
            return None
            
        features = {
            'color_histogram': self.extract_color_histogram(person_roi),
            'height_width_ratio': (y2 - y1) / (x2 - x1),
            'area': (x2 - x1) * (y2 - y1),
            'center_position': ((x1 + x2) / 2, (y1 + y2) / 2)
        }
        
        return features
    
    def extract_color_histogram(self, roi):
        """Extrai histograma de cores da região da pessoa"""
        # Converter para HSV para melhor análise de cores
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Calcular histograma para cada canal
        hist_h = cv2.calcHist([hsv], [0], None, [30], [0, 180])
        hist_s = cv2.calcHist([hsv], [1], None, [32], [0, 256])
        hist_v = cv2.calcHist([hsv], [2], None, [32], [0, 256])
        
        # Normalizar histogramas
        hist_h = cv2.normalize(hist_h, hist_h).flatten()
        hist_s = cv2.normalize(hist_s, hist_s).flatten()
        hist_v = cv2.normalize(hist_v, hist_v).flatten()
        
        return np.concatenate([hist_h, hist_s, hist_v])
    
    def calculate_similarity(self, features1, features2):
        """Calcula similaridade entre duas pessoas"""
        if features1 is None or features2 is None:
            return 0.0
            
        similarities = []
        
        # Similaridade de histograma de cores
        if 'color_histogram' in features1 and 'color_histogram' in features2:
            color_sim = cv2.compareHist(
                features1['color_histogram'], 
                features2['color_histogram'], 
                cv2.HISTCMP_CORREL
            )
            similarities.append(max(0, color_sim))  # Normalizar para [0, 1]
        
        # Similaridade de proporções
        if 'height_width_ratio' in features1 and 'height_width_ratio' in features2:
            ratio_diff = abs(features1['height_width_ratio'] - features2['height_width_ratio'])
            ratio_sim = max(0, 1 - ratio_diff / 2)  # Normalizar diferença
            similarities.append(ratio_sim)
        
        # Similaridade de área (tamanho)
        if 'area' in features1 and 'area' in features2:
            area_diff = abs(features1['area'] - features2['area'])
            max_area = max(features1['area'], features2['area'])
            if max_area > 0:
                area_sim = max(0, 1 - area_diff / max_area)
                similarities.append(area_sim)
        
        # Similaridade de posição (se disponível)
        if 'center_position' in features1 and 'center_position' in features2:
            pos1 = features1['center_position']
            pos2 = features2['center_position']
            distance = np.sqrt((pos1[0] - pos2[0])**2 + (pos1[1] - pos2[1])**2)
            # Normalizar pela diagonal da imagem (assumindo 640x480)
            max_distance = np.sqrt(640**2 + 480**2)
            pos_sim = max(0, 1 - distance / max_distance)
            similarities.append(pos_sim)
        
        # Retornar média das similaridades
        return np.mean(similarities) if similarities else 0.0
    
    def add_exited_person(self, track_id, features, bbox, exit_time=None):
        """Adiciona uma pessoa que saiu do quadro"""
        if exit_time is None:
            exit_time = datetime.now()
            
        self.exited_persons[track_id] = {
            'features': features,
            'bbox': bbox,
            'exit_time': exit_time,
            'reid_attempts': 0
        }
        
        print(f"Pessoa {track_id} adicionada à lista de pessoas que saíram")
    
    def try_reidentify(self, features, bbox, current_time=None):
        """Tenta re-identificar uma pessoa"""
        if current_time is None:
            current_time = datetime.now()
        
        best_match = None
        best_similarity = 0
        
        # Limpar pessoas que saíram há muito tempo
        expired_ids = []
        for track_id, person_data in self.exited_persons.items():
            if (current_time - person_data['exit_time']).seconds > self.max_exit_time:
                expired_ids.append(track_id)
        
        for track_id in expired_ids:
            del self.exited_persons[track_id]
        
        # Tentar re-identificação
        for track_id, person_data in self.exited_persons.items():
            similarity = self.calculate_similarity(features, person_data['features'])
            
            if similarity > self.similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = track_id
        
        if best_match:
            # Registrar re-identificação
            self.reid_matches.append({
                'original_id': best_match,
                'new_detection_time': current_time,
                'similarity': best_similarity,
                'exit_duration': (current_time - self.exited_persons[best_match]['exit_time']).seconds
            })
            
            print(f"Re-identificação bem-sucedida: Pessoa {best_match} retornou (similaridade: {best_similarity:.3f})")
            
            # Remover da lista de pessoas que saíram
            del self.exited_persons[best_match]
            
            return best_match
        
        return None
    
    def get_reid_statistics(self):
        """Retorna estatísticas de re-identificação"""
        if not self.reid_matches:
            return {
                'total_reid_matches': 0,
                'average_similarity': 0,
                'average_exit_duration': 0
            }
        
        similarities = [match['similarity'] for match in self.reid_matches]
        exit_durations = [match['exit_duration'] for match in self.reid_matches]
        
        return {
            'total_reid_matches': len(self.reid_matches),
            'average_similarity': np.mean(similarities),
            'average_exit_duration': np.mean(exit_durations),
            'max_exit_duration': max(exit_durations),
            'min_exit_duration': min(exit_durations)
        }
    
    def save_reid_data(self, filename='reid_data.pkl'):
        """Salva dados de re-identificação"""
        data = {
            'reid_matches': self.reid_matches,
            'exited_persons': self.exited_persons,
            'person_history': dict(self.person_history)
        }
        
        with open(filename, 'wb') as f:
            pickle.dump(data, f)
        
        print(f"Dados de re-identificação salvos em {filename}")
    
    def load_reid_data(self, filename='reid_data.pkl'):
        """Carrega dados de re-identificação"""
        if os.path.exists(filename):
            with open(filename, 'rb') as f:
                data = pickle.load(f)
            
            self.reid_matches = data.get('reid_matches', [])
            self.exited_persons = data.get('exited_persons', {})
            self.person_history = defaultdict(list, data.get('person_history', {}))
            
            print(f"Dados de re-identificação carregados de {filename}")
            return True
        return False 