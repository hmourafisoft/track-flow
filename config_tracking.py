#!/usr/bin/env python3
"""
Sistema de tracking usando configurações de câmeras via JSON
"""

import cv2
import numpy as np
from ultralytics import YOLO
from tracker import Tracker
import time
from datetime import datetime
import argparse
import sys
from camera_manager import CameraManager

def main():
    parser = argparse.ArgumentParser(description='Tracking de pessoas usando configurações de câmeras')
    parser.add_argument('--camera', type=str, default='camera_1', help='ID da câmera no config')
    parser.add_argument('--config', type=str, default='camera_config.json', help='Arquivo de configuração')
    parser.add_argument('--max-frames', type=int, default=0, help='Máximo de frames (0 = ilimitado)')
    parser.add_argument('--frame-skip', type=int, help='Processar 1 a cada N frames (sobrescreve config)')
    parser.add_argument('--confidence', type=float, help='Confiança mínima (sobrescreve config)')
    parser.add_argument('--show-display', action='store_true', help='Mostrar display (sobrescreve config)')
    parser.add_argument('--output', type=str, help='Arquivo de saída (sobrescreve config)')
    parser.add_argument('--test-only', action='store_true', help='Apenas testar conexão')
    parser.add_argument('--list-cameras', action='store_true', help='Listar câmeras configuradas')
    
    args = parser.parse_args()
    
    print("🎥 SISTEMA DE TRACKING COM CONFIGURAÇÃO")
    print("=" * 50)
    
    # Inicializar gerenciador de câmeras
    manager = CameraManager(args.config)
    
    # Listar câmeras se solicitado
    if args.list_cameras:
        print("\n📋 Câmeras configuradas:")
        cameras = manager.list_cameras()
        for camera_id, camera_info in cameras:
            status = "✅ Habilitada" if camera_info.get("enabled", True) else "❌ Desabilitada"
            print(f"   {camera_id}: {camera_info['name']} ({camera_info['type']}) - {status}")
            if camera_info.get("description"):
                print(f"      Descrição: {camera_info['description']}")
        return
    
    # Obter informações da câmera
    camera_info = manager.get_camera_info(args.camera)
    if not camera_info:
        print(f"❌ Câmera não encontrada: {args.camera}")
        print("Use --list-cameras para ver câmeras disponíveis")
        return
    
    if not camera_info.get("enabled", True):
        print(f"❌ Câmera desabilitada: {args.camera}")
        return
    
    print(f"📹 Câmera: {camera_info['name']} ({args.camera})")
    print(f"🔗 Tipo: {camera_info['type']}")
    
    # Obter URL da câmera
    camera_url = manager.get_camera_url(args.camera)
    if not camera_url:
        print("❌ Erro ao gerar URL da câmera")
        return
    
    print(f"🌐 URL: {camera_url}")
    
    # Testar conexão se solicitado
    if args.test_only:
        print("\n🧪 Testando conexão...")
        success = manager.test_camera_connection(args.camera)
        if success:
            print("✅ Teste concluído com sucesso!")
        else:
            print("❌ Falha no teste de conexão")
        return
    
    # Carregar configurações padrão
    default_settings = manager.get_default_settings()
    
    # Aplicar argumentos da linha de comando (sobrescrevem config)
    frame_skip = args.frame_skip if args.frame_skip is not None else default_settings.get("frame_skip", 1)
    confidence = args.confidence if args.confidence is not None else default_settings.get("confidence", 0.5)
    show_display = args.show_display if args.show_display else default_settings.get("show_display", False)
    max_frames = args.max_frames if args.max_frames > 0 else default_settings.get("max_frames", 0)
    save_video = default_settings.get("save_video", True)
    save_csv = default_settings.get("save_csv", True)
    
    # Gerar nome do arquivo de saída
    if args.output:
        output_file = args.output
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"tracking_{args.camera}_{timestamp}.avi"
    
    print(f"⚙️  Configurações:")
    print(f"   Frame skip: {frame_skip}")
    print(f"   Confiança: {confidence}")
    print(f"   Display: {'Sim' if show_display else 'Não'}")
    print(f"   Máximo frames: {'Ilimitado' if max_frames == 0 else max_frames}")
    print(f"   Salvar vídeo: {'Sim' if save_video else 'Não'}")
    print(f"   Salvar CSV: {'Sim' if save_csv else 'Não'}")
    print(f"   Arquivo saída: {output_file}")
    
    # Carregar modelo YOLOv8
    print("\n🤖 Carregando modelo YOLOv8...")
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker
    tracker = Tracker()
    
    # Criar captura de vídeo
    print(f"\n🔗 Conectando à câmera...")
    cap = cv2.VideoCapture(camera_url)
    
    if not cap.isOpened():
        print(f"❌ Erro ao conectar à câmera: {camera_url}")
        return
    
    # Configurar captura
    network_settings = manager.get_network_settings()
    cap.set(cv2.CAP_PROP_BUFFERSIZE, network_settings.get("buffer_size", 1))
    
    # Obter informações do stream
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    if fps <= 0:
        fps = 30  # FPS padrão
    
    print(f"✅ Conectado!")
    print(f"📹 Resolução: {width}x{height}")
    print(f"⚡ FPS: {fps}")
    
    # Configurar vídeo de saída
    out = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    print("\n🎯 Iniciando tracking...")
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
                        if box.cls == 0 and box.conf > confidence:
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
                        'Camera_ID': args.camera,
                        'Camera_Name': camera_info['name'],
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
                f"Camera: {camera_info['name']}",
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
                cv2.imshow(f'Tracking - {camera_info["name"]}', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Salvar frame no vídeo de saída
            if save_video and out:
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
        if out:
            out.release()
        if show_display:
            cv2.destroyAllWindows()
    
    # Estatísticas finais
    total_time = time.time() - start_time
    print("\n" + "=" * 50)
    print("✅ PROCESSAMENTO CONCLUÍDO!")
    print(f"📹 Câmera: {camera_info['name']}")
    print(f"⏱️  Tempo total: {total_time:.1f} segundos")
    print(f"⚡ FPS médio: {processed_frames/total_time:.1f}")
    print(f"📊 Frames processados: {processed_frames}")
    print(f"👥 Pessoas únicas detectadas: {len(set([d['Track_ID'] for d in tracking_data]))}")
    print(f"🚪 Pessoas que saíram: {len(tracker.exited_persons)}")
    
    # Salvar relatório CSV
    if save_csv and tracking_data:
        import pandas as pd
        df = pd.DataFrame(tracking_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"tracking_{args.camera}_{timestamp}.csv"
        df.to_csv(csv_filename, index=False)
        print(f"💾 Relatório salvo: {csv_filename}")
    
    if save_video:
        print(f"🎬 Vídeo salvo: {output_file}")
    
    print("\n🎯 TRACKING FINALIZADO!")

if __name__ == "__main__":
    main() 