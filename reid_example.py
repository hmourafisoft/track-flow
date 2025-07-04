import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
from reid_system import ReIdentificationSystem
import csv
from datetime import datetime
import os

def main():
    # Carregar modelo YOLO
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker e sistema de re-identificação
    tracker = Tracker()
    reid_system = ReIdentificationSystem(max_exit_time=30, similarity_threshold=0.6)
    
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
    output_path = 'output_with_reid.mp4'
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Definir zonas de interesse
    zones = {
        'Expositor 1': [(100, 100), (300, 400)],
        'Expositor 2': [(350, 100), (550, 400)]
    }
    
    # Dicionários para armazenar dados
    tracking_data = []
    person_positions = {}  # {track_id: [(frame, x, y), ...]}
    zone_visits = {}  # {track_id: {zone: frames}}
    current_tracks = set()
    exited_tracks = set()
    
    frame_count = 0
    
    print("Iniciando processamento com sistema de re-identificação...")
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
                
                # Verificar se está em alguma zona
                current_zone = None
                for zone_name, (top_left, bottom_right) in zones.items():
                    if (top_left[0] <= center_x <= bottom_right[0] and 
                        top_left[1] <= center_y <= bottom_right[1]):
                        current_zone = zone_name
                        break
                
                # Atualizar visitas às zonas
                if track_id not in zone_visits:
                    zone_visits[track_id] = {}
                if current_zone:
                    if current_zone not in zone_visits[track_id]:
                        zone_visits[track_id][current_zone] = 0
                    zone_visits[track_id][current_zone] += 1
                
                # Extrair características para re-identificação
                appearance_features = reid_system.extract_appearance_features(frame, bbox)
                
                # Tentar re-identificação se for uma nova detecção
                if track_id not in current_tracks:
                    reid_id = reid_system.try_reidentify(appearance_features, bbox)
                    if reid_id:
                        print(f"Re-identificação: ID {reid_id} retornou como ID {track_id}")
                
                # Armazenar dados para CSV
                timestamp = frame_count / fps
                tracking_data.append([
                    frame_count,
                    timestamp,
                    track_id,
                    bbox[0], bbox[1], bbox[2], bbox[3],
                    center_x, center_y,
                    current_zone or "Nenhuma",
                    confidence if 'confidence' in locals() else 0.0
                ])
                
                # Desenhar bounding box e ID
                cv2.rectangle(frame, (int(bbox[0]), int(bbox[1])), (int(bbox[2]), int(bbox[3])), (0, 255, 0), 2)
                cv2.putText(frame, f'ID: {track_id}', (int(bbox[0]), int(bbox[1]) - 10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
                
                # Desenhar trajetória
                if track_id in person_positions and len(person_positions[track_id]) > 1:
                    positions = person_positions[track_id][-30:]  # Últimas 30 posições
                    for i in range(1, len(positions)):
                        cv2.line(frame, positions[i-1][1:], positions[i][1:], (255, 0, 0), 2)
        
        # Identificar pessoas que saíram
        for track_id in current_tracks - current_frame_tracks:
            if track_id not in exited_tracks:
                exited_tracks.add(track_id)
                # Adicionar à lista de pessoas que saíram para re-identificação
                if track_id in person_positions and person_positions[track_id]:
                    last_pos = person_positions[track_id][-1]
                    last_bbox = [last_pos[1] - 25, last_pos[2] - 50, last_pos[1] + 25, last_pos[2] + 50]
                    reid_system.add_exited_person(track_id, None, last_bbox)
        
        current_tracks = current_frame_tracks
        
        # Desenhar zonas
        for zone_name, (top_left, bottom_right) in zones.items():
            cv2.rectangle(frame, top_left, bottom_right, (0, 0, 255), 2)
            cv2.putText(frame, zone_name, (top_left[0], top_left[1] - 10), 
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)
        
        # Mostrar estatísticas de re-identificação
        reid_stats = reid_system.get_reid_statistics()
        cv2.putText(frame, f'Re-ID Matches: {reid_stats["total_reid_matches"]}', 
                   (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(frame, f'Exited Persons: {len(reid_system.exited_persons)}', 
                   (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        
        # Mostrar frame
        cv2.imshow('Tracking with Re-ID', frame)
        
        # Salvar frame no vídeo de saída
        out.write(frame)
        
        # Pressionar 'q' para sair
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Liberar recursos
    cap.release()
    out.release()
    cv2.destroyAllWindows()
    
    # Salvar dados de re-identificação
    reid_system.save_reid_data()
    
    # Gerar relatórios CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Relatório detalhado
    detailed_filename = f'tracking_report_with_reid_{timestamp}.csv'
    with open(detailed_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['frame', 'timestamp', 'track_id', 'x1', 'y1', 'x2', 'y2', 'center_x', 'center_y', 'zone', 'confidence'])
        writer.writerows(tracking_data)
    
    # Relatório resumido
    summary_filename = f'tracking_summary_with_reid_{timestamp}.csv'
    with open(summary_filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['track_id', 'total_frames', 'first_frame', 'last_frame', 'duration_seconds', 'zones_visited', 'zone_details'])
        
        for track_id in set([row[2] for row in tracking_data]):
            track_frames = [row for row in tracking_data if row[2] == track_id]
            total_frames = len(track_frames)
            first_frame = track_frames[0][0]
            last_frame = track_frames[-1][0]
            duration_seconds = (last_frame - first_frame) / fps
            
            zones_visited = 0
            zone_details = ""
            if track_id in zone_visits:
                zones_visited = len(zone_visits[track_id])
                zone_details = "; ".join([f"{zone}: {frames} frames" for zone, frames in zone_visits[track_id].items()])
            
            writer.writerow([track_id, total_frames, first_frame, last_frame, duration_seconds, zones_visited, zone_details])
    
    print(f"Relatório detalhado salvo em: {detailed_filename}")
    print(f"Relatório resumido salvo em: {summary_filename}")
    
    # Mostrar estatísticas de re-identificação
    print("\nEstatísticas de Re-identificação:")
    reid_stats = reid_system.get_reid_statistics()
    for key, value in reid_stats.items():
        print(f"{key}: {value}")
    
    # Mostrar relatório de zonas
    print("\nRelatório de zonas por ID:")
    for track_id, zones_data in zone_visits.items():
        print(f"ID {track_id}:")
        for zone, frames in zones_data.items():
            print(f"  - {zone}: {frames} frames")

if __name__ == "__main__":
    main() 