from deep_sort.deep_sort.tracker import Tracker as DeepSortTracker
from deep_sort.tools import generate_detections as gdet
from deep_sort.deep_sort import nn_matching
from deep_sort.deep_sort.detection import Detection
import numpy as np
import cv2
from datetime import datetime, timedelta
from person_features import PersonFeatureExtractor

class Tracker:
    tracker = None
    encoder = None
    tracks = None
    exited_persons = []  # Lista de pessoas que saíram do quadro
    track_features = {}  # Dicionário para armazenar características por track_id
    reid_threshold = 0.3  # Threshold para re-identificação (reduzido de 0.7 para 0.3)
    max_exit_time = 30  # Tempo máximo (segundos) para considerar re-identificação
    feature_extractor = None  # Extrator de características visuais

    def __init__(self):
        max_cosine_distance = 0.3
        nn_budget = 100

        encoder_model_filename = 'model_data/mars-small128.pb'

        metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
        self.tracker = DeepSortTracker(metric)
        self.encoder = gdet.create_box_encoder(encoder_model_filename, batch_size=1)
        
        # Inicializar extrator de características
        self.feature_extractor = PersonFeatureExtractor()

    def update(self, frame, detections):
        if len(detections) == 0:
            if self.tracker is not None:
                self.tracker.predict()
                self.tracker.update([])
            self.update_tracks()
            return

        bboxes = np.asarray([d[:-1] for d in detections])
        bboxes[:, 2:] = bboxes[:, 2:] - bboxes[:, 0:2]
        scores = [d[-1] for d in detections]

        if self.encoder is not None:
            features = self.encoder(frame, bboxes)
        else:
            features = np.zeros((len(bboxes), 128))  # Fallback

        detections_with_reid = []
        for bbox_id, bbox in enumerate(bboxes):
            # Tentar re-identificar com pessoas que saíram
            reid_id = self.try_reidentify(features[bbox_id], bbox, frame)
            detections_with_reid.append(Detection(bbox, scores[bbox_id], features[bbox_id]))

        if self.tracker is not None:
            self.tracker.predict()
            self.tracker.update(detections_with_reid)
            
            # Armazenar características dos tracks ativos
            self.store_track_features(features, bboxes, frame)
            
        self.update_tracks()
        
        # Atualizar lista de pessoas que saíram
        self.update_exited_persons()

    def store_track_features(self, features, bboxes, frame):
        """Armazena características dos tracks ativos"""
        if self.tracker is not None and hasattr(self.tracker, 'tracks'):
            for track in self.tracker.tracks:
                if track.is_confirmed() and track.time_since_update <= 1:  # Track ativo
                    # Encontrar a detecção correspondente a este track
                    track_bbox = track.to_tlbr()
                    best_match_idx = -1
                    best_iou = 0
                    
                    for i, bbox in enumerate(bboxes):
                        # Converter bbox para formato tlbr
                        bbox_tlbr = [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]
                        
                        # Calcular IoU
                        iou = self.calculate_iou(track_bbox, bbox_tlbr)
                        if iou > best_iou:
                            best_iou = iou
                            best_match_idx = i
                    
                    # Se encontrou uma correspondência com IoU > 0.5, armazenar características
                    if best_match_idx >= 0 and best_iou > 0.5:
                        self.track_features[track.track_id] = features[best_match_idx]
                        
                        # Extrair características visuais detalhadas
                        bbox_tlbr = [bboxes[best_match_idx][0], bboxes[best_match_idx][1], 
                                   bboxes[best_match_idx][0] + bboxes[best_match_idx][2], 
                                   bboxes[best_match_idx][1] + bboxes[best_match_idx][3]]
                        
                        if self.feature_extractor:
                            visual_features = self.feature_extractor.extract_person_features(
                                frame, bbox_tlbr, track.track_id
                            )

    def calculate_iou(self, bbox1, bbox2):
        """Calcula o IoU entre duas bounding boxes"""
        x1 = max(bbox1[0], bbox2[0])
        y1 = max(bbox1[1], bbox2[1])
        x2 = min(bbox1[2], bbox2[2])
        y2 = min(bbox1[3], bbox2[3])
        
        intersection = max(0, x2 - x1) * max(0, y2 - y1)
        area1 = (bbox1[2] - bbox1[0]) * (bbox1[3] - bbox1[1])
        area2 = (bbox2[2] - bbox2[0]) * (bbox2[3] - bbox2[1])
        union = area1 + area2 - intersection
        
        return intersection / union if union > 0 else 0

    def try_reidentify(self, features, bbox, frame):
        """Tenta re-identificar uma pessoa com base nas características visuais"""
        current_time = datetime.now()
        
        # Extrair características visuais da detecção atual
        current_visual_features = None
        if self.feature_extractor:
            bbox_tlbr = [bbox[0], bbox[1], bbox[0] + bbox[2], bbox[1] + bbox[3]]
            current_visual_features = self.feature_extractor.extract_person_features(
                frame, bbox_tlbr, None  # ID temporário
            )
        
        best_match_id = None
        best_similarity = 0
        
        for exited_person in self.exited_persons:
            # Verificar se ainda está dentro do tempo limite
            if (current_time - exited_person['exit_time']).seconds > self.max_exit_time:
                continue
            
            # Calcular similaridade entre características do Deep SORT
            deepsort_similarity = self.calculate_similarity(features, exited_person['features'])
            
            # Calcular similaridade entre características visuais
            visual_similarity = 0
            if current_visual_features and 'visual_features' in exited_person and self.feature_extractor:
                visual_similarity = self.feature_extractor.compare_person_features(
                    current_visual_features, exited_person['visual_features']
                )
            
            # Combinar similaridades (70% Deep SORT + 30% características visuais)
            combined_similarity = 0.7 * deepsort_similarity + 0.3 * visual_similarity
            
            if combined_similarity > self.reid_threshold and combined_similarity > best_similarity:
                best_similarity = combined_similarity
                best_match_id = exited_person['track_id']
        
        if best_match_id:
            print(f"Re-identificação: Pessoa {best_match_id} retornou ao quadro "
                  f"(similaridade: {best_similarity:.3f})")
        
        return best_match_id

    def calculate_similarity(self, features1, features2):
        """Calcula a similaridade entre dois vetores de características"""
        # Converter para numpy array se não for
        if features1 is None or features2 is None:
            return 0
        features1 = np.asarray(features1)
        features2 = np.asarray(features2)
        if features1.size == 0 or features2.size == 0:
            return 0
        if features1.shape != features2.shape:
            return 0
        # Usar distância cosseno (1 = idêntico, 0 = completamente diferente)
        dot_product = np.dot(features1, features2)
        norm1 = np.linalg.norm(features1)
        norm2 = np.linalg.norm(features2)
        if norm1 == 0 or norm2 == 0:
            return 0
        similarity = dot_product / (norm1 * norm2)
        return similarity

    def update_exited_persons(self):
        """Atualiza a lista de pessoas que saíram do quadro"""
        current_time = datetime.now()
        
        # Remover pessoas que saíram há muito tempo
        self.exited_persons = [
            person for person in self.exited_persons 
            if (current_time - person['exit_time']).seconds <= self.max_exit_time
        ]
        
        # Adicionar pessoas que acabaram de sair
        if self.tracks is not None:
            current_track_ids = {track.track_id for track in self.tracks}
        else:
            current_track_ids = set()
        
        if self.tracker is not None and hasattr(self.tracker, 'tracks'):
            for track in self.tracker.tracks:
                if track.is_confirmed() and track.time_since_update > 5:  # Pessoa saiu há 5 frames
                    if track.track_id not in current_track_ids:
                        # Verificar se temos características armazenadas para este track
                        if track.track_id in self.track_features:
                            features = self.track_features[track.track_id]
                            
                            # Obter características visuais
                            visual_features = None
                            if self.feature_extractor:
                                visual_features = self.feature_extractor.get_person_features(track.track_id)
                            
                            exited_person = {
                                'track_id': track.track_id,
                                'features': features,
                                'visual_features': visual_features,
                                'exit_time': current_time,
                                'last_bbox': track.to_tlbr()
                            }
                            self.exited_persons.append(exited_person)
                            print(f"Pessoa {track.track_id} saiu do quadro - COM características visuais")
                        else:
                            print(f"Pessoa {track.track_id} saiu do quadro - SEM características")

    def update_tracks(self):
        tracks = []
        if self.tracker is not None and hasattr(self.tracker, 'tracks'):
            for track in self.tracker.tracks:
                if not track.is_confirmed() or track.time_since_update > 3:
                    continue
                bbox = track.to_tlbr()
                id = track.track_id
                tracks.append(Track(id, bbox))
        self.tracks = tracks
    
    def save_person_features(self, filename=None):
        """Salva características das pessoas em arquivo"""
        if self.feature_extractor:
            return self.feature_extractor.save_features_to_file(filename)
        return None
    
    def print_person_features(self, track_id):
        """Imprime características de uma pessoa específica"""
        if self.feature_extractor:
            self.feature_extractor.print_person_summary(track_id)

class Track:
    track_id = None
    bbox = None

    def __init__(self, id, bbox):
        self.track_id = id
        self.bbox = bbox
