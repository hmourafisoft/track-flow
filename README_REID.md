# Sistema de Re-identificação para Rastreamento de Pessoas

## Visão Geral

Este sistema permite identificar quando uma pessoa sai do quadro e retorna, mantendo o mesmo ID de rastreamento. Isso é especialmente útil para:

- **Análise de comportamento de clientes** em lojas
- **Monitoramento de fluxo de pessoas** em espaços públicos
- **Análise de padrões de movimento** em vídeos de segurança
- **Estudos de comportamento** em ambientes controlados

## Como Funciona

### 1. **Detecção e Rastreamento Inicial**
- Usa YOLOv8 para detectar pessoas em cada frame
- Deep SORT para rastreamento contínuo com IDs únicos
- Armazena características visuais de cada pessoa

### 2. **Detecção de Saída**
- Monitora quando uma pessoa sai do campo de visão
- Armazena características visuais da pessoa que saiu
- Mantém registro por um tempo limitado (configurável)

### 3. **Re-identificação**
- Quando uma nova pessoa aparece, compara características visuais
- Usa múltiplos critérios para determinar se é a mesma pessoa:
  - **Histograma de cores** (roupas, cor da pele)
  - **Proporções corporais** (altura/largura)
  - **Tamanho relativo** (área da bounding box)
  - **Posição** (onde apareceu no frame)

### 4. **Critérios de Decisão**
- **Similaridade mínima**: 0.6 (configurável)
- **Tempo máximo de ausência**: 30 segundos (configurável)
- **Múltiplas características**: Combina diferentes aspectos visuais

## Arquivos do Sistema

### `reid_system.py`
Sistema principal de re-identificação com as seguintes funcionalidades:

```python
class ReIdentificationSystem:
    def __init__(self, max_exit_time=30, similarity_threshold=0.7):
        # max_exit_time: tempo máximo em segundos para considerar re-identificação
        # similarity_threshold: threshold mínimo de similaridade (0-1)
```

**Métodos principais:**
- `extract_appearance_features()`: Extrai características visuais
- `try_reidentify()`: Tenta re-identificar uma pessoa
- `add_exited_person()`: Adiciona pessoa que saiu à lista
- `get_reid_statistics()`: Retorna estatísticas de re-identificação

### `reid_example.py`
Exemplo completo de uso do sistema com:
- Processamento de vídeo
- Visualização em tempo real
- Geração de relatórios CSV
- Estatísticas de re-identificação

## Como Usar

### 1. **Configuração Básica**

```python
from reid_system import ReIdentificationSystem

# Inicializar sistema
reid_system = ReIdentificationSystem(
    max_exit_time=30,        # 30 segundos para re-identificação
    similarity_threshold=0.6  # 60% de similaridade mínima
)
```

### 2. **Processamento de Frame**

```python
# Para cada frame do vídeo
for frame in video_frames:
    # Detectar pessoas
    detections = detect_people(frame)
    
    # Para cada pessoa detectada
    for bbox in detections:
        # Extrair características
        features = reid_system.extract_appearance_features(frame, bbox)
        
        # Tentar re-identificação
        reid_id = reid_system.try_reidentify(features, bbox)
        
        if reid_id:
            print(f"Pessoa {reid_id} retornou!")
```

### 3. **Detecção de Saída**

```python
# Quando uma pessoa sai do quadro
reid_system.add_exited_person(
    track_id=person_id,
    features=person_features,
    bbox=last_bbox
)
```

### 4. **Executar Exemplo Completo**

```bash
python reid_example.py
```

## Parâmetros Configuráveis

### `max_exit_time` (30 segundos padrão)
- Tempo máximo que o sistema mantém registro de uma pessoa que saiu
- Valores maiores = mais chance de re-identificação, mas mais falsos positivos
- Valores menores = menos falsos positivos, mas pode perder re-identificações válidas

### `similarity_threshold` (0.6 padrão)
- Threshold mínimo de similaridade para considerar re-identificação
- 0.0 = aceita qualquer pessoa como re-identificação
- 1.0 = só aceita pessoas idênticas
- **Recomendado**: 0.5-0.7 para equilíbrio entre precisão e recall

## Características Visuais Utilizadas

### 1. **Histograma de Cores (HSV)**
- **Matiz (Hue)**: Cor base (vermelho, azul, verde, etc.)
- **Saturação (Saturation)**: Intensidade da cor
- **Valor (Value)**: Brilho
- **Vantagem**: Robusto a mudanças de iluminação

### 2. **Proporções Corporais**
- Razão altura/largura da bounding box
- Útil para distinguir pessoas de diferentes tamanhos

### 3. **Tamanho Relativo**
- Área da bounding box
- Considera mudanças de perspectiva e distância

### 4. **Posição**
- Localização no frame
- Útil para contextos específicos

## Limitações e Considerações

### **Limitações:**
1. **Pessoas muito similares**: Pode confundir pessoas com roupas similares
2. **Mudanças drásticas**: Mudança de roupa pode afetar a re-identificação
3. **Oclusão prolongada**: Pessoas que ficam muito tempo fora do quadro
4. **Qualidade do vídeo**: Resolução baixa pode afetar a precisão

### **Melhorias Possíveis:**
1. **Características faciais**: Adicionar reconhecimento facial
2. **Padrões de movimento**: Análise de como a pessoa se move
3. **Características temporais**: Histórico de comportamento
4. **Múltiplas câmeras**: Integração com outras câmeras

## Exemplo de Saída

### **Console:**
```
Re-identificação: ID 5 retornou como ID 12
Pessoa 5 adicionada à lista de pessoas que saíram
Re-identificação bem-sucedida: Pessoa 5 retornou (similaridade: 0.723)
```

### **Estatísticas:**
```
Estatísticas de Re-identificação:
total_reid_matches: 3
average_similarity: 0.712
average_exit_duration: 15.3
max_exit_duration: 28
min_exit_duration: 5
```

### **CSV Reports:**
- `tracking_report_with_reid_YYYYMMDD_HHMMSS.csv`: Dados detalhados
- `tracking_summary_with_reid_YYYYMMDD_HHMMSS.csv`: Resumo por pessoa
- `reid_data.pkl`: Dados de re-identificação para análise posterior

## Casos de Uso

### **1. Análise de Comportamento em Lojas**
- Rastrear clientes que visitam diferentes seções
- Medir tempo de permanência em cada área
- Identificar padrões de movimento

### **2. Monitoramento de Segurança**
- Detectar pessoas que saem e retornam
- Análise de comportamento suspeito
- Contagem de pessoas em áreas específicas

### **3. Estudos de Fluxo**
- Análise de tráfego em espaços públicos
- Otimização de layout de ambientes
- Estudos de comportamento humano

## Troubleshooting

### **Problema: Muitas re-identificações falsas**
- **Solução**: Aumentar `similarity_threshold` para 0.7-0.8
- **Solução**: Reduzir `max_exit_time` para 15-20 segundos

### **Problema: Perdendo re-identificações válidas**
- **Solução**: Reduzir `similarity_threshold` para 0.5-0.6
- **Solução**: Aumentar `max_exit_time` para 45-60 segundos

### **Problema: Performance lenta**
- **Solução**: Reduzir número de características extraídas
- **Solução**: Processar frames em resolução menor

## Dependências

```bash
pip install opencv-python numpy ultralytics
```

## Licença

Este projeto é de código aberto e pode ser usado para fins educacionais e comerciais. 