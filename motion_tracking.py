#!/usr/bin/env python3
"""
Sistema de tracking otimizado com detecção de movimento
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
import os
import pandas as pd

class MotionDetector:
    def __init__(self, threshold=25, min_area=500):
        """
        Detector de movimento usando diferença de frames
        
        Args:
            threshold: Threshold para detecção de movimento (0-255)
            min_area: Área mínima para considerar movimento
        """
        self.threshold = threshold
        self.min_area = min_area
        self.prev_frame = None
        self.motion_detected = False
        self.motion_frames = 0
        self.no_motion_frames = 0
        
    def detect_motion(self, frame):
        """
        Detecta movimento no frame
        
        Returns:
            bool: True se movimento detectado
        """
        # Converter para escala de cinza
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)
        
        # Se é o primeiro frame
        if self.prev_frame is None:
            self.prev_frame = gray
            return False
        
        # Calcular diferença entre frames
        frame_delta = cv2.absdiff(self.prev_frame, gray)
        thresh = cv2.threshold(frame_delta, self.threshold, 255, cv2.THRESH_BINARY)[1]
        
        # Dilatar para preencher buracos
        thresh = cv2.dilate(thresh, None, iterations=2)
        
        # Encontrar contornos
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Verificar se há movimento significativo
        motion_detected = False
        for contour in contours:
            if cv2.contourArea(contour) > self.min_area:
                motion_detected = True
                break
        
        # Atualizar estado
        if motion_detected:
            self.motion_frames += 1
            self.no_motion_frames = 0
        else:
            self.no_motion_frames += 1
            self.motion_frames = 0
        
        # Atualizar frame anterior
        self.prev_frame = gray
        
        return motion_detected

class AdaptiveMotionTracker:
    def __init__(self, motion_threshold=25, min_area=500, motion_buffer=3, idle_buffer=10):
        """
        Tracker adaptativo que só processa quando há movimento
        
        Args:
            motion_threshold: Threshold para detecção de movimento
            min_area: Área mínima para considerar movimento
            motion_buffer: Frames para confirmar movimento
            idle_buffer: Frames para considerar sem movimento
        """
        self.motion_detector = MotionDetector(motion_threshold, min_area)
        self.motion_buffer = motion_buffer
        self.idle_buffer = idle_buffer
        self.processing_mode = False  # True = processando, False = aguardando movimento
        
    def should_process_frame(self, frame):
        """
        Decide se deve processar o frame baseado no movimento
        
        Returns:
            bool: True se deve processar
        """
        motion_detected = self.motion_detector.detect_motion(frame)
        
        # Lógica adaptativa
        if motion_detected and self.motion_detector.motion_frames >= self.motion_buffer:
            self.processing_mode = True
            return True
        elif not motion_detected and self.motion_detector.no_motion_frames >= self.idle_buffer:
            self.processing_mode = False
            return False
        else:
            return self.processing_mode

def main():
    parser = argparse.ArgumentParser(description='Tracking otimizado com detecção de movimento')
    parser.add_argument('--camera', type=str, default='camera_1', help='ID da câmera no config')
    parser.add_argument('--config', type=str, default='camera_config.json', help='Arquivo de configuração')
    parser.add_argument('--motion-threshold', type=int, default=25, help='Threshold de movimento (0-255)')
    parser.add_argument('--min-area', type=int, default=500, help='Área mínima para movimento')
    parser.add_argument('--motion-buffer', type=int, default=3, help='Frames para confirmar movimento')
    parser.add_argument('--idle-buffer', type=int, default=10, help='Frames para considerar sem movimento')
    parser.add_argument('--max-frames', type=int, default=0, help='Máximo de frames (0 = ilimitado)')
    parser.add_argument('--frame-skip', type=int, help='Processar 1 a cada N frames (sobrescreve config)')
    parser.add_argument('--confidence', type=float, help='Confiança mínima (sobrescreve config)')
    parser.add_argument('--show-display', action='store_true', help='Mostrar display (sobrescreve config)')
    parser.add_argument('--output', type=str, help='Arquivo de saída (sobrescreve config)')
    parser.add_argument('--show-motion', action='store_true', help='Mostrar detecção de movimento')
    parser.add_argument('--test-only', action='store_true', help='Apenas testar conexão')
    parser.add_argument('--list-cameras', action='store_true', help='Listar câmeras configuradas')
    
    args = parser.parse_args()
    
    print("🎥 SISTEMA DE TRACKING OTIMIZADO COM DETECÇÃO DE MOVIMENTO")
    print("=" * 60)
    
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
    
    # Gerar nome do diretório de saída
    camera_ip = camera_info.get('ip', args.camera)  # Usa IP se existir, senão camera_id
    today_str = datetime.now().strftime("%Y-%m-%d")
    output_dir = os.path.join("data_output", str(camera_ip), today_str)
    os.makedirs(output_dir, exist_ok=True)

    # Gerar nome do arquivo de saída
    if args.output:
        output_file = os.path.join(output_dir, args.output)
    else:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = os.path.join(output_dir, f"motion_tracking_{args.camera}_{timestamp}.avi")
    
    print(f"⚙️  Configurações:")
    print(f"   Frame skip: {frame_skip}")
    print(f"   Confiança: {confidence}")
    print(f"   Display: {'Sim' if show_display else 'Não'}")
    print(f"   Máximo frames: {'Ilimitado' if max_frames == 0 else max_frames}")
    print(f"   Salvar vídeo: {'Sim' if save_video else 'Não'}")
    print(f"   Salvar CSV: {'Sim' if save_csv else 'Não'}")
    print(f"   Arquivo saída: {output_file}")
    print(f"🎯 Detecção de Movimento:")
    print(f"   Threshold: {args.motion_threshold}")
    print(f"   Área mínima: {args.min_area}")
    print(f"   Buffer movimento: {args.motion_buffer}")
    print(f"   Buffer inativo: {args.idle_buffer}")
    
    # Carregar modelo YOLOv8
    print("\n🤖 Carregando modelo YOLOv8...")
    model = YOLO('yolov8n.pt')
    
    # Inicializar tracker e detector de movimento
    tracker = Tracker()
    motion_tracker = AdaptiveMotionTracker(
        motion_threshold=args.motion_threshold,
        min_area=args.min_area,
        motion_buffer=args.motion_buffer,
        idle_buffer=args.idle_buffer
    )
    
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
    
    # Definir linha horizontal 20% abaixo do centro
    if width > 0 and height > 0:
        y_line = int(height * 0.6)  # 60% da altura
        line_p1 = (0, y_line)
        line_p2 = (width-1, y_line)
        # Zonas maiores: metade inferior direita e esquerda
        zone_right = (width//2, height//2, width-1, height-1)  # x1, y1, x2, y2
        zone_left = (0, height//2, width//2, height-1)
    else:
        line_p1 = line_p2 = None
        zone_right = zone_left = None
    
    print(f"✅ Conectado!")
    print(f"📹 Resolução: {width}x{height}")
    print(f"⚡ FPS: {fps}")
    
    # Configurar vídeo de saída
    out = None
    if save_video:
        fourcc = cv2.VideoWriter_fourcc(*'XVID')
        out = cv2.VideoWriter(output_file, fourcc, fps, (width, height))
    
    print("\n🎯 Iniciando tracking otimizado...")
    print("-" * 60)
    
    frame_count = 0
    processed_frames = 0
    motion_frames = 0
    idle_frames = 0
    start_time = time.time()
    
    # Lista para armazenar dados
    tracking_data = []
    
    # --- Definição da linha e zonas ---
    # Será inicializado após obter width/height do vídeo
    zone_names = {"right": "Inferior Direita", "left": "Inferior Esquerda", "none": "Fora das Zonas"}
    # Dicionário para armazenar tempo de entrada/saída por track_id e zona
    zone_times = {}
    # Dicionário para armazenar última posição do centro de cada track
    last_centers = {}
    # Dicionário para armazenar se cada track já cruzou a linha
    crossed_tracks = set()
    # Contador para relatórios parciais
    partial_report_counter = 0
    
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                print("⚠️  Erro ao ler frame - tentando reconectar...")
                time.sleep(1)
                continue
                
            frame_count += 1
            
            # Verificar se deve processar baseado no movimento
            should_process = motion_tracker.should_process_frame(frame)
            
            if should_process:
                motion_frames += 1
                # Processar apenas 1 a cada frame_skip frames
                if motion_frames % frame_skip != 0:
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
                        center_x = int((bbox[0] + bbox[2]) / 2)
                        center_y = int((bbox[1] + bbox[3]) / 2)
                        # --- Ponto de referência: centro horizontal e 20% acima da base ---
                        bbox_height = bbox[3] - bbox[1]
                        ref_x = int((bbox[0] + bbox[2]) / 2)
                        ref_y = int(bbox[3] - 0.2 * bbox_height)
                        
                        # Inicializar variáveis para este track
                        zone = zone_names["none"]
                        crossed_line = False
                        
                        # --- Zona ---
                        if zone_right is not None and zone_left is not None:
                            if point_in_zone(ref_x, ref_y, zone_right):
                                zone = zone_names["right"]
                                print(f"Track {track.track_id} entrou na zona: {zone}")
                                
                                # Salvar relatório parcial por evento importante
                                if tracking_data:
                                    partial_report_counter += 1
                                    timestamp_event = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    partial_csv_filename = os.path.join(output_dir, f"evento_zona_{timestamp_event}_{partial_report_counter}.csv")
                                    df_partial = pd.DataFrame(tracking_data)
                                    df_partial.to_csv(partial_csv_filename, index=False)
                                    print(f"💾 Relatório parcial salvo: {partial_csv_filename}")
                            elif point_in_zone(ref_x, ref_y, zone_left):
                                zone = zone_names["left"]
                                print(f"Track {track.track_id} entrou na zona: {zone}")
                                
                                # Salvar relatório parcial por evento importante
                                if tracking_data:
                                    partial_report_counter += 1
                                    timestamp_event = datetime.now().strftime("%Y%m%d_%H%M%S")
                                    partial_csv_filename = os.path.join(output_dir, f"evento_zona_{timestamp_event}_{partial_report_counter}.csv")
                                    df_partial = pd.DataFrame(tracking_data)
                                    df_partial.to_csv(partial_csv_filename, index=False)
                                    print(f"💾 Relatório parcial salvo: {partial_csv_filename}")
                        # --- Tempo de permanência ---
                        tid = track.track_id
                        if tid not in zone_times:
                            zone_times[tid] = {z: None for z in zone_names.values()}
                        # Entrada na zona
                        if zone != zone_names["none"] and zone_times[tid][zone] is None:
                            zone_times[tid][zone] = timestamp
                            print(f"Track {tid} entrou na zona: {zone}")
                            
                            # Salvar relatório parcial por evento importante
                            if tracking_data:
                                partial_report_counter += 1
                                timestamp_event = datetime.now().strftime("%Y%m%d_%H%M%S")
                                partial_csv_filename = os.path.join(output_dir, f"evento_zona_{timestamp_event}_{partial_report_counter}.csv")
                                df_partial = pd.DataFrame(tracking_data)
                                df_partial.to_csv(partial_csv_filename, index=False)
                                print(f"💾 Relatório parcial salvo: {partial_csv_filename}")
                        # Saída da zona
                        for z in zone_names.values():
                            if z != zone and zone_times[tid][z] is not None:
                                # Calcula tempo de permanência
                                zone_times[tid][z + "_dur"] = timestamp - zone_times[tid][z]
                                zone_times[tid][z] = None
                        # --- Tempo acumulado enquanto está na zona ---
                        zone_right_dur = 0
                        zone_left_dur = 0
                        if zone == zone_names["right"] and zone_times[tid][zone_names["right"]] is not None:
                            zone_right_dur = timestamp - zone_times[tid][zone_names["right"]]
                        elif zone_times[tid].get(zone_names["right"] + "_dur") is not None:
                            zone_right_dur = zone_times[tid][zone_names["right"] + "_dur"]
                        if zone == zone_names["left"] and zone_times[tid][zone_names["left"]] is not None:
                            zone_left_dur = timestamp - zone_times[tid][zone_names["left"]]
                        elif zone_times[tid].get(zone_names["left"] + "_dur") is not None:
                            zone_left_dur = zone_times[tid][zone_names["left"] + "_dur"]
                        # --- Cruzamento de linha ---
                        if line_p1 is not None and line_p2 is not None:
                            current_side = side_of_line(ref_x, ref_y, line_p1, line_p2)
                            if tid in last_centers and tid not in crossed_tracks:
                                last_side = side_of_line(last_centers[tid][0], last_centers[tid][1], line_p1, line_p2)
                                if last_side != current_side:
                                    crossed_line = True
                                    crossed_tracks.add(tid)
                                    print(f"Track {tid} cruzou a linha!")
                                    
                                    # Salvar relatório parcial por evento importante
                                    if tracking_data:
                                        partial_report_counter += 1
                                        timestamp_event = datetime.now().strftime("%Y%m%d_%H%M%S")
                                        partial_csv_filename = os.path.join(output_dir, f"evento_cruzamento_{timestamp_event}_{partial_report_counter}.csv")
                                        df_partial = pd.DataFrame(tracking_data)
                                        df_partial.to_csv(partial_csv_filename, index=False)
                                        print(f"💾 Relatório parcial salvo: {partial_csv_filename}")
                            last_centers[tid] = (ref_x, ref_y)
                        # --- Salvar dados ---
                        data = {
                            'Camera_ID': args.camera,
                            'Camera_Name': camera_info['name'],
                            'Frame': frame_count,
                            'Timestamp': timestamp,
                            'Track_ID': tid,
                            'X1': bbox[0],
                            'Y1': bbox[1],
                            'X2': bbox[2],
                            'Y2': bbox[3],
                            'Center_X': ref_x,
                            'Center_Y': ref_y,
                            'Zone': zone,
                            'Zone_Right_Dur': zone_right_dur,
                            'Zone_Left_Dur': zone_left_dur,
                            'Crossed_Line': crossed_line,
                            'Confidence': 0.8,
                            'Motion_Detected': True
                        }
                        tracking_data.append(data)
            else:
                idle_frames += 1
                # Manter tracker atualizado mesmo sem processamento
                if tracker.tracks is not None:
                    tracker.update(frame, [])
            
            # Desenhar bounding boxes e IDs
            if tracker.tracks is not None:
                for track in tracker.tracks:
                    bbox = track.bbox
                    track_id = track.track_id
                    x1, y1, x2, y2 = map(int, bbox)
                    
                    # Cor baseada no estado de movimento
                    color = (0, 255, 0) if should_process else (128, 128, 128)
                    
                    # Caixa
                    cv2.rectangle(frame, (x1, y1), (x2, y2), color, 2)
                    
                    # ID da pessoa
                    cv2.putText(frame, f'ID: {track_id}', (x1, y1 - 10),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
                    
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
                f"Tempo: {elapsed:.1f}s",
                f"Modo: {'PROCESSANDO' if should_process else 'AGUARDANDO'}",
                f"Movimento: {motion_frames} | Inativo: {idle_frames}"
            ]
            
            for i, text in enumerate(info_text):
                color = (0, 255, 0) if "PROCESSANDO" in text else (255, 255, 255)
                cv2.putText(frame, text, (10, 30 + i * 25),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.6, color, 2)
            
            # Mostrar detecção de movimento se solicitado
            if args.show_motion:
                motion_detector = motion_tracker.motion_detector
                if motion_detector.prev_frame is not None:
                    # Mostrar frame de diferença
                    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                    gray = cv2.GaussianBlur(gray, (21, 21), 0)
                    frame_delta = cv2.absdiff(motion_detector.prev_frame, gray)
                    thresh = cv2.threshold(frame_delta, args.motion_threshold, 255, cv2.THRESH_BINARY)[1]
                    thresh = cv2.dilate(thresh, None, iterations=2)
                    
                    # Converter para BGR para exibição
                    motion_display = cv2.cvtColor(thresh, cv2.COLOR_GRAY2BGR)
                    cv2.imshow('Motion Detection', motion_display)
            
            # --- Desenhar linha e zonas ---
            if zone_right is not None and zone_left is not None and line_p1 is not None and line_p2 is not None:
                # Zonas
                cv2.rectangle(frame, (zone_right[0], zone_right[1]), (zone_right[2], zone_right[3]), (0, 0, 255), 2)
                cv2.putText(frame, zone_names["right"], (zone_right[0]+10, zone_right[1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,0,255), 2)
                cv2.rectangle(frame, (zone_left[0], zone_left[1]), (zone_left[2], zone_left[3]), (255, 0, 0), 2)
                cv2.putText(frame, zone_names["left"], (zone_left[0]+10, zone_left[1]+30), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255,0,0), 2)
                # Linha horizontal
                cv2.line(frame, line_p1, line_p2, (0,255,255), 3)
                cv2.putText(frame, "Linha", (line_p1[0]-100, line_p1[1]-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,255), 2)
            
            # Mostrar display se solicitado
            if show_display:
                cv2.imshow(f'Motion Tracking - {camera_info["name"]}', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            
            # Salvar frame no vídeo de saída
            if save_video and out:
                out.write(frame)
            
            # Mostrar progresso a cada 30 frames
            if frame_count % 30 == 0:
                print(f"⏳ Frame {frame_count}: {current_tracks} pessoas | "
                      f"FPS: {current_fps:.1f} | Modo: {'PROCESSANDO' if should_process else 'AGUARDANDO'}")
            
            # Verificar limite de frames
            if max_frames > 0 and frame_count >= max_frames:
                break
                
    except KeyboardInterrupt:
        print("\n⚠️  Interrompido pelo usuário")
    except Exception as e:
        print(f"❌ Erro durante processamento: {e}")
    finally:
        cap.release()
        if out:
            out.release()
        if show_display or args.show_motion:
            cv2.destroyAllWindows()
    
    # Estatísticas finais
    total_time = time.time() - start_time
    print("\n" + "=" * 60)
    print("✅ PROCESSAMENTO OTIMIZADO CONCLUÍDO!")
    print(f"📹 Câmera: {camera_info['name']}")
    print(f"⏱️  Tempo total: {total_time:.1f} segundos")
    print(f"⚡ FPS médio: {processed_frames/total_time:.1f}")
    print(f"📊 Frames processados: {processed_frames}/{frame_count} ({processed_frames/frame_count*100:.1f}%)")
    print(f"🎯 Frames com movimento: {motion_frames}")
    print(f"😴 Frames inativos: {idle_frames}")
    print(f"👥 Pessoas únicas detectadas: {len(set([d['Track_ID'] for d in tracking_data]))}")
    print(f"🚪 Pessoas que saíram: {len(tracker.exited_persons)}")
    
    # Salvar relatório CSV
    if save_csv and tracking_data:
        df = pd.DataFrame(tracking_data)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = os.path.join(output_dir, f"motion_tracking_{args.camera}_{timestamp}.csv")
        df.to_csv(csv_filename, index=False)
        print(f"💾 Relatório salvo: {csv_filename}")
    
    if save_video:
        print(f"🎬 Vídeo salvo: {output_file}")
    
    print("\n🎯 TRACKING OTIMIZADO FINALIZADO!")

# --- Funções auxiliares para zonas e linha ---
def point_in_zone(x, y, zone):
    x1, y1, x2, y2 = zone
    return x1 <= x <= x2 and y1 <= y <= y2
def side_of_line(x, y, p1, p2):
    # Retorna >0 de um lado, <0 do outro, 0 na linha
    return (x - p1[0]) * (p2[1] - p1[1]) - (y - p1[1]) * (p2[0] - p1[0])

if __name__ == "__main__":
    main() 