import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import time
from datetime import datetime
import argparse
import sys

def create_rtsp_capture(rtsp_url, username=None, password=None):
    """
    Cria uma captura de vídeo RTSP com configurações otimizadas
    """
    if username and password:
        # Formato: rtsp://username:password@ip:port/stream
        if '@' not in rtsp_url:
            # Extrair IP e porta do URL
            if rtsp_url.startswith('rtsp://'):
                url_parts = rtsp_url[7:].split('/')
                ip_port = url_parts[0]
                stream_path = '/'.join(url_parts[1:])
                rtsp_url = f"rtsp://{username}:{password}@{ip_port}/{stream_path}"
    
    print(f"🔗 Conectando ao stream RTSP: {rtsp_url}")
    
    # Configurar captura com buffer otimizado para RTSP
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print(f"❌ Erro ao conectar ao stream RTSP: {rtsp_url}")
        return None
    
    # Configurações otimizadas para RTSP
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # Buffer mínimo para reduzir latência
    cap.set(cv2.CAP_PROP_FPS, 30)        # Tentar 30 FPS
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1920)  # Resolução HD
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 1080)
    
    # Verificar se a conexão foi estabelecida
    ret, frame = cap.read()
    if not ret:
        print("❌ Não foi possível ler frames do stream RTSP")
        cap.release()
        return None
    
    print("✅ Conexão RTSP estabelecida com sucesso!")
    return cap

def create_ip_camera_capture(ip, port=554, username=None, password=None, stream_path="stream1"):
    """
    Cria URL RTSP para câmeras IP comuns
    """
    if username and password:
        return f"rtsp://{username}:{password}@{ip}:{port}/{stream_path}"
    else:
        return f"rtsp://{ip}:{port}/{stream_path}"

def main():
    parser = argparse.ArgumentParser(description='Tracking de pessoas via RTSP/Stream')
    parser.add_argument('--source', type=str, default='rtsp://192.168.1.100:554/stream1',
                       help='URL RTSP ou caminho do arquivo de vídeo')
    parser.add_argument('--username', type=str, help='Usuário da câmera IP')
    parser.add_argument('--password', type=str, help='Senha da câmera IP')
    parser.add_argument('--ip', type=str, help='IP da câmera')
    parser.add_argument('--port', type=int, default=554, help='Porta RTSP (padrão: 554)')
    parser.add_argument('--stream', type=str, default='stream1', help='Caminho do stream')
    parser.add_argument('--max-frames', type=int, default=0, help='Máximo de frames (0 = ilimitado)')
    parser.add_argument('--frame-skip', type=int, default=1, help='Processar 1 a cada N frames')
    parser.add_argument('--output', type=str, default='rtsp_output.avi', help='Arquivo de saída')
    parser.add_argument('--show-display', action='store_true', help='Mostrar display em tempo real')
    parser.add_argument('--confidence', type=float, default=0.5, help='Confiança mínima para detecção')
    
    args = parser.parse_args()
    
    print("🎥 SISTEMA DE TRACKING VIA RTSP/STREAM")
    print("=" * 50)
    
    # Carregar modelo YOLOv8
    print("🤖 Carregando modelo YOLOv8...")
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker
    tracker = Tracker()
    
    # Determinar fonte de vídeo
    if args.ip:
        # Usar IP da câmera
        rtsp_url = create_ip_camera_capture(
            args.ip, args.port, args.username, args.password, args.stream
        )
    else:
        # Usar URL RTSP direta
        rtsp_url = args.source
    
    # Criar captura
    if rtsp_url.startswith('rtsp://'):
        cap = create_rtsp_capture(rtsp_url, args.username, args.password)
    else:
        # Arquivo de vídeo local
        cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print(f"❌ Erro ao abrir fonte: {rtsp_url}")
        return
    
    # Configurar vídeo de saída
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if fps <= 0:
        fps = 30  # FPS padrão se não detectado
    
    print(f"📹 Resolução: {width}x{height}")
    print(f"⚡ FPS: {fps}")
    
    # Configurar codec de saída
    fourcc = cv2.VideoWriter_fourcc(*'XVID')
    out = cv2.VideoWriter(args.output, fourcc, fps, (width, height))
    
    # Configurações
    max_frames = args.max_frames
    frame_skip = args.frame_skip
    show_display = args.show_display
    
    print(f"⚡ Processando: {'Ilimitado' if max_frames == 0 else max_frames} frames")
    print(f"🔄 Frame skip: {frame_skip}")
    print(f"👁️  Display: {'Sim' if show_display else 'Não'}")
    print("-" * 50)
    
    frame_count = 0
    processed_frames = 0
    start_time = time.time()
    
    # Lista para armazenar dados
    tracking_data = []
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("⚠️  Erro ao ler frame - tentando reconectar...")
                time.sleep(1)
                continue
                
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
                        if box.cls == 0 and box.conf > args.confidence:
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
            
            # Desenhar bounding boxes e IDs
            if tracker.tracks is not None:
                for track in tracker.tracks:
                    bbox = track.bbox
                    track_id = track.track_id
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # Caixa verde
                    cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
                    
                    # ID da pessoa
                    cv2.putText(frame, f'ID: {track_id}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                    
                    # Centro da pessoa
                    center_x = int((x1 + x2) / 2)
                    center_y = int((y1 + y2) / 2)
                    cv2.circle(frame, (center_x, center_y), 3, (255, 0, 0), -1)
            
            # Adicionar informações no frame
            current_tracks = len(tracker.tracks) if tracker.tracks else 0
            elapsed = time.time() - start_time
            current_fps = processed_frames / elapsed if elapsed > 0 else 0
            
            # Informações no canto superior esquerdo
            info_text = [
                f"Frame: {frame_count}",
                f"Pessoas: {current_tracks}",
                f"FPS: {current_fps:.1f}",
                f"Tempo: {elapsed:.1f}s"
            ]
            
            for i, text in enumerate(info_text):
                cv2.putText(frame, text, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
            
            # Mostrar display se solicitado
            if show_display:
                cv2.imshow('RTSP Tracking', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Salvar frame no vídeo de saída
            out.write(frame)
            
            # Mostrar progresso a cada 30 frames
            if processed_frames % 30 == 0:
                print(f"⏳ Frame {frame_count}: {current_tracks} pessoas | "
                      f"FPS: {current_fps:.1f} | Tempo: {elapsed:.1f}s")
            
            # Verificar limite de frames
            if max_frames > 0 and processed_frames >= max_frames:
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
    finally:
        cap.release()
        out.release()
        if show_display:
            cv2.destroyAllWindows()
    
    # Estatísticas finais
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
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
        csv_filename = f"rtsp_tracking_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"💾 Relatório salvo: {csv_filename}")
    
    print(f"🎬 Vídeo salvo: {args.output}")
    print("\n🎯 TRACKING VIA RTSP FINALIZADO!")

if __name__ == "__main__":
    main() 