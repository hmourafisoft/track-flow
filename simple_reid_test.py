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
    
    # Inicializar tracker com threshold mais baixo
    tracker = Tracker()
    tracker.reid_threshold = 0.2  # Threshold muito baixo para testar
    
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
    
    # Configurar vídeo de saída
    output_path = 'output_simple_reid.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Dicionários para armazenar dados
    tracking_data = []
    person_positions = {}
    current_tracks = set()
    reid_count = 0
    
    frame_count = 0
    
    print("Iniciando teste simplificado de re-identificação...")
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
                
                # Calcular centro da bounding box
                center_x = int((bbox[0] + bbox[2]) / 2)
                center_y = int((bbox[1] + bbox[3]) / 2)
                
                # Armazenar posição
                if track_id not in person_positions:
                    person_positions[track_id] = []
                person_positions[track_id].append((frame_count, center_x, center_y))
                
                # Armazenar dados para CSV
                timestamp = frame_count / fps
                tracking_data.append([
                    frame_count,
                    timestamp,
                    track_id,
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    center_x, center_y,
                    "Nenhuma",
                    confidence if 'confidence' in locals() else 0.0
                ])
                
                # Desenhar bounding box e ID
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
                cv2.putText(frame, f'ID: {track_id}', (int(bbox[0]), int(bbox[1]) - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Desenhar trajetória
                if track_id in person_positions and len(person_positions[track_id]) > 1:
                    positions = person_positions[track_id][-30:]
                    for i in range(1, len(positions)):
                        cv2.line(frame, positions[i-1][1:], positions[i][1:], (255, 0, 0), 2)
        
        # Identificar pessoas que saíram
        for track_id in current_tracks - current_frame_tracks:
            print(f"Pessoa {track_id} saiu do quadro (frame {frame_count})")
        
        current_tracks = current_frame_tracks
        
        # Mostrar estatísticas
        cv2.putText(frame, f'Pessoas que saíram: {len(tracker.exited_persons)}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f'Re-ID Matches: {reid_count}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar frame
        cv2.imshow('Simple Re-ID Test', frame)
        
        # Salvar frame no vídeo de saída
        out.write(frame)
        
        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Liberar recursos
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    # Gerar relatório
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_filename = f'simple_reid_report_{timestamp}.csv'
    
    with open(report_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['frame', 'timestamp', 'track_id', 'x1', 'y1', 'x2', 'y2', 'center_x', 'center_y', 'zone', 'confidence'])
        writer.writerows(tracking_data)
    
    print(f"Relatório salvo em: {report_filename}")
    print(f"Total de pessoas que saíram: {len(tracker.exited_persons)}")
    print(f"Total de re-identificações: {reid_count}")

if __name__ == "__main__":
    main() 