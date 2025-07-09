# Sistema de Tracking via RTSP

## 🎥 Visão Geral

Este sistema permite fazer tracking de pessoas em tempo real usando streams RTSP de câmeras IP. É ideal para:

- **Monitoramento de segurança** em tempo real
- **Análise de fluxo de pessoas** em espaços públicos
- **Contagem de pessoas** em entradas/saídas
- **Detecção de comportamento** suspeito

## 🚀 Instalação

### 1. Instalar Dependências

```bash
pip install -r requirements.txt
```

### 2. Verificar Instalação

```bash
python test_rtsp_connection.py --local
```

## 📹 Como Usar

### 1. **Teste Básico de Conexão**

Antes de usar o tracking completo, teste a conexão:

```bash
# Testar câmera local (USB)
python test_rtsp_connection.py --local

# Testar câmera IP
python test_rtsp_connection.py --ip 192.168.1.100 --username admin --password password

# Testar URL RTSP direta
python test_rtsp_connection.py --url rtsp://192.168.1.100:554/stream1
```

### 2. **Tracking Completo**

```bash
# Câmera IP básica
python rtsp_tracking.py --ip 192.168.1.100 --username admin --password password

# Com visualização em tempo real
python rtsp_tracking.py --ip 192.168.1.100 --username admin --password password --show-display

# Teste rápido (50 frames)
python rtsp_tracking.py --ip 192.168.1.100 --max-frames 50 --show-display

# Alta performance (pular frames)
python rtsp_tracking.py --ip 192.168.1.100 --frame-skip 3 --confidence 0.7
```

## 🔧 Configurações por Fabricante

### **HIKVISION**
```bash
python rtsp_tracking.py --ip 192.168.1.100 --username admin --password password --stream Streaming/Channels/101
```

### **DAHUA**
```bash
python rtsp_tracking.py --ip 192.168.1.101 --username admin --password password --stream cam/realmonitor?channel=1&subtype=0
```

### **AXIS**
```bash
python rtsp_tracking.py --ip 192.168.1.102 --username root --password password --stream axis-media/media.amp
```

### **FOSCAM**
```bash
python rtsp_tracking.py --ip 192.168.1.103 --username admin --password password --stream videoMain
```

### **Câmera USB Local**
```bash
python rtsp_tracking.py --source 0 --show-display
```

## ⚙️ Parâmetros Avançados

### **Parâmetros de Performance**
- `--frame-skip N`: Processar 1 a cada N frames (padrão: 1)
- `--max-frames N`: Limitar número de frames (0 = ilimitado)
- `--confidence 0.7`: Confiança mínima para detecção (0.0-1.0)

### **Parâmetros de Saída**
- `--output video.avi`: Nome do arquivo de saída
- `--show-display`: Mostrar visualização em tempo real
- `--output ""`: Não salvar vídeo (apenas visualizar)

### **Parâmetros de Rede**
- `--port 554`: Porta RTSP (padrão: 554)
- `--stream path`: Caminho do stream RTSP

## 📊 Saídas do Sistema

### **1. Vídeo Processado**
- Arquivo `.avi` com bounding boxes e IDs
- FPS e informações em tempo real
- Centro de cada pessoa marcado

### **2. Relatório CSV**
- Dados de tracking por frame
- Posição (X, Y) de cada pessoa
- Timestamp e ID único
- Estatísticas de performance

### **3. Console Output**
- Progresso em tempo real
- Estatísticas de FPS
- Número de pessoas detectadas
- Alertas de reconexão

## 🔍 Solução de Problemas

### **Erro de Conexão**
```bash
# 1. Testar conectividade
ping 192.168.1.100

# 2. Testar porta RTSP
telnet 192.168.1.100 554

# 3. Verificar credenciais
python test_rtsp_connection.py --ip 192.168.1.100 --username admin --password password
```

### **Performance Baixa**
```bash
# Aumentar frame skip
python rtsp_tracking.py --ip 192.168.1.100 --frame-skip 5

# Reduzir resolução (se suportado pela câmera)
# Configurar câmera para 720p ou menor

# Aumentar confiança (menos detecções)
python rtsp_tracking.py --ip 192.168.1.100 --confidence 0.8
```

### **Latência Alta**
```bash
# Buffer mínimo
# O sistema já configura automaticamente

# Verificar rede
# Usar cabo Ethernet em vez de WiFi

# Reduzir FPS da câmera
# Configurar câmera para 15 FPS
```

## 🎯 Casos de Uso

### **1. Monitoramento de Entrada**
```bash
# Contar pessoas que entram/saem
python rtsp_tracking.py --ip 192.168.1.100 --show-display --output entrada.avi
```

### **2. Análise de Fluxo**
```bash
# Processar por 5 minutos
python rtsp_tracking.py --ip 192.168.1.100 --max-frames 9000 --frame-skip 2
```

### **3. Detecção de Comportamento**
```bash
# Alta confiança para evitar falsos positivos
python rtsp_tracking.py --ip 192.168.1.100 --confidence 0.8 --show-display
```

### **4. Gravação Contínua**
```bash
# Sem limite de frames
python rtsp_tracking.py --ip 192.168.1.100 --output monitoramento_24h.avi
```

## 📈 Monitoramento de Performance

### **Métricas Importantes**
- **FPS de Processamento**: Deve ser > 15 FPS
- **Latência**: < 500ms para aplicações em tempo real
- **Precisão**: Ajustar `--confidence` conforme necessário
- **Uso de CPU**: Monitorar com `htop` ou `taskmgr`

### **Otimizações**
1. **Reduzir resolução** da câmera
2. **Aumentar frame-skip** para performance
3. **Usar GPU** se disponível (CUDA)
4. **Conexão Ethernet** para baixa latência

## 🔒 Segurança

### **Boas Práticas**
- ✅ Usar credenciais fortes
- ✅ Isolar câmeras em VLAN separada
- ✅ Atualizar firmware das câmeras
- ✅ Usar HTTPS/RTMPS quando possível
- ❌ Não expor câmeras diretamente na internet

### **Configuração de Rede**
```bash
# Exemplo de configuração segura
# VLAN 100: Câmeras IP (192.168.100.0/24)
# VLAN 200: Sistema de tracking (192.168.200.0/24)
# Firewall: Permitir apenas RTSP entre VLANs
```

## 📝 Logs e Debug

### **Habilitar Logs Detalhados**
```bash
# Adicionar ao comando
python rtsp_tracking.py --ip 192.168.1.100 --show-display 2>&1 | tee tracking.log
```

### **Informações Úteis**
- FPS de entrada vs saída
- Número de reconexões
- Erros de detecção
- Performance por frame

## 🆘 Suporte

### **Problemas Comuns**

1. **"Erro ao conectar ao stream RTSP"**
   - Verificar IP, usuário e senha
   - Testar com `test_rtsp_connection.py`

2. **"FPS muito baixo"**
   - Reduzir resolução da câmera
   - Aumentar `--frame-skip`
   - Verificar performance da CPU

3. **"Muitos falsos positivos"**
   - Aumentar `--confidence`
   - Verificar iluminação
   - Ajustar posicionamento da câmera

### **Contato**
Para suporte adicional, verifique:
- Logs de erro no console
- Configuração da câmera
- Documentação do fabricante
- Exemplos em `rtsp_examples.py` 