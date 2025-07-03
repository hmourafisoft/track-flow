import numpy as np
import cv2
from collections import deque

class Tracker:
    def __init__(self):
        self.tracks = []
        self.next_id = 0
        self.max_disappeared = 30
        self.max_distance = 50

    def update(self, frame, detections):
        if len(detections) == 0:
            # Se não há detecções, marcar todos os tracks como desaparecidos
            for track in self.tracks:
                track['disappeared'] += 1
            return

        # Converter detecções para formato [x1, y1, x2, y2, score]
        bboxes = np.array([d[:4] for d in detections])
        scores = np.array([d[4] for d in detections])

        # Se não há tracks, criar novos para todas as detecções
        if len(self.tracks) == 0:
            for bbox, score in zip(bboxes, scores):
                self.tracks.append({
                    'id': self.next_id,
                    'bbox': bbox,
                    'score': score,
                    'disappeared': 0,
                    'centroid': self._get_centroid(bbox)
                })
                self.next_id += 1
            return

        # Calcular centroides das detecções atuais
        centroids = np.array([self._get_centroid(bbox) for bbox in bboxes])
        
        # Calcular centroides dos tracks existentes
        track_centroids = np.array([track['centroid'] for track in self.tracks])
        
        # Calcular distâncias entre centroides
        distances = np.zeros((len(self.tracks), len(centroids)))
        for i, track_centroid in enumerate(track_centroids):
            for j, centroid in enumerate(centroids):
                distances[i, j] = np.linalg.norm(track_centroid - centroid)

        # Associação simples baseada em distância mínima
        used_tracks = set()
        used_detections = set()
        
        # Associar detecções aos tracks mais próximos
        for _ in range(min(len(self.tracks), len(centroids))):
            min_dist = float('inf')
            track_idx = -1
            detection_idx = -1
            
            for i in range(len(self.tracks)):
                if i in used_tracks:
                    continue
                for j in range(len(centroids)):
                    if j in used_detections:
                        continue
                    if distances[i, j] < min_dist and distances[i, j] < self.max_distance:
                        min_dist = distances[i, j]
                        track_idx = i
                        detection_idx = j
            
            if track_idx != -1 and detection_idx != -1:
                # Atualizar track
                self.tracks[track_idx]['bbox'] = bboxes[detection_idx]
                self.tracks[track_idx]['score'] = scores[detection_idx]
                self.tracks[track_idx]['centroid'] = centroids[detection_idx]
                self.tracks[track_idx]['disappeared'] = 0
                used_tracks.add(track_idx)
                used_detections.add(detection_idx)

        # Marcar tracks não associados como desaparecidos
        for i in range(len(self.tracks)):
            if i not in used_tracks:
                self.tracks[i]['disappeared'] += 1

        # Criar novos tracks para detecções não associadas
        for j in range(len(centroids)):
            if j not in used_detections:
                self.tracks.append({
                    'id': self.next_id,
                    'bbox': bboxes[j],
                    'score': scores[j],
                    'disappeared': 0,
                    'centroid': centroids[j]
                })
                self.next_id += 1

        # Remover tracks que desapareceram por muito tempo
        self.tracks = [track for track in self.tracks if track['disappeared'] < self.max_disappeared]

    def _get_centroid(self, bbox):
        x1, y1, x2, y2 = bbox
        return np.array([(x1 + x2) / 2, (y1 + y2) / 2])

    @property
    def tracks(self):
        return self._tracks

    @tracks.setter
    def tracks(self, value):
        self._tracks = value


class Track:
    def __init__(self, id, bbox):
        self.track_id = id
        self.bbox = bbox
