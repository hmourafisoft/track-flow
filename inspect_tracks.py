import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
from deep_sort.deep_sort.tracker import Tracker as DeepSortTracker
from deep_sort.tools import generate_detections as gdet
from deep_sort.deep_sort import nn_matching
from deep_sort.deep_sort.detection import Detection

def inspect_track_structure():
    """Inspeciona a estrutura dos tracks do Deep SORT"""
    
    # Inicializar tracker
    max_cosine_distance = 0.3
    nn_budget = 100
    encoder_model_filename = 'model_data/mars-small128.pb'
    
    metric = nn_matching.NearestNeighborDistanceMetric("cosine", max_cosine_distance, nn_budget)
    tracker = DeepSortTracker(metric)
    encoder = gdet.create_box_encoder(encoder_model_filename, batch_size=1)
    
    # Carregar modelo YOLO
    model = YOLO('yolov8n.pt')
    
    # Abrir vídeo
    video_path = 'people.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir o vídeo {video_path}")
        return
    
    frame_count = 0
    
    while frame_count < 50:  # Primeiros 50 frames
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detectar objetos
        results = model(frame, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    if int(box.cls) == 0:  # Pessoas
                        x1, y1, x2, y2 = box.xyxy[0]
                        confidence = float(box.conf[0])
                        detections.append([x1, y1, x2, y2, confidence])
        
        if len(detections) > 0:
            bboxes = np.asarray([d[:-1] for d in detections])
            bboxes[:, 2:] = bboxes[:, 2:] - bboxes[:, 0:2]
            scores = [d[-1] for d in detections]
            
            if encoder is not None:
                features = encoder(frame, bboxes)
            else:
                features = np.zeros((len(bboxes), 128))
            
            detections_with_features = []
            for bbox_id, bbox in enumerate(bboxes):
                detections_with_features.append(Detection(bbox, scores[bbox_id], features[bbox_id]))
            
            tracker.predict()
            tracker.update(detections_with_features)
            
            # Inspecionar tracks após alguns frames
            if frame_count > 10 and len(tracker.tracks) > 0:
                print(f"\nFrame {frame_count}: {len(tracker.tracks)} tracks")
                
                for i, track in enumerate(tracker.tracks[:3]):  # Primeiros 3 tracks
                    print(f"\nTrack {i+1} (ID: {track.track_id}):")
                    print(f"  - is_confirmed(): {track.is_confirmed()}")
                    print(f"  - time_since_update: {track.time_since_update}")
                    print(f"  - hasattr 'features': {hasattr(track, 'features')}")
                    
                    if hasattr(track, 'features'):
                        features = track.features
                        print(f"  - features type: {type(features)}")
                        print(f"  - features shape: {features.shape if hasattr(features, 'shape') else 'N/A'}")
                        print(f"  - features length: {len(features) if hasattr(features, '__len__') else 'N/A'}")
                        if hasattr(features, '__len__') and len(features) > 0:
                            print(f"  - features[0] type: {type(features[0])}")
                            print(f"  - features[0] shape: {features[0].shape if hasattr(features[0], 'shape') else 'N/A'}")
                            print(f"  - features[0] length: {len(features[0]) if hasattr(features[0], '__len__') else 'N/A'}")
                    
                    print(f"  - dir(track): {[attr for attr in dir(track) if not attr.startswith('_')]}")
                    break  # Só inspecionar o primeiro track
    
    cap.release()
    print("\nInspeção concluída!")

if __name__ == "__main__":
    inspect_track_structure() 