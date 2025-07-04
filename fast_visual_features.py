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
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print("🚀 SISTEMA RÁPIDO DE CARACTERÍSTICAS VISUAIS")
    print("=" * 60)
    print(f"Total de frames: {total_frames}")
    print(f"FPS: {fps}")
    print("Processando apenas frames chave para otimizar velocidade...")
    
    # Dicionários para armazenar dados
    tracking_data = []
    current_persons = set()
    exited_persons_count = 0
    
    frame_count = 0
    processed_frames = 0
    
    # Processar apenas a cada N frames para otimizar velocidade
    process_every_n_frames = 5  # Processar a cada 5 frames
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_count += 1
        
        # Processar apenas a cada N frames
        if frame_count % process_every_n_frames != 0:
            continue
        
        processed_frames += 1
        
        # Mostrar progresso
        if processed_frames % 50 == 0:
            progress = (frame_count / total_frames) * 100
            print(f"Progresso: {progress:.1f}% ({frame_count}/{total_frames} frames)")
        
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
                    center_x, center_y, "Nenhuma", 0.8  # Confidence padrão
                ])
            
            # Detectar pessoas que saíram
            exited_this_frame = current_persons - current_frame_persons
            for person_id in exited_this_frame:
                exited_persons_count += 1
                print(f"Frame {frame_count}: Pessoa {person_id} saiu do quadro")
            
            current_persons = current_frame_persons
        
        # Mostrar estatísticas a cada 200 frames processados
        if processed_frames % 200 == 0:
            print(f"\n--- Frame {frame_count} (Processado: {processed_frames}) ---")
            print(f"Pessoas atuais: {len(current_persons)}")
            print(f"Pessoas que saíram: {exited_persons_count}")
            print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
    
    cap.release()
    
    # Salvar relatório CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"fast_visual_features_report_{timestamp}.csv"
    
    with open(csv_filename, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Frame', 'Timestamp', 'Track_ID', 'X1', 'Y1', 'X2', 'Y2', 
                        'Center_X', 'Center_Y', 'Zone', 'Confidence'])
        writer.writerows(tracking_data)
    
    # Salvar características visuais
    features_filename = tracker.save_person_features()
    
    print("\n" + "=" * 60)
    print("📊 RESUMO FINAL - SISTEMA RÁPIDO")
    print("=" * 60)
    print(f"Total de frames no vídeo: {total_frames}")
    print(f"Frames processados: {processed_frames}")
    print(f"Taxa de processamento: {processed_frames/total_frames*100:.1f}%")
    print(f"Total de pessoas que saíram: {exited_persons_count}")
    print(f"Pessoas na lista de saídas: {len(tracker.exited_persons)}")
    print(f"Relatório salvo em: {csv_filename}")
    print(f"Características salvas em: {features_filename}")
    
    # Mostrar algumas características
    print("\n🔍 CARACTERÍSTICAS DAS PESSOAS:")
    print("=" * 60)
    
    # Mostrar características das primeiras 3 pessoas que saíram
    for i, exited_person in enumerate(tracker.exited_persons[:3]):
        track_id = exited_person['track_id']
        print(f"\nPessoa {track_id}:")
        tracker.print_person_features(track_id)

if __name__ == "__main__":
    main() 