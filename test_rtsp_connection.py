#!/usr/bin/env python3
"""
Script para testar conexão RTSP sem processamento pesado
"""

import cv2
import time
import argparse

def test_rtsp_connection(rtsp_url, max_frames=10):
    """
    Testa conexão RTSP básica
    """
    print(f"🔗 Testando conexão RTSP: {rtsp_url}")
    print("-" * 50)
    
    # Tentar conectar
    cap = cv2.VideoCapture(rtsp_url)
    
    if not cap.isOpened():
        print("❌ Falha ao conectar ao stream RTSP")
        return False
    
    # Configurar buffer mínimo para RTSP
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    
    print("✅ Conexão estabelecida!")
    
    # Obter informações do stream
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📹 Resolução: {width}x{height}")
    print(f"⚡ FPS: {fps}")
    
    # Testar leitura de frames
    frame_count = 0
    start_time = time.time()
    
    print("\n🔄 Testando leitura de frames...")
    
    while frame_count < max_frames:
        ret, frame = cap.read()
        
        if not ret:
            print(f"❌ Erro ao ler frame {frame_count + 1}")
            break
        
        frame_count += 1
        
        if frame_count % 5 == 0:
            elapsed = time.time() - start_time
            current_fps = frame_count / elapsed
            print(f"   Frame {frame_count}: OK (FPS: {current_fps:.1f})")
    
    cap.release()
    
    # Resultados
    total_time = time.time() - start_time
    avg_fps = frame_count / total_time if total_time > 0 else 0
    
    print("\n" + "=" * 50)
    print("📊 RESULTADOS DO TESTE:")
    print(f"✅ Frames lidos: {frame_count}/{max_frames}")
    print(f"⏱️  Tempo total: {total_time:.1f}s")
    print(f"⚡ FPS médio: {avg_fps:.1f}")
    
    if frame_count == max_frames:
        print("🎉 Teste concluído com sucesso!")
        return True
    else:
        print("⚠️  Teste incompleto - verifique a conexão")
        return False

def test_local_camera(camera_index=0):
    """
    Testa câmera local (USB)
    """
    print(f"📹 Testando câmera local (índice {camera_index})")
    print("-" * 50)
    
    cap = cv2.VideoCapture(camera_index)
    
    if not cap.isOpened():
        print("❌ Não foi possível abrir a câmera local")
        return False
    
    print("✅ Câmera local conectada!")
    
    # Obter informações
    fps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    
    print(f"📹 Resolução: {width}x{height}")
    print(f"⚡ FPS: {fps}")
    
    # Testar alguns frames
    for i in range(5):
        ret, frame = cap.read()
        if ret:
            print(f"   Frame {i+1}: OK")
        else:
            print(f"   Frame {i+1}: ERRO")
    
    cap.release()
    print("✅ Teste da câmera local concluído!")
    return True

def main():
    parser = argparse.ArgumentParser(description='Teste de conexão RTSP')
    parser.add_argument('--url', type=str, help='URL RTSP para testar')
    parser.add_argument('--ip', type=str, help='IP da câmera')
    parser.add_argument('--username', type=str, help='Usuário')
    parser.add_argument('--password', type=str, help='Senha')
    parser.add_argument('--stream', type=str, default='stream1', help='Caminho do stream')
    parser.add_argument('--port', type=int, default=554, help='Porta RTSP')
    parser.add_argument('--local', action='store_true', help='Testar câmera local')
    parser.add_argument('--frames', type=int, default=10, help='Número de frames para testar')
    
    args = parser.parse_args()
    
    print("🧪 TESTE DE CONEXÃO RTSP")
    print("=" * 50)
    
    if args.local:
        # Testar câmera local
        test_local_camera()
    elif args.url:
        # Testar URL RTSP direta
        test_rtsp_connection(args.url, args.frames)
    elif args.ip:
        # Construir URL RTSP
        if args.username and args.password:
            rtsp_url = f"rtsp://{args.username}:{args.password}@{args.ip}:{args.port}/{args.stream}"
        else:
            rtsp_url = f"rtsp://{args.ip}:{args.port}/{args.stream}"
        
        test_rtsp_connection(rtsp_url, args.frames)
    else:
        print("❌ Especifique --url, --ip ou --local")
        print("\nExemplos:")
        print("  python test_rtsp_connection.py --local")
        print("  python test_rtsp_connection.py --ip 192.168.1.100 --username admin --password password")
        print("  python test_rtsp_connection.py --url rtsp://192.168.1.100:554/stream1")

if __name__ == "__main__":
    main() 