import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import csv
from datetime import datetime
import os

def main():
    # Carregar modelo YOLO
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker
    tracker = Tracker()
    tracker.reid_threshold = 0.1  # Threshold muito baixo para testar
    
    # Abrir vídeo
    video_path = 'people.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Erro: Não foi possível abrir o vídeo {video_path}")
        return
    
    # Obter informações do vídeo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    # Dicionários para armazenar dados
    tracking_data = []
    current_tracks = set()
    reid_count = 0
    
    frame_count = 0
    
    print("Iniciando debug de re-identificação...")
    print("Pressione 'q' para sair")
    
    while True:
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
                    # Filtrar apenas pessoas (classe 0)
                    if int(box.cls) == 0:
                        x1, y1, x2, y2 = box.xyxy[0]
                        confidence = float(box.conf[0])
                        detections.append([x1, y1, x2, y2, confidence])
        
        # Atualizar tracker
        tracker.update(frame, detections)
        
        # Processar tracks atuais
        current_frame_tracks = set()
        
        if tracker.tracks is not None:
            for track in tracker.tracks:
                track_id = track.track_id
                bbox = track.bbox
                
                current_frame_tracks.add(track_id)
                
                # Armazenar dados para CSV
                timestamp = frame_count / fps
                tracking_data.append([
                    frame_count,
                    timestamp,
                    track_id,
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    int((bbox[0] + bbox[2]) / 2),
                    int((bbox[1] + bbox[3]) / 2),
                    "Nenhuma",
                    confidence if 'confidence' in locals() else 0.0
                ])
        
        # Identificar pessoas que saíram
        for track_id in current_tracks - current_frame_tracks:
            print(f"Pessoa {track_id} saiu do quadro (frame {frame_count})")
        
        current_tracks = current_frame_tracks
        
        # Verificar se há pessoas na lista de saídas
        if len(tracker.exited_persons) > 0:
            print(f"Frame {frame_count}: {len(tracker.exited_persons)} pessoas na lista de saídas")
            
            # Verificar características da primeira pessoa que saiu
            if len(tracker.exited_persons) > 0:
                first_exited = tracker.exited_persons[0]
                features = first_exited['features']
                print(f"  - Pessoa {first_exited['track_id']}: características = {type(features)}, tamanho = {len(features) if hasattr(features, '__len__') else 'N/A'}")
        
        # Mostrar frame
        cv2.imshow('Debug Re-ID', frame)
        
        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Parar após alguns frames para debug
        if frame_count > 100:
            break
    
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    
    print(f"\nResumo do debug:")
    print(f"Total de pessoas que saíram: {len(tracker.exited_persons)}")
    print(f"Total de re-identificações: {reid_count}")
    
    # Verificar características das pessoas que saíram
    if len(tracker.exited_persons) > 0:
        print(f"\nDetalhes das pessoas que saíram:")
        for i, person in enumerate(tracker.exited_persons[:5]):  # Primeiras 5
            features = person['features']
            print(f"  {i+1}. ID {person['track_id']}: {type(features)}, tamanho = {len(features) if hasattr(features, '__len__') else 'N/A'}")

if __name__ == "__main__":
    main() 