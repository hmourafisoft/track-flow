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
    
    # Inicializar tracker com características visuais
    tracker = Tracker()
    tracker.reid_threshold = 0.4  # Threshold otimizado
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
    current_persons = set()
    exited_persons_count = 0
    reid_count = 0
    
    frame_count = 0
    
    print("🎯 TESTE DO SISTEMA DE CARACTERÍSTICAS VISUAIS")
    print("=" * 60)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Detectar pessoas
        results = model(frame, classes=0)  # Classe 0 = pessoa
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0]
                    confidence = box.conf[0]
                    if confidence > 0.5:  # Threshold de confiança
                        detections.append([x1, y1, x2, y2, confidence])
        
        # Atualizar tracker
        tracker.update(frame, detections)
        
        # Processar tracks
        if tracker.tracks is not None:
            current_frame_persons = set()
            
            for track in tracker.tracks:
                bbox = track.bbox
                track_id = track.track_id
                
                # Adicionar à lista de pessoas atuais
                current_frame_persons.add(track_id)
                
                # Salvar dados para CSV
                timestamp = frame_count / fps
                center_x = int((bbox[0] + bbox[2]) / 2)
                center_y = int((bbox[1] + bbox[3]) / 2)
                
                tracking_data.append([
                    frame_count, timestamp, track_id,
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    center_x, center_y, "Nenhuma", confidence
                ])
                
                # Desenhar bounding box e ID
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), 
                             (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
                cv2.putText(frame, f"ID: {track_id}", 
                           (int(bbox[0]), int(bbox[1]) - 10),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
            
            # Detectar pessoas que saíram
            exited_this_frame = current_persons - current_frame_persons
            for person_id in exited_this_frame:
                exited_persons_count += 1
                print(f"Frame {frame_count}: Pessoa {person_id} saiu do quadro")
                
                # Mostrar características da pessoa que saiu
                tracker.print_person_features(person_id)
            
            current_persons = current_frame_persons
        
        # Mostrar estatísticas a cada 100 frames
        if frame_count % 100 == 0:
            print(f"\n--- Frame {frame_count} ---")
            print(f"Pessoas atuais: {len(current_persons)}")
            print(f"Pessoas que saíram: {exited_persons_count}")
            print(f"Re-identificações: {reid_count}")
            print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
        
        # Mostrar frame
        cv2.imshow('Tracking com Características Visuais', frame)
        
        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    cap.release()
    cv2.destroyAllWindows()
    
    # Salvar relatório CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"visual_features_report_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Frame', 'Timestamp', 'Track_ID', 'X1', 'Y1', 'X2', 'Y2', 
                        'Center_X', 'Center_Y', 'Zone', 'Confidence'])
        writer.writerows(tracking_data)
    
    # Salvar características visuais
    features_filename = tracker.save_person_features()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL")
    print("=" * 60)
    print(f"Total de frames processados: {frame_count}")
    print(f"Total de pessoas que saíram: {exited_persons_count}")
    print(f"Total de re-identificações: {reid_count}")
    print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
    print(f"Relatório salvo em: {csv_filename}")
    print(f"Características salvas em: {features_filename}")
    
    # Mostrar características de algumas pessoas
    print("\n🔍 CARACTERÍSTICAS DAS PESSOAS:")
    print("=" * 60)
    
    # Mostrar características das primeiras 5 pessoas que saíram
    for i, exited_person in enumerate(tracker.exited_persons[:5]):
        track_id = exited_person['track_id']
        print(f"\nPessoa {track_id}:")
        tracker.print_person_features(track_id)

if __name__ == "__main__":
    main() 