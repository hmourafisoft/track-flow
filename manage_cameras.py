#!/usr/bin/env python3
"""
Script interativo para gerenciar configurações de câmeras
"""

import json
import os
from camera_manager import CameraManager

def print_menu():
    """Mostra menu principal"""
    print("\n" + "=" * 50)
    print("📹 GERENCIADOR DE CÂMERAS")
    print("=" * 50)
    print("1. Listar câmeras")
    print("2. Adicionar câmera")
    print("3. Editar câmera")
    print("4. Remover câmera")
    print("5. Habilitar/Desabilitar câmera")
    print("6. Testar conexão")
    print("7. Editar configurações padrão")
    print("8. Salvar e sair")
    print("0. Sair sem salvar")
    print("-" * 50)

def get_camera_type():
    """Solicita tipo de câmera"""
    print("\n📹 Tipos de câmera disponíveis:")
    print("1. dahua")
    print("2. hikvision")
    print("3. axis")
    print("4. foscam")
    print("5. generic")
    print("6. usb")
    
    while True:
        choice = input("Escolha o tipo (1-6): ").strip()
        types = {
            "1": "dahua",
            "2": "hikvision", 
            "3": "axis",
            "4": "foscam",
            "5": "generic",
            "6": "usb"
        }
        if choice in types:
            return types[choice]
        print("❌ Opção inválida. Tente novamente.")

def get_stream_path(camera_type):
    """Sugere stream path baseado no tipo"""
    paths = {
        "dahua": "cam/realmonitor?channel=1&subtype=0",
        "hikvision": "Streaming/Channels/101",
        "axis": "axis-media/media.amp",
        "foscam": "videoMain",
        "generic": "stream1"
    }
    return paths.get(camera_type, "stream1")

def add_camera_interactive(manager):
    """Adiciona câmera de forma interativa"""
    print("\n➕ ADICIONAR NOVA CÂMERA")
    print("-" * 30)
    
    camera_id = input("ID da câmera (ex: camera_1): ").strip()
    if not camera_id:
        print("❌ ID é obrigatório")
        return
    
    if manager.get_camera_info(camera_id):
        print(f"❌ Câmera {camera_id} já existe")
        return
    
    name = input("Nome da câmera: ").strip()
    if not name:
        name = f"Câmera {camera_id}"
    
    camera_type = get_camera_type()
    
    camera_info = {
        "name": name,
        "type": camera_type,
        "enabled": True,
        "description": input("Descrição (opcional): ").strip()
    }
    
    if camera_type == "usb":
        source = input("Índice da câmera USB (0): ").strip()
        camera_info["source"] = int(source) if source.isdigit() else 0
    else:
        camera_info["ip"] = input("IP da câmera: ").strip()
        camera_info["port"] = int(input("Porta RTSP (554): ").strip() or "554")
        camera_info["username"] = input("Usuário: ").strip()
        camera_info["password"] = input("Senha: ").strip()
        
        # Sugerir stream path
        suggested_path = get_stream_path(camera_type)
        stream_path = input(f"Stream path ({suggested_path}): ").strip()
        camera_info["stream_path"] = stream_path if stream_path else suggested_path
    
    manager.add_camera(camera_id, camera_info)
    print(f"✅ Câmera {camera_id} adicionada com sucesso!")

def edit_camera_interactive(manager):
    """Edita câmera de forma interativa"""
    print("\n✏️  EDITAR CÂMERA")
    print("-" * 20)
    
    # Listar câmeras
    cameras = manager.list_cameras()
    if not cameras:
        print("❌ Nenhuma câmera configurada")
        return
    
    print("Câmeras disponíveis:")
    for i, (camera_id, camera_info) in enumerate(cameras, 1):
        status = "✅" if camera_info.get("enabled", True) else "❌"
        print(f"{i}. {camera_id}: {camera_info['name']} {status}")
    
    try:
        choice = int(input("Escolha a câmera (número): ")) - 1
        if 0 <= choice < len(cameras):
            camera_id, camera_info = cameras[choice]
        else:
            print("❌ Opção inválida")
            return
    except ValueError:
        print("❌ Entrada inválida")
        return
    
    print(f"\n📹 Editando: {camera_id}")
    print(f"Nome atual: {camera_info['name']}")
    
    new_name = input("Novo nome (Enter para manter): ").strip()
    if new_name:
        camera_info['name'] = new_name
    
    new_description = input("Nova descrição (Enter para manter): ").strip()
    if new_description:
        camera_info['description'] = new_description
    
    if camera_info['type'] != 'usb':
        new_ip = input(f"Novo IP ({camera_info.get('ip', '')}): ").strip()
        if new_ip:
            camera_info['ip'] = new_ip
        
        new_username = input(f"Novo usuário ({camera_info.get('username', '')}): ").strip()
        if new_username:
            camera_info['username'] = new_username
        
        new_password = input("Nova senha (Enter para manter): ").strip()
        if new_password:
            camera_info['password'] = new_password
    
    manager.config["cameras"][camera_id] = camera_info
    manager.save_config()
    print("✅ Câmera atualizada!")

def toggle_camera_status(manager):
    """Habilita/desabilita câmera"""
    print("\n🔄 HABILITAR/DESABILITAR CÂMERA")
    print("-" * 30)
    
    cameras = manager.list_cameras()
    if not cameras:
        print("❌ Nenhuma câmera configurada")
        return
    
    print("Câmeras disponíveis:")
    for i, (camera_id, camera_info) in enumerate(cameras, 1):
        status = "✅ Habilitada" if camera_info.get("enabled", True) else "❌ Desabilitada"
        print(f"{i}. {camera_id}: {camera_info['name']} - {status}")
    
    try:
        choice = int(input("Escolha a câmera (número): ")) - 1
        if 0 <= choice < len(cameras):
            camera_id, camera_info = cameras[choice]
        else:
            print("❌ Opção inválida")
            return
    except ValueError:
        print("❌ Entrada inválida")
        return
    
    current_status = camera_info.get("enabled", True)
    if current_status:
        manager.disable_camera(camera_id)
    else:
        manager.enable_camera(camera_id)

def edit_default_settings(manager):
    """Edita configurações padrão"""
    print("\n⚙️  CONFIGURAÇÕES PADRÃO")
    print("-" * 25)
    
    settings = manager.get_default_settings()
    
    print("Configurações atuais:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    print("\nNovos valores (Enter para manter):")
    
    new_frame_skip = input(f"Frame skip ({settings.get('frame_skip', 1)}): ").strip()
    if new_frame_skip and new_frame_skip.isdigit():
        settings['frame_skip'] = int(new_frame_skip)
    
    new_confidence = input(f"Confiança ({settings.get('confidence', 0.5)}): ").strip()
    if new_confidence:
        try:
            settings['confidence'] = float(new_confidence)
        except ValueError:
            print("❌ Valor inválido para confiança")
    
    new_show_display = input(f"Mostrar display ({settings.get('show_display', True)}): ").strip().lower()
    if new_show_display in ['true', '1', 'sim', 's', 'y', 'yes']:
        settings['show_display'] = True
    elif new_show_display in ['false', '0', 'não', 'n', 'no']:
        settings['show_display'] = False
    
    new_save_video = input(f"Salvar vídeo ({settings.get('save_video', True)}): ").strip().lower()
    if new_save_video in ['true', '1', 'sim', 's', 'y', 'yes']:
        settings['save_video'] = True
    elif new_save_video in ['false', '0', 'não', 'n', 'no']:
        settings['save_video'] = False
    
    new_save_csv = input(f"Salvar CSV ({settings.get('save_csv', True)}): ").strip().lower()
    if new_save_csv in ['true', '1', 'sim', 's', 'y', 'yes']:
        settings['save_csv'] = True
    elif new_save_csv in ['false', '0', 'não', 'n', 'no']:
        settings['save_csv'] = False
    
    manager.config["default_settings"] = settings
    manager.save_config()
    print("✅ Configurações padrão atualizadas!")

def main():
    """Função principal"""
    config_file = "camera_config.json"
    manager = CameraManager(config_file)
    
    while True:
        print_menu()
        
        try:
            choice = input("Escolha uma opção: ").strip()
            
            if choice == "1":
                print("\n📋 Câmeras configuradas:")
                cameras = manager.list_cameras()
                for camera_id, camera_info in cameras:
                    status = "✅ Habilitada" if camera_info.get("enabled", True) else "❌ Desabilitada"
                    print(f"   {camera_id}: {camera_info['name']} ({camera_info['type']}) - {status}")
                    if camera_info.get("description"):
                        print(f"      Descrição: {camera_info['description']}")
            
            elif choice == "2":
                add_camera_interactive(manager)
            
            elif choice == "3":
                edit_camera_interactive(manager)
            
            elif choice == "4":
                print("\n🗑️  REMOVER CÂMERA")
                camera_id = input("ID da câmera: ").strip()
                if camera_id:
                    confirm = input(f"Confirmar remoção de {camera_id}? (s/N): ").strip().lower()
                    if confirm in ['s', 'sim', 'y', 'yes']:
                        manager.remove_camera(camera_id)
            
            elif choice == "5":
                toggle_camera_status(manager)
            
            elif choice == "6":
                print("\n🧪 TESTAR CONEXÃO")
                cameras = manager.list_cameras()
                if not cameras:
                    print("❌ Nenhuma câmera configurada")
                    continue
                
                print("Câmeras disponíveis:")
                for i, (camera_id, camera_info) in enumerate(cameras, 1):
                    if camera_info.get("enabled", True):
                        print(f"{i}. {camera_id}: {camera_info['name']}")
                
                try:
                    choice = int(input("Escolha a câmera (número): ")) - 1
                    if 0 <= choice < len(cameras):
                        camera_id, camera_info = cameras[choice]
                        if camera_info.get("enabled", True):
                            manager.test_camera_connection(camera_id)
                        else:
                            print("❌ Câmera desabilitada")
                    else:
                        print("❌ Opção inválida")
                except ValueError:
                    print("❌ Entrada inválida")
            
            elif choice == "7":
                edit_default_settings(manager)
            
            elif choice == "8":
                print("✅ Configurações salvas!")
                break
            
            elif choice == "0":
                print("❌ Alterações não salvas!")
                break
            
            else:
                print("❌ Opção inválida")
                
        except KeyboardInterrupt:
            print("\n⚠️  Interrompido pelo usuário")
            break
        except Exception as e:
            print(f"❌ Erro: {e}")

if __name__ == "__main__":
    main() 