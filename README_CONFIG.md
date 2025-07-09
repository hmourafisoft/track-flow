# Sistema de Configuração de Câmeras

## 🎯 Visão Geral

Este sistema permite gerenciar múltiplas câmeras IP através de um arquivo de configuração JSON, facilitando a administração de várias câmeras sem precisar modificar código.

## 📁 Arquivos do Sistema

### **`camera_config.json`**
Arquivo de configuração principal com:
- Configurações de cada câmera
- Parâmetros padrão do sistema
- Configurações de rede

### **`camera_manager.py`**
Gerenciador de câmeras que:
- Carrega/salva configurações
- Gera URLs RTSP
- Testa conexões
- Gerencia câmeras

### **`config_tracking.py`**
Sistema de tracking que usa configurações:
- Lê configurações do JSON
- Suporta múltiplas câmeras
- Parâmetros configuráveis

### **`manage_cameras.py`**
Interface interativa para:
- Adicionar/editar câmeras
- Testar conexões
- Configurar parâmetros

## 🚀 Como Usar

### **1. Configuração Inicial**

O sistema já vem com sua câmera configurada:

```json
{
  "cameras": {
    "camera_1": {
      "name": "Câmera Principal",
      "type": "dahua",
      "ip": "192.168.15.88",
      "port": 554,
      "username": "admin",
      "password": "sophia2011",
      "stream_path": "cam/realmonitor?channel=1&subtype=0",
      "enabled": true,
      "description": "Câmera principal da entrada"
    }
  }
}
```

### **2. Gerenciar Câmeras Interativamente**

```bash
python manage_cameras.py
```

**Opções disponíveis:**
- **1. Listar câmeras** - Ver todas as câmeras configuradas
- **2. Adicionar câmera** - Adicionar nova câmera
- **3. Editar câmera** - Modificar câmera existente
- **4. Remover câmera** - Remover câmera
- **5. Habilitar/Desabilitar** - Ativar/desativar câmera
- **6. Testar conexão** - Testar conectividade
- **7. Configurações padrão** - Ajustar parâmetros gerais

### **3. Executar Tracking**

```bash
# Usar câmera padrão (camera_1)
python config_tracking.py

# Especificar câmera
python config_tracking.py --camera camera_1

# Com visualização
python config_tracking.py --camera camera_1 --show-display

# Teste rápido
python config_tracking.py --camera camera_1 --max-frames 50 --show-display

# Apenas testar conexão
python config_tracking.py --camera camera_1 --test-only

# Listar câmeras disponíveis
python config_tracking.py --list-cameras
```

## 🔧 Configuração de Câmeras

### **Tipos Suportados**

1. **DAHUA**
   ```json
   {
     "type": "dahua",
     "stream_path": "cam/realmonitor?channel=1&subtype=0"
   }
   ```

2. **HIKVISION**
   ```json
   {
     "type": "hikvision",
     "stream_path": "Streaming/Channels/101"
   }
   ```

3. **AXIS**
   ```json
   {
     "type": "axis",
     "stream_path": "axis-media/media.amp"
   }
   ```

4. **FOSCAM**
   ```json
   {
     "type": "foscam",
     "stream_path": "videoMain"
   }
   ```

5. **Genérica (ONVIF)**
   ```json
   {
     "type": "generic",
     "stream_path": "stream1"
   }
   ```

6. **USB Local**
   ```json
   {
     "type": "usb",
     "source": 0
   }
   ```

### **Estrutura de Configuração**

```json
{
  "cameras": {
    "camera_id": {
      "name": "Nome da Câmera",
      "type": "tipo_camera",
      "ip": "192.168.1.100",
      "port": 554,
      "username": "admin",
      "password": "password",
      "stream_path": "caminho/do/stream",
      "enabled": true,
      "description": "Descrição opcional"
    }
  },
  "default_settings": {
    "frame_skip": 1,
    "confidence": 0.5,
    "max_frames": 0,
    "show_display": true,
    "output_format": "avi",
    "save_video": true,
    "save_csv": true
  },
  "network_settings": {
    "timeout": 10,
    "reconnect_attempts": 3,
    "buffer_size": 1
  }
}
```

## 📊 Parâmetros Configuráveis

### **Configurações de Câmera**
- `name`: Nome amigável da câmera
- `type`: Tipo da câmera (dahua, hikvision, etc.)
- `ip`: Endereço IP da câmera
- `port`: Porta RTSP (padrão: 554)
- `username`: Usuário de acesso
- `password`: Senha de acesso
- `stream_path`: Caminho do stream RTSP
- `enabled`: Se a câmera está ativa
- `description`: Descrição opcional

### **Configurações Padrão**
- `frame_skip`: Processar 1 a cada N frames
- `confidence`: Confiança mínima para detecção (0.0-1.0)
- `max_frames`: Máximo de frames (0 = ilimitado)
- `show_display`: Mostrar visualização em tempo real
- `save_video`: Salvar vídeo processado
- `save_csv`: Salvar relatório CSV

### **Configurações de Rede**
- `timeout`: Timeout de conexão em segundos
- `reconnect_attempts`: Tentativas de reconexão
- `buffer_size`: Tamanho do buffer RTSP

## 🎯 Exemplos de Uso

### **1. Adicionar Nova Câmera**

```bash
python manage_cameras.py
# Escolher opção 2 (Adicionar câmera)
# Seguir o assistente interativo
```

### **2. Testar Todas as Câmeras**

```bash
# Listar câmeras
python config_tracking.py --list-cameras

# Testar cada câmera
python config_tracking.py --camera camera_1 --test-only
python config_tracking.py --camera camera_2 --test-only
```

### **3. Tracking com Configurações Personalizadas**

```bash
# Alta performance
python config_tracking.py --camera camera_1 --frame-skip 3 --confidence 0.7

# Visualização apenas
python config_tracking.py --camera camera_1 --show-display --max-frames 100

# Gravação contínua
python config_tracking.py --camera camera_1 --output monitoramento_24h.avi
```

### **4. Múltiplas Câmeras**

```bash
# Processar câmera 1
python config_tracking.py --camera camera_1 --output cam1.avi &

# Processar câmera 2
python config_tracking.py --camera camera_2 --output cam2.avi &

# Aguardar conclusão
wait
```

## 🔍 Solução de Problemas

### **Câmera Não Conecta**
1. Verificar IP e credenciais
2. Testar com `--test-only`
3. Verificar se câmera está habilitada
4. Testar conectividade de rede

### **Performance Baixa**
1. Aumentar `frame_skip`
2. Reduzir resolução da câmera
3. Aumentar `confidence`
4. Verificar uso de CPU

### **Erro de Configuração**
1. Verificar sintaxe do JSON
2. Usar `manage_cameras.py` para editar
3. Fazer backup antes de modificar

## 📈 Monitoramento

### **Logs de Sistema**
```bash
# Executar com logs detalhados
python config_tracking.py --camera camera_1 2>&1 | tee tracking.log
```

### **Métricas Importantes**
- FPS de processamento
- Latência de conexão
- Número de reconexões
- Precisão de detecção

## 🔒 Segurança

### **Boas Práticas**
- ✅ Usar credenciais fortes
- ✅ Isolar câmeras em VLAN
- ✅ Atualizar firmware
- ✅ Fazer backup das configurações
- ❌ Não expor câmeras na internet

### **Backup de Configuração**
```bash
# Fazer backup
cp camera_config.json camera_config_backup.json

# Restaurar backup
cp camera_config_backup.json camera_config.json
```

## 🆘 Suporte

### **Comandos Úteis**

```bash
# Verificar configuração
python manage_cameras.py

# Testar conexão
python config_tracking.py --camera camera_1 --test-only

# Listar câmeras
python config_tracking.py --list-cameras

# Ver ajuda
python config_tracking.py --help
```

### **Problemas Comuns**

1. **"Câmera não encontrada"**
   - Verificar ID da câmera
   - Usar `--list-cameras`

2. **"Câmera desabilitada"**
   - Habilitar via `manage_cameras.py`
   - Verificar campo `enabled`

3. **"Erro de conexão"**
   - Testar com `--test-only`
   - Verificar IP e credenciais
   - Testar conectividade de rede

O sistema está pronto para gerenciar múltiplas câmeras de forma eficiente! 🎥✨ 