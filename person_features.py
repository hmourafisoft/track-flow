import cv2
import numpy as np
from sklearn.cluster import KMeans
from collections import defaultdict
import json
from datetime import datetime
import os

class PersonFeatureExtractor:
    """Sistema de extração e mapeamento de características visuais de pessoas"""
    
    def __init__(self):
        self.person_features = {}  # {track_id: features}
        self.feature_history = defaultdict(list)  # Histórico de características por ID
        self.color_names = {
            'red': [0, 0, 255],
            'green': [0, 255, 0], 
            'blue': [255, 0, 0],
            'yellow': [0, 255, 255],
            'cyan': [255, 255, 0],
            'magenta': [255, 0, 255],
            'white': [255, 255, 255],
            'black': [0, 0, 0],
            'gray': [128, 128, 128],
            'orange': [0, 165, 255],
            'purple': [128, 0, 128],
            'brown': [42, 42, 165],
            'pink': [203, 192, 255]
        }
    
    def extract_person_features(self, frame, bbox, track_id):
        """Extrai características visuais de uma pessoa"""
        x1, y1, x2, y2 = map(int, bbox)
        
        # Extrair região da pessoa
        person_roi = frame[y1:y2, x1:x2]
        if person_roi.size == 0:
            return None
        
        features = {
            'track_id': track_id,
            'timestamp': datetime.now().isoformat(),
            'bbox': bbox,
            'colors': self.extract_dominant_colors(person_roi),
            'body_proportions': self.extract_body_proportions(bbox),
            'color_histogram': self.extract_color_histogram(person_roi),
            'texture_features': self.extract_texture_features(person_roi),
            'edge_density': self.extract_edge_density(person_roi),
            'brightness': self.extract_brightness(person_roi),
            'contrast': self.extract_contrast(person_roi)
        }
        
        # Armazenar características
        self.person_features[track_id] = features
        self.feature_history[track_id].append(features)
        
        return features
    
    def extract_dominant_colors(self, roi, n_colors=5):
        """Extrai as cores dominantes da região da pessoa"""
        # Redimensionar para processamento mais rápido
        roi_small = cv2.resize(roi, (50, 50))
        
        # Converter para formato adequado para K-means
        pixels = roi_small.reshape(-1, 3)
        
        if len(pixels) < n_colors:
            return []
        
        # Aplicar K-means para encontrar cores dominantes
        kmeans = KMeans(n_clusters=n_colors, random_state=42, n_init=10)
        kmeans.fit(pixels)
        
        # Obter cores dominantes
        colors = kmeans.cluster_centers_.astype(int)
        
        # Calcular porcentagem de cada cor
        labels = kmeans.labels_
        color_percentages = []
        for i in range(n_colors):
            percentage = (labels == i).sum() / len(labels) if labels is not None else 0
            color_percentages.append(percentage)
        
        # Combinar cores com porcentagens
        dominant_colors = []
        for i, color in enumerate(colors):
            color_name = self.get_color_name(color)
            dominant_colors.append({
                'rgb': color.tolist(),
                'name': color_name,
                'percentage': color_percentages[i]
            })
        
        # Ordenar por porcentagem
        dominant_colors.sort(key=lambda x: x['percentage'], reverse=True)
        return dominant_colors
    
    def get_color_name(self, rgb_color):
        """Converte RGB para nome da cor mais próxima"""
        min_distance = float('inf')
        closest_color = 'unknown'
        
        for color_name, color_rgb in self.color_names.items():
            distance = np.sqrt(sum((np.array(rgb_color) - np.array(color_rgb))**2))
            if distance < min_distance:
                min_distance = distance
                closest_color = color_name
        
        return closest_color
    
    def extract_body_proportions(self, bbox):
        """Extrai proporções do corpo"""
        x1, y1, x2, y2 = bbox
        width = x2 - x1
        height = y2 - y1
        
        return {
            'width': width,
            'height': height,
            'aspect_ratio': width / height if height > 0 else 0,
            'area': width * height,
            'is_tall': height > width * 1.5,
            'is_wide': width > height * 1.2
        }
    
    def extract_color_histogram(self, roi, bins=32):
        """Extrai histograma de cores"""
        # Converter para HSV para melhor análise de cores
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        
        # Calcular histogramas para H, S, V
        h_hist = cv2.calcHist([hsv], [0], None, [bins], [0, 180])
        s_hist = cv2.calcHist([hsv], [1], None, [bins], [0, 256])
        v_hist = cv2.calcHist([hsv], [2], None, [bins], [0, 256])
        
        # Normalizar histogramas
        h_hist = cv2.normalize(h_hist, h_hist).flatten()
        s_hist = cv2.normalize(s_hist, s_hist).flatten()
        v_hist = cv2.normalize(v_hist, v_hist).flatten()
        
        return {
            'hue_histogram': h_hist.tolist(),
            'saturation_histogram': s_hist.tolist(),
            'value_histogram': v_hist.tolist()
        }
    
    def extract_texture_features(self, roi):
        """Extrai características de textura"""
        # Converter para escala de cinza
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        
        # Aplicar filtros para extrair textura
        # Gradiente
        grad_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Magnitude do gradiente
        magnitude = np.sqrt(grad_x**2 + grad_y**2)
        
        # Características de textura
        texture_features = {
            'gradient_mean': np.mean(magnitude),
            'gradient_std': np.std(magnitude),
            'gradient_max': np.max(magnitude),
            'gray_mean': np.mean(gray),
            'gray_std': np.std(gray)
        }
        
        return texture_features
    
    def extract_edge_density(self, roi):
        """Calcula densidade de bordas"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        return edge_density
    
    def extract_brightness(self, roi):
        """Calcula brilho médio"""
        hsv = cv2.cvtColor(roi, cv2.COLOR_BGR2HSV)
        brightness = np.mean(hsv[:, :, 2])
        return brightness
    
    def extract_contrast(self, roi):
        """Calcula contraste"""
        gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        contrast = np.std(gray)
        return contrast
    
    def compare_person_features(self, features1, features2):
        """Compara características de duas pessoas"""
        if not features1 or not features2:
            return 0
        
        similarity_score = 0
        weights = {
            'colors': 0.3,
            'body_proportions': 0.2,
            'color_histogram': 0.25,
            'texture_features': 0.15,
            'brightness': 0.05,
            'contrast': 0.05
        }
        
        # Comparar cores dominantes
        color_similarity = self.compare_colors(
            features1.get('colors', []), 
            features2.get('colors', [])
        )
        similarity_score += weights['colors'] * color_similarity
        
        # Comparar proporções do corpo
        body_similarity = self.compare_body_proportions(
            features1.get('body_proportions', {}),
            features2.get('body_proportions', {})
        )
        similarity_score += weights['body_proportions'] * body_similarity
        
        # Comparar histogramas de cor
        hist_similarity = self.compare_histograms(
            features1.get('color_histogram', {}),
            features2.get('color_histogram', {})
        )
        similarity_score += weights['color_histogram'] * hist_similarity
        
        # Comparar características de textura
        texture_similarity = self.compare_texture_features(
            features1.get('texture_features', {}),
            features2.get('texture_features', {})
        )
        similarity_score += weights['texture_features'] * texture_similarity
        
        # Comparar brilho e contraste
        brightness_similarity = self.compare_scalar_values(
            features1.get('brightness', 0),
            features2.get('brightness', 0)
        )
        similarity_score += weights['brightness'] * brightness_similarity
        
        contrast_similarity = self.compare_scalar_values(
            features1.get('contrast', 0),
            features2.get('contrast', 0)
        )
        similarity_score += weights['contrast'] * contrast_similarity
        
        return similarity_score
    
    def compare_colors(self, colors1, colors2):
        """Compara cores dominantes"""
        if not colors1 or not colors2:
            return 0
        
        # Comparar cores por nome
        names1 = [c['name'] for c in colors1[:3]]  # Top 3 cores
        names2 = [c['name'] for c in colors2[:3]]
        
        common_colors = set(names1) & set(names2)
        color_similarity = len(common_colors) / max(len(names1), len(names2))
        
        return color_similarity
    
    def compare_body_proportions(self, props1, props2):
        """Compara proporções do corpo"""
        if not props1 or not props2:
            return 0
        
        # Comparar aspect ratio
        aspect_diff = abs(props1.get('aspect_ratio', 0) - props2.get('aspect_ratio', 0))
        aspect_similarity = max(0, 1 - aspect_diff)
        
        # Comparar se ambos são altos/baixos
        height_similarity = 1.0 if props1.get('is_tall', False) == props2.get('is_tall', False) else 0.5
        
        return (aspect_similarity + height_similarity) / 2
    
    def compare_histograms(self, hist1, hist2):
        """Compara histogramas usando correlação"""
        if not hist1 or not hist2:
            return 0
        
        similarities = []
        
        # Comparar histogramas H, S, V
        for channel in ['hue_histogram', 'saturation_histogram', 'value_histogram']:
            if channel in hist1 and channel in hist2:
                h1 = np.array(hist1[channel])
                h2 = np.array(hist2[channel])
                
                # Correlação de Pearson
                correlation = np.corrcoef(h1, h2)[0, 1]
                if not np.isnan(correlation):
                    similarities.append(max(0, correlation))
        
        return np.mean(similarities) if similarities else 0
    
    def compare_texture_features(self, tex1, tex2):
        """Compara características de textura"""
        if not tex1 or not tex2:
            return 0
        
        similarities = []
        
        for feature in ['gradient_mean', 'gradient_std', 'gray_mean', 'gray_std']:
            if feature in tex1 and feature in tex2:
                similarity = self.compare_scalar_values(tex1[feature], tex2[feature])
                similarities.append(similarity)
        
        return np.mean(similarities) if similarities else 0
    
    def compare_scalar_values(self, val1, val2):
        """Compara valores escalares"""
        if val1 == 0 and val2 == 0:
            return 1.0
        
        max_val = max(abs(val1), abs(val2))
        if max_val == 0:
            return 1.0
        
        diff = abs(val1 - val2) / max_val
        return max(0, 1 - diff)
    
    def get_person_features(self, track_id):
        """Retorna características de uma pessoa específica"""
        return self.person_features.get(track_id)
    
    def get_feature_history(self, track_id):
        """Retorna histórico de características de uma pessoa"""
        return self.feature_history.get(track_id, [])
    
    def save_features_to_file(self, filename=None):
        """Salva características em arquivo JSON"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"person_features_{timestamp}.json"
        
        # Converter numpy arrays para listas para serialização
        serializable_features = {}
        for track_id, features in self.person_features.items():
            serializable_features[track_id] = {}
            
            for key, value in features.items():
                if isinstance(value, np.ndarray):
                    serializable_features[track_id][key] = value.tolist()
                elif isinstance(value, np.floating):
                    serializable_features[track_id][key] = float(value)
                elif isinstance(value, np.integer):
                    serializable_features[track_id][key] = int(value)
                elif isinstance(value, dict):
                    # Processar dicionários aninhados
                    serializable_features[track_id][key] = {}
                    for sub_key, sub_value in value.items():
                        if isinstance(sub_value, np.ndarray):
                            serializable_features[track_id][key][sub_key] = sub_value.tolist()
                        elif isinstance(sub_value, np.floating):
                            serializable_features[track_id][key][sub_key] = float(sub_value)
                        elif isinstance(sub_value, np.integer):
                            serializable_features[track_id][key][sub_key] = int(sub_value)
                        else:
                            serializable_features[track_id][key][sub_key] = sub_value
                else:
                    serializable_features[track_id][key] = value
        
        with open(filename, 'w') as f:
            json.dump(serializable_features, f, indent=2)
        
        print(f"Características salvas em: {filename}")
        return filename
    
    def load_features_from_file(self, filename):
        """Carrega características de arquivo JSON"""
        with open(filename, 'r') as f:
            self.person_features = json.load(f)
        
        print(f"Características carregadas de: {filename}")
    
    def print_person_summary(self, track_id):
        """Imprime resumo das características de uma pessoa"""
        features = self.get_person_features(track_id)
        if not features:
            print(f"Pessoa {track_id}: Características não encontradas")
            return
        
        print(f"\n=== CARACTERÍSTICAS DA PESSOA {track_id} ===")
        print(f"Timestamp: {features['timestamp']}")
        print(f"BBox: {features['bbox']}")
        
        # Cores dominantes
        print("\n🎨 CORES DOMINANTES:")
        for i, color in enumerate(features['colors'][:3]):
            print(f"  {i+1}. {color['name']} ({color['percentage']:.1%})")
        
        # Proporções do corpo
        props = features['body_proportions']
        print(f"\n📏 PROPORÇÕES:")
        print(f"  Altura: {props['height']}px, Largura: {props['width']}px")
        print(f"  Aspect Ratio: {props['aspect_ratio']:.2f}")
        print(f"  Tipo: {'Alto' if props['is_tall'] else 'Baixo'}")
        
        # Características de textura
        tex = features['texture_features']
        print(f"\n🔍 TEXTURA:")
        print(f"  Densidade de bordas: {features['edge_density']:.3f}")
        print(f"  Brilho: {features['brightness']:.1f}")
        print(f"  Contraste: {features['contrast']:.1f}")
        
        print("=" * 50) 