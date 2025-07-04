import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import time
from datetime import datetime

def main():
    print("🚀 SISTEMA ULTRA-RÁPIDO DE TRACKING COM CARACTERÍSTICAS VISUAIS")
    print("=" * 60)
    
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
    
    # Configurações para processamento rápido
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    # Processar apenas os primeiros 10 segundos (ou 300 frames)
    max_frames = min(300, total_frames)
    frame_skip = 3  # Processar apenas 1 a cada 3 frames
    
    print(f"📹 Vídeo: {video_path}")
    print(f"📊 FPS: {fps:.1f}")
    print(f"🎬 Total de frames: {total_frames}")
    print(f"⚡ Processando: {max_frames} frames (1 a cada {frame_skip})")
    print(f"⏱️  Tempo estimado: ~{max_frames//fps:.1f} segundos")
    print("-" * 60)
    
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
                timestamp = frame_count / fps
                
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
        
        # Mostrar progresso a cada 50 frames processados
        if processed_frames % 50 == 0:
            elapsed = time.time() - start_time
            fps_processed = processed_frames / elapsed
            eta = (max_frames - processed_frames) / fps_processed if fps_processed > 0 else 0
            
            print(f"⏳ Progresso: {processed_frames}/{max_frames} frames "
                  f"({processed_frames/max_frames*100:.1f}%) | "
                  f"FPS: {fps_processed:.1f} | "
                  f"ETA: {eta:.1f}s")
        
        # Mostrar estatísticas a cada 100 frames
        if processed_frames % 100 == 0:
            current_tracks = len(tracker.tracks) if tracker.tracks else 0
            exited_persons = len(tracker.exited_persons)
            print(f"📊 Frame {frame_count}: {current_tracks} pessoas ativas, "
                  f"{exited_persons} pessoas saíram")
    
    cap.release()
    
    # Estatísticas finais
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
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
        csv_filename = f"ultra_fast_report_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"💾 Relatório salvo: {csv_filename}")
    
    # Salvar características visuais
    try:
        features_filename = tracker.save_person_features()
        if features_filename:
            print(f"🎨 Características visuais salvas: {features_filename}")
    except Exception as e:
        print(f"⚠️  Erro ao salvar características: {e}")
    
    print("\n🎯 SISTEMA ULTRA-RÁPIDO FINALIZADO!")
    print("📁 Verifique os arquivos de saída gerados.")

if __name__ == "__main__":
    main() 