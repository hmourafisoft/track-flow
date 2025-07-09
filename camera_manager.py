#!/usr/bin/env python3
"""
Gerenciador de câmeras com configuração via JSON
"""

import json
import os
import cv2
from typing import Dict, List, Optional, Tuple
import time

class CameraManager:
    def __init__(self, config_file: str = "camera_config.json"):
        """
        Inicializa o gerenciador de câmeras
        
        Args:
            config_file: Caminho para o arquivo de configuração JSON
        """
        self.config_file = config_file
        self.config = self.load_config()
        self.cameras = {}
        
    def load_config(self) -> Dict:
        """Carrega configuração do arquivo JSON"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                print(f"✅ Configuração carregada: {self.config_file}")
                return config
            else:
                print(f"⚠️  Arquivo de configuração não encontrado: {self.config_file}")
                return self.create_default_config()
        except Exception as e:
            print(f"❌ Erro ao carregar configuração: {e}")
            return self.create_default_config()
    
    def create_default_config(self) -> Dict:
        """Cria configuração padrão"""
        default_config = {
            "cameras": {
                "camera_1": {
                    "name": "Câmera Padrão",
                    "type": "dahua",
                    "ip": "192.168.15.88",
                    "port": 554,
                    "username": "admin",
                    "password": "sophia2011",
                    "stream_path": "cam/realmonitor?channel=1&subtype=0",
                    "enabled": True,
                    "description": "Câmera padrão"
                }
            },
            "default_settings": {
                "frame_skip": 1,
                "confidence": 0.5,
                "max_frames": 0,
                "show_display": True,
                "output_format": "avi",
                "save_video": True,
                "save_csv": True
            },
            "network_settings": {
                "timeout": 10,
                "reconnect_attempts": 3,
                "buffer_size": 1
            }
        }
        
        # Salvar configuração padrão
        self.save_config(default_config)
        return default_config
    
    def save_config(self, config: Dict = None):
        """Salva configuração no arquivo JSON"""
        if config is None:
            config = self.config
            
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            print(f"✅ Configuração salva: {self.config_file}")
        except Exception as e:
            print(f"❌ Erro ao salvar configuração: {e}")
    
    def get_camera_url(self, camera_id: str) -> Optional[str]:
        """Gera URL RTSP para uma câmera"""
        if camera_id not in self.config["cameras"]:
            print(f"❌ Câmera não encontrada: {camera_id}")
            return None
        
        camera = self.config["cameras"][camera_id]
        
        if not camera.get("enabled", True):
            print(f"⚠️  Câmera desabilitada: {camera_id}")
            return None
        
        if camera["type"] == "usb":
            return str(camera.get("source", 0))
        
        # Construir URL RTSP
        username = camera.get("username", "")
        password = camera.get("password", "")
        ip = camera.get("ip", "")
        port = camera.get("port", 554)
        stream_path = camera.get("stream_path", "stream1")
        
        if username and password:
            return f"rtsp://{username}:{password}@{ip}:{port}/{stream_path}"
        else:
            return f"rtsp://{ip}:{port}/{stream_path}"
    
    def get_camera_info(self, camera_id: str) -> Optional[Dict]:
        """Retorna informações de uma câmera"""
        if camera_id in self.config["cameras"]:
            return self.config["cameras"][camera_id]
        return None
    
    def list_cameras(self) -> List[Tuple[str, Dict]]:
        """Lista todas as câmeras configuradas"""
        cameras = []
        for camera_id, camera_info in self.config["cameras"].items():
            cameras.append((camera_id, camera_info))
        return cameras
    
    def add_camera(self, camera_id: str, camera_info: Dict):
        """Adiciona uma nova câmera"""
        self.config["cameras"][camera_id] = camera_info
        self.save_config()
        print(f"✅ Câmera adicionada: {camera_id}")
    
    def remove_camera(self, camera_id: str):
        """Remove uma câmera"""
        if camera_id in self.config["cameras"]:
            del self.config["cameras"][camera_id]
            self.save_config()
            print(f"✅ Câmera removida: {camera_id}")
        else:
            print(f"❌ Câmera não encontrada: {camera_id}")
    
    def enable_camera(self, camera_id: str):
        """Habilita uma câmera"""
        if camera_id in self.config["cameras"]:
            self.config["cameras"][camera_id]["enabled"] = True
            self.save_config()
            print(f"✅ Câmera habilitada: {camera_id}")
        else:
            print(f"❌ Câmera não encontrada: {camera_id}")
    
    def disable_camera(self, camera_id: str):
        """Desabilita uma câmera"""
        if camera_id in self.config["cameras"]:
            self.config["cameras"][camera_id]["enabled"] = False
            self.save_config()
            print(f"✅ Câmera desabilitada: {camera_id}")
        else:
            print(f"❌ Câmera não encontrada: {camera_id}")
    
    def test_camera_connection(self, camera_id: str, max_frames: int = 5) -> bool:
        """Testa conexão com uma câmera"""
        url = self.get_camera_url(camera_id)
        if not url:
            return False
        
        camera_info = self.get_camera_info(camera_id)
        print(f"🔗 Testando câmera: {camera_info['name']} ({camera_id})")
        print(f"   URL: {url}")
        
        try:
            cap = cv2.VideoCapture(url)
            
            if not cap.isOpened():
                print("❌ Falha ao conectar")
                return False
            
            # Configurar buffer mínimo para RTSP
            cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
            
            # Testar leitura de frames
            frame_count = 0
            start_time = time.time()
            
            while frame_count < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                frame_count += 1
            
            cap.release()
            
            total_time = time.time() - start_time
            fps = frame_count / total_time if total_time > 0 else 0
            
            if frame_count > 0:
                print(f"✅ Conexão OK - {frame_count} frames em {total_time:.1f}s (FPS: {fps:.1f})")
                return True
            else:
                print("❌ Não foi possível ler frames")
                return False
                
        except Exception as e:
            print(f"❌ Erro: {e}")
            return False
    
    def get_default_settings(self) -> Dict:
        """Retorna configurações padrão"""
        return self.config.get("default_settings", {})
    
    def get_network_settings(self) -> Dict:
        """Retorna configurações de rede"""
        return self.config.get("network_settings", {})

def main():
    """Função principal para testar o gerenciador"""
    manager = CameraManager()
    
    print("📹 GERENCIADOR DE CÂMERAS")
    print("=" * 50)
    
    # Listar câmeras
    print("\n📋 Câmeras configuradas:")
    cameras = manager.list_cameras()
    for camera_id, camera_info in cameras:
        status = "✅ Habilitada" if camera_info.get("enabled", True) else "❌ Desabilitada"
        print(f"   {camera_id}: {camera_info['name']} ({camera_info['type']}) - {status}")
    
    # Testar primeira câmera habilitada
    print("\n🧪 Testando primeira câmera habilitada:")
    for camera_id, camera_info in cameras:
        if camera_info.get("enabled", True):
            manager.test_camera_connection(camera_id)
            break
    
    # Mostrar configurações
    print(f"\n⚙️  Configurações padrão:")
    default_settings = manager.get_default_settings()
    for key, value in default_settings.items():
        print(f"   {key}: {value}")

if __name__ == "__main__":
    main() 