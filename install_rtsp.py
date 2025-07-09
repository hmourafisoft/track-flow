#!/usr/bin/env python3
"""
Script de instalação e teste para sistema RTSP
"""

import subprocess
import sys
import os

def run_command(command, description):
    """Executa comando e mostra resultado"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - ERRO")
            print(f"   Erro: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ {description} - EXCEÇÃO: {e}")
        return False

def check_python_version():
    """Verifica versão do Python"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version.major < 3 or (version.major == 3 and version.minor < 7):
        print("❌ Python 3.7+ é necessário")
        return False
    
    print("✅ Versão do Python OK")
    return True

def install_dependencies():
    """Instala dependências"""
    print("\n📦 INSTALANDO DEPENDÊNCIAS")
    print("=" * 40)
    
    # Verificar se pip está disponível
    if not run_command("pip --version", "Verificando pip"):
        print("❌ pip não encontrado. Instale o Python com pip.")
        return False
    
    # Instalar dependências
    dependencies = [
        "opencv-python>=4.5.0",
        "numpy>=1.21.0",
        "ultralytics==8.0.33",
        "pandas>=1.3.0",
        "scikit-learn>=1.0.0",
        "tensorflow>=2.8.0",
        "scikit-image>=0.19.0",
        "filterpy>=1.4.5"
    ]
    
    for dep in dependencies:
        if not run_command(f"pip install {dep}", f"Instalando {dep}"):
            print(f"⚠️  Falha ao instalar {dep}")
    
    return True

def test_imports():
    """Testa importações principais"""
    print("\n🧪 TESTANDO IMPORTAÇÕES")
    print("=" * 40)
    
    imports = [
        ("cv2", "OpenCV"),
        ("numpy", "NumPy"),
        ("ultralytics", "Ultralytics YOLOv8"),
        ("pandas", "Pandas"),
        ("sklearn", "Scikit-learn"),
        ("tensorflow", "TensorFlow")
    ]
    
    all_ok = True
    for module, name in imports:
        try:
            __import__(module)
            print(f"✅ {name} - OK")
        except ImportError as e:
            print(f"❌ {name} - ERRO: {e}")
            all_ok = False
    
    return all_ok

def test_camera_access():
    """Testa acesso à câmera local"""
    print("\n📹 TESTANDO CÂMERA LOCAL")
    print("=" * 40)
    
    try:
        import cv2
        cap = cv2.VideoCapture(0)
        
        if cap.isOpened():
            ret, frame = cap.read()
            cap.release()
            
            if ret:
                print("✅ Câmera local acessível")
                return True
            else:
                print("⚠️  Câmera local encontrada mas não consegue ler frames")
                return False
        else:
            print("⚠️  Câmera local não encontrada")
            return False
            
    except Exception as e:
        print(f"❌ Erro ao testar câmera: {e}")
        return False

def show_next_steps():
    """Mostra próximos passos"""
    print("\n🎯 PRÓXIMOS PASSOS")
    print("=" * 40)
    
    print("1. Testar câmera local:")
    print("   python test_rtsp_connection.py --local")
    
    print("\n2. Testar câmera IP:")
    print("   python test_rtsp_connection.py --ip 192.168.1.100 --username admin --password password")
    
    print("\n3. Executar tracking completo:")
    print("   python rtsp_tracking.py --source 0 --show-display")
    
    print("\n4. Ver exemplos de configuração:")
    print("   python rtsp_examples.py")
    
    print("\n5. Documentação completa:")
    print("   Ver README_RTSP.md")

def main():
    """Função principal"""
    print("🚀 INSTALADOR DO SISTEMA RTSP")
    print("=" * 50)
    
    # Verificar Python
    if not check_python_version():
        return
    
    # Instalar dependências
    if not install_dependencies():
        print("❌ Falha na instalação das dependências")
        return
    
    # Testar importações
    if not test_imports():
        print("❌ Falha nos testes de importação")
        return
    
    # Testar câmera
    test_camera_access()
    
    # Mostrar próximos passos
    show_next_steps()
    
    print("\n🎉 INSTALAÇÃO CONCLUÍDA!")
    print("Agora você pode usar o sistema de tracking RTSP!")

if __name__ == "__main__":
    main() 