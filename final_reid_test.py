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
    tracker.reid_threshold = 0.5  # Threshold mais razoável
    tracker.max_exit_time = 30  # 30 segundos para re-identificação
    
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
    exited_count = 0
    
    frame_count = 0
    
    print("=== TESTE FINAL DE RE-IDENTIFICAÇÃO ===")
    print(f"Threshold: {tracker.reid_threshold}")
    print(f"Tempo máximo para re-identificação: {tracker.max_exit_time} segundos")
    print("Pressione 'q' para sair")
    print("=" * 50)
    
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
            print(f"Frame {frame_count}: Pessoa {track_id} saiu do quadro")
            exited_count += 1
        
        current_tracks = current_frame_tracks
        
        # Mostrar estatísticas a cada 100 frames
        if frame_count % 100 == 0:
            print(f"\n--- Frame {frame_count} ---")
            print(f"Pessoas atuais: {len(current_tracks)}")
            print(f"Pessoas que saíram: {exited_count}")
            print(f"Re-identificações: {reid_count}")
            print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
        
        # Mostrar frame
        cv2.imshow('Re-Identification Test', frame)
        
        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
        
        # Parar após alguns frames para teste
        if frame_count > 500:
            break
    
    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()
    
    # Salvar relatório CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"final_reid_report_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Frame', 'Timestamp', 'Track_ID', 'X1', 'Y1', 'X2', 'Y2', 'Center_X', 'Center_Y', 'Zone', 'Confidence'])
        writer.writerows(tracking_data)
    
    print(f"\n=== RESUMO FINAL ===")
    print(f"Total de frames processados: {frame_count}")
    print(f"Total de pessoas que saíram: {exited_count}")
    print(f"Total de re-identificações: {reid_count}")
    print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
    print(f"Relatório salvo em: {csv_filename}")
    
    # Mostrar detalhes das pessoas que saíram
    if len(tracker.exited_persons) > 0:
        print(f"\nDetalhes das pessoas que saíram:")
        for i, person in enumerate(tracker.exited_persons[:10]):  # Primeiras 10
            features = person['features']
            exit_time = person['exit_time']
            print(f"  {i+1}. ID {person['track_id']}: {type(features)}, tamanho = {len(features)}, saiu em {exit_time}")

if __name__ == "__main__":
    main() 