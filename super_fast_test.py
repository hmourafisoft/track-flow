import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import time
from datetime import datetime

def main():
    print("⚡ TESTE SUPER-RÁPIDO - APENAS 50 FRAMES")
    print("=" * 50)
    
    # Carregar modelo YOLOv8
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker
    tracker = Tracker()
    
    # Abrir vídeo
    video_path = 'people.mp4'
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"❌ Erro ao abrir vídeo: {video_path}")
        return
    
    # Configurar vídeo de saída compatível
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    out = cv2.VideoWriter('out_compat.avi', cv2.VideoWriter_fourcc(*'XVID'), fps, (width, height))
    
    # Configurações para teste super-rápido
    max_frames = 50  # Apenas 50 frames
    frame_skip = 5   # Processar apenas 1 a cada 5 frames
    
    print(f"📹 Vídeo: {video_path}")
    print(f"⚡ Processando: {max_frames} frames (1 a cada {frame_skip})")
    print(f"⏱️  Tempo estimado: ~30 segundos")
    print("-" * 50)
    
    frame_count = 0
    processed_frames = 0
    start_time = time.time()
    
    # Lista para armazenar dados
    tracking_data = []
    
    while cap.isOpened() and processed_frames < max_frames:
        ret, frame = cap.read()
        if not ret:
            break
            
        frame_count += 1
        
        # Processar apenas 1 a cada frame_skip frames
        if frame_count % frame_skip != 0:
            continue
            
        processed_frames += 1
        
        # Detectar pessoas
        results = model(frame, verbose=False)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    # Filtrar apenas pessoas (classe 0)
                    if box.cls == 0 and box.conf > 0.5:
                        x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                        conf = box.conf[0].cpu().numpy()
                        detections.append([x1, y1, x2, y2, conf])
        
        # Atualizar tracker
        tracker.update(frame, detections)
        
        # Coletar dados de tracking
        if tracker.tracks is not None:
            for track in tracker.tracks:
                bbox = track.bbox
                timestamp = frame_count / 30.0  # Assumindo 30 FPS
                
                data = {
                    'Frame': frame_count,
                    'Timestamp': timestamp,
                    'Track_ID': track.track_id,
                    'X1': bbox[0],
                    'Y1': bbox[1],
                    'X2': bbox[2],
                    'Y2': bbox[3],
                    'Center_X': int((bbox[0] + bbox[2]) / 2),
                    'Center_Y': int((bbox[1] + bbox[3]) / 2),
                    'Zone': 'Nenhuma',
                    'Confidence': 0.8
                }
                tracking_data.append(data)
        
        # Mostrar progresso a cada 10 frames
        if processed_frames % 10 == 0:
            elapsed = time.time() - start_time
            fps_processed = processed_frames / elapsed
            eta = (max_frames - processed_frames) / fps_processed if fps_processed > 0 else 0
            
            print(f"⏳ {processed_frames}/{max_frames} frames "
                  f"({processed_frames/max_frames*100:.0f}%) | "
                  f"ETA: {eta:.0f}s")
        
        # Mostrar estatísticas a cada 20 frames
        if processed_frames % 20 == 0:
            current_tracks = len(tracker.tracks) if tracker.tracks else 0
            exited_persons = len(tracker.exited_persons)
            print(f"📊 Frame {frame_count}: {current_tracks} pessoas ativas, "
                  f"{exited_persons} pessoas saíram")
        
        # Desenhar bounding boxes e IDs nos frames antes de salvar
        if tracker.tracks is not None:
            for track in tracker.tracks:
                bbox = track.bbox
                track_id = track.track_id
                x1, y1, x2, y2 = map(int, bbox)
                # Caixa
                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                # ID
                cv2.putText(frame, f'ID: {track_id}', (x1, y1 - 10),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)
        
        # Salvar frame no vídeo de saída compatível
        out.write(frame)
    
    cap.release()
    out.release()
    
    # Estatísticas finais
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("✅ TESTE CONCLUÍDO!")
    print(f"⏱️  Tempo total: {total_time:.1f} segundos")
    print(f"⚡ FPS médio: {processed_frames/total_time:.1f}")
    print(f"📊 Frames processados: {processed_frames}")
    print(f"👥 Pessoas únicas detectadas: {len(set([d['Track_ID'] for d in tracking_data]))}")
    print(f"🚪 Pessoas que saíram: {len(tracker.exited_persons)}")
    
    # Salvar relatório CSV
    if tracking_data:
        import pandas as pd
        df = pd.DataFrame(tracking_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"super_fast_test_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"💾 Relatório salvo: {csv_filename}")
    
    print("\n🎯 TESTE SUPER-RÁPIDO FINALIZADO!")
    print("📁 Verifique o arquivo CSV gerado.")

if __name__ == "__main__":
    main() 