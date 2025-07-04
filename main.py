import os
import random
import csv
from datetime import datetime

import cv2
from ultralytics import YOLO

from tracker import Tracker
from reid_system import ReIdentificationSystem

# Defina zonas de interesse como retângulos: (x1, y1, x2, y2)
ZONES = {
    'Expositor 1': (100, 100, 300, 300),
    'Expositor 2': (400, 100, 600, 300),
    'Caixa': (700, 400, 900, 600)
}

video_path = os.path.join('.', 'people.mp4')
video_out_path = os.path.join('.', 'out_compat.avi')

cap = cv2.VideoCapture(video_path)
ret, frame = cap.read()

if not ret:
    print(f"Erro ao abrir o vídeo {video_path}!")
    exit(1)

# Usar codec XVID para máxima compatibilidade
cap_out = cv2.VideoWriter(video_out_path, cv2.VideoWriter_fourcc(*'XVID'), cap.get(cv2.CAP_PROP_FPS),
                          (frame.shape[1], frame.shape[0]))

model = YOLO("yolov8n.pt")

tracker = Tracker()
reid_system = ReIdentificationSystem(max_exit_time=30, similarity_threshold=0.6)

colors = [(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for j in range(100)]

# Dicionário para armazenar trajetos de cada ID
trajectories = {}

# Dicionário para armazenar tempo em cada zona por ID
zone_times = {}

# Lista para armazenar dados detalhados para CSV
tracking_data = []

frame_count = 0
fps = cap.get(cv2.CAP_PROP_FPS)

while ret:
    results = model(frame)
    result = results[0]
    detections = []
    
    for r in result.boxes.data.tolist():
        x1, y1, x2, y2, score, class_id = r
        
        if int(class_id) == 0:  # Apenas pessoas
            detections.append([x1, y1, x2, y2, score])
    
    tracker.update(frame, detections)
    
    # Desenhar zonas de interesse
    for zone_name, (x1, y1, x2, y2) in ZONES.items():
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, zone_name, (x1, y1-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
    
    # Processar tracks e desenhar trajetos
    if tracker.tracks is not None:
        for track in tracker.tracks:
            bbox = track.bbox
            x1, y1, x2, y2 = bbox
            track_id = track.track_id
            
            # Calcular centro da pessoa
            center_x = int((x1 + x2) / 2)
            center_y = int((y1 + y2) / 2)
            
            # Adicionar posição ao trajeto
            if track_id not in trajectories:
                trajectories[track_id] = []
            trajectories[track_id].append((center_x, center_y))
            
            # Manter apenas os últimos 30 pontos para não sobrecarregar o vídeo
            if len(trajectories[track_id]) > 30:
                trajectories[track_id] = trajectories[track_id][-30:]
            
            # Desenhar trajeto
            if len(trajectories[track_id]) > 1:
                for i in range(1, len(trajectories[track_id])):
                    cv2.line(frame, trajectories[track_id][i-1], trajectories[track_id][i], 
                            colors[track_id % len(colors)], 2)
            
            # Desenhar caixa e ID
            cv2.rectangle(frame, (int(x1), int(y1)), (int(x2), int(y2)), (colors[track_id % len(colors)]), 3)
            cv2.putText(frame, f"ID: {track_id}", (int(x1), int(y1)-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (colors[track_id % len(colors)]), 2)
            
            # Registrar dados para CSV
            timestamp = frame_count / fps
            current_zone = "Nenhuma"
            
            # Verificar se está em alguma zona
            for zone_name, (zx1, zy1, zx2, zy2) in ZONES.items():
                if zx1 <= center_x <= zx2 and zy1 <= center_y <= zy2:
                    current_zone = zone_name
                    if track_id not in zone_times:
                        zone_times[track_id] = {}
                    if zone_name not in zone_times[track_id]:
                        zone_times[track_id][zone_name] = 0
                    zone_times[track_id][zone_name] += 1
            
            # Adicionar dados ao CSV
            tracking_data.append({
                'frame': frame_count,
                'timestamp': round(timestamp, 2),
                'track_id': track_id,
                'x1': int(x1),
                'y1': int(y1),
                'x2': int(x2),
                'y2': int(y2),
                'center_x': center_x,
                'center_y': center_y,
                'zone': current_zone,
                'bbox_width': int(x2 - x1),
                'bbox_height': int(y2 - y1)
            })
    
    cap_out.write(frame)
    ret, frame = cap.read()
    frame_count += 1

cap.release()
cap_out.release()

# Salvar relatório CSV
csv_filename = f"tracking_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['frame', 'timestamp', 'track_id', 'x1', 'y1', 'x2', 'y2', 'center_x', 'center_y', 'zone', 'bbox_width', 'bbox_height']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    for row in tracking_data:
        writer.writerow(row)

# Salvar relatório resumido por ID
summary_filename = f"tracking_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
with open(summary_filename, 'w', newline='', encoding='utf-8') as csvfile:
    fieldnames = ['track_id', 'total_frames', 'first_frame', 'last_frame', 'duration_seconds', 'zones_visited', 'zone_details']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    
    writer.writeheader()
    
    # Agrupar dados por track_id
    track_summary = {}
    for row in tracking_data:
        track_id = row['track_id']
        if track_id not in track_summary:
            track_summary[track_id] = {
                'frames': [],
                'zones': set()
            }
        track_summary[track_id]['frames'].append(row['frame'])
        if row['zone'] != 'Nenhuma':
            track_summary[track_id]['zones'].add(row['zone'])
    
    # Escrever resumo
    for track_id, data in track_summary.items():
        frames = data['frames']
        zones = data['zones']
        
        # Detalhes das zonas
        zone_details = []
        for zone_name in zones:
            zone_frames = sum(1 for row in tracking_data if row['track_id'] == track_id and row['zone'] == zone_name)
            zone_details.append(f"{zone_name}: {zone_frames} frames")
        
        writer.writerow({
            'track_id': track_id,
            'total_frames': len(frames),
            'first_frame': min(frames),
            'last_frame': max(frames),
            'duration_seconds': round(len(frames) / fps, 2),
            'zones_visited': len(zones),
            'zone_details': '; '.join(zone_details)
        })

print(f"Relatório detalhado salvo em: {csv_filename}")
print(f"Relatório resumido salvo em: {summary_filename}")

print("\nRelatório de zonas por ID:")
for track_id, zones in zone_times.items():
    print(f"ID {track_id}:")
    for zone_name, frames in zones.items():
        print(f"  - {zone_name}: {frames} frames")
