#!/usr/bin/env python3
"""
Exemplos de configuração para diferentes tipos de câmeras IP via RTSP
"""

# ============================================================================
# EXEMPLOS DE CONFIGURAÇÃO PARA DIFERENTES CÂMERAS IP
# ============================================================================

# 1. CÂMERA HIKVISION
HIKVISION_EXAMPLES = {
    "rtsp_url": "rtsp://admin:password@192.168.1.100:554/Streaming/Channels/101",
    "command": "python rtsp_tracking.py --ip 192.168.1.100 --username admin --password password --stream Streaming/Channels/101"
}

# 2. CÂMERA DAHUA
DAHUA_EXAMPLES = {
    "rtsp_url": "rtsp://admin:password@192.168.1.101:554/cam/realmonitor?channel=1&subtype=0",
    "command": "python rtsp_tracking.py --ip 192.168.1.101 --username admin --password password --stream cam/realmonitor?channel=1&subtype=0"
}

# 3. CÂMERA AXIS
AXIS_EXAMPLES = {
    "rtsp_url": "rtsp://root:password@192.168.1.102:554/axis-media/media.amp",
    "command": "python rtsp_tracking.py --ip 192.168.1.102 --username root --password password --stream axis-media/media.amp"
}

# 4. CÂMERA FOSCAM
FOSCAM_EXAMPLES = {
    "rtsp_url": "rtsp://admin:password@192.168.1.103:554/videoMain",
    "command": "python rtsp_tracking.py --ip 192.168.1.103 --username admin --password password --stream videoMain"
}

# 5. CÂMERA GENÉRICA (ONVIF)
GENERIC_EXAMPLES = {
    "rtsp_url": "rtsp://admin:password@192.168.1.104:554/stream1",
    "command": "python rtsp_tracking.py --ip 192.168.1.104 --username admin --password password --stream stream1"
}

# 6. CÂMERA USB (para teste local)
USB_CAMERA_EXAMPLES = {
    "rtsp_url": "0",  # Câmera USB padrão
    "command": "python rtsp_tracking.py --source 0 --show-display"
}

# ============================================================================
# COMANDOS DE EXEMPLO PARA EXECUTAR
# ============================================================================

def print_examples():
    print("🎥 EXEMPLOS DE CONFIGURAÇÃO PARA CÂMERAS IP")
    print("=" * 60)
    
    examples = [
        ("HIKVISION", HIKVISION_EXAMPLES),
        ("DAHUA", DAHUA_EXAMPLES),
        ("AXIS", AXIS_EXAMPLES),
        ("FOSCAM", FOSCAM_EXAMPLES),
        ("GENÉRICA", GENERIC_EXAMPLES),
        ("USB", USB_CAMERA_EXAMPLES)
    ]
    
    for name, config in examples:
        print(f"\n📹 {name}:")
        print(f"   URL RTSP: {config['rtsp_url']}")
        print(f"   Comando: {config['command']}")
    
    print("\n" + "=" * 60)
    print("🔧 CONFIGURAÇÕES AVANÇADAS:")
    print("\n1. Teste rápido (50 frames):")
    print("   python rtsp_tracking.py --ip 192.168.1.100 --max-frames 50 --show-display")
    
    print("\n2. Alta performance (pular frames):")
    print("   python rtsp_tracking.py --ip 192.168.1.100 --frame-skip 3 --confidence 0.7")
    
    print("\n3. Salvar vídeo com nome personalizado:")
    print("   python rtsp_tracking.py --ip 192.168.1.100 --output minha_camera.avi")
    
    print("\n4. Apenas visualização (sem salvar):")
    print("   python rtsp_tracking.py --ip 192.168.1.100 --show-display --output ''")
    
    print("\n5. Alta confiança (menos falsos positivos):")
    print("   python rtsp_tracking.py --ip 192.168.1.100 --confidence 0.8")

def get_camera_config(camera_type):
    """Retorna configuração para tipo específico de câmera"""
    configs = {
        "hikvision": HIKVISION_EXAMPLES,
        "dahua": DAHUA_EXAMPLES,
        "axis": AXIS_EXAMPLES,
        "foscam": FOSCAM_EXAMPLES,
        "generic": GENERIC_EXAMPLES,
        "usb": USB_CAMERA_EXAMPLES
    }
    return configs.get(camera_type.lower())

if __name__ == "__main__":
    print_examples() 