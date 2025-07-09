#!/usr/bin/env python3
"""
Comparação de performance entre tracking normal e com detecção de movimento
"""

import time
import psutil
import subprocess
import sys
import os
from datetime import datetime

def get_system_info():
    """Obtém informações do sistema"""
    cpu_count = psutil.cpu_count()
    memory = psutil.virtual_memory()
    return {
        'cpu_count': cpu_count,
        'memory_total': memory.total / (1024**3),  # GB
        'memory_available': memory.available / (1024**3)  # GB
    }

def monitor_performance(duration=30):
    """Monitora performance do sistema durante execução"""
    cpu_usage = []
    memory_usage = []
    start_time = time.time()
    
    while time.time() - start_time < duration:
        cpu_percent = psutil.cpu_percent(interval=1)
        memory_percent = psutil.virtual_memory().percent
        
        cpu_usage.append(cpu_percent)
        memory_usage.append(memory_percent)
        
        print(f"⏳ CPU: {cpu_percent:.1f}% | RAM: {memory_percent:.1f}% | "
              f"Tempo: {time.time() - start_time:.0f}s/{duration}s")
    
    return {
        'cpu_avg': sum(cpu_usage) / len(cpu_usage),
        'cpu_max': max(cpu_usage),
        'memory_avg': sum(memory_usage) / len(memory_usage),
        'memory_max': max(memory_usage),
        'duration': duration
    }

def run_tracking_test(script_name, args, test_name, duration=30):
    """Executa teste de tracking"""
    print(f"\n🧪 TESTE: {test_name}")
    print("=" * 50)
    
    # Informações do sistema
    system_info = get_system_info()
    print(f"💻 Sistema: {system_info['cpu_count']} CPUs, "
          f"{system_info['memory_total']:.1f}GB RAM")
    
    # Comando para executar
    cmd = [sys.executable, script_name] + args
    
    print(f"🚀 Executando: {' '.join(cmd)}")
    print(f"⏱️  Duração do teste: {duration} segundos")
    
    try:
        # Iniciar processo
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        # Monitorar performance
        print("\n📊 Monitorando performance...")
        performance = monitor_performance(duration)
        
        # Parar processo
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
        
        # Obter saída
        stdout, stderr = process.communicate()
        
        return {
            'test_name': test_name,
            'script': script_name,
            'args': args,
            'performance': performance,
            'stdout': stdout,
            'stderr': stderr,
            'return_code': process.returncode
        }
        
    except Exception as e:
        print(f"❌ Erro ao executar teste: {e}")
        return None

def print_comparison_results(results):
    """Imprime resultados da comparação"""
    print("\n" + "=" * 80)
    print("📊 COMPARAÇÃO DE PERFORMANCE")
    print("=" * 80)
    
    for result in results:
        if result is None:
            continue
            
        print(f"\n🎯 {result['test_name']}")
        print("-" * 40)
        print(f"📁 Script: {result['script']}")
        print(f"⚙️  Args: {' '.join(result['args'])}")
        
        perf = result['performance']
        print(f"📈 Performance:")
        print(f"   CPU Médio: {perf['cpu_avg']:.1f}%")
        print(f"   CPU Máximo: {perf['cpu_max']:.1f}%")
        print(f"   RAM Médio: {perf['memory_avg']:.1f}%")
        print(f"   RAM Máximo: {perf['memory_max']:.1f}%")
        print(f"   Duração: {perf['duration']}s")
    
    # Comparação direta
    if len(results) >= 2 and all(r is not None for r in results):
        print(f"\n🔄 COMPARAÇÃO DIRETA")
        print("-" * 40)
        
        perf1 = results[0]['performance']
        perf2 = results[1]['performance']
        
        cpu_diff = perf1['cpu_avg'] - perf2['cpu_avg']
        memory_diff = perf1['memory_avg'] - perf2['memory_avg']
        
        print(f"CPU: {results[0]['test_name']} vs {results[1]['test_name']}")
        print(f"   Diferença: {cpu_diff:+.1f}% ({results[0]['test_name']} {'mais alto' if cpu_diff > 0 else 'mais baixo'})")
        
        print(f"RAM: {results[0]['test_name']} vs {results[1]['test_name']}")
        print(f"   Diferença: {memory_diff:+.1f}% ({results[0]['test_name']} {'mais alto' if memory_diff > 0 else 'mais baixo'})")
        
        # Calcular economia
        if cpu_diff > 0:
            cpu_savings = (cpu_diff / perf1['cpu_avg']) * 100
            print(f"💰 Economia de CPU: {cpu_savings:.1f}%")
        
        if memory_diff > 0:
            memory_savings = (memory_diff / perf1['memory_avg']) * 100
            print(f"💰 Economia de RAM: {memory_savings:.1f}%")

def save_results(results, filename=None):
    """Salva resultados em arquivo"""
    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"performance_comparison_{timestamp}.txt"
    
    with open(filename, 'w', encoding='utf-8') as f:
        f.write("COMPARAÇÃO DE PERFORMANCE - TRACKING\n")
        f.write("=" * 50 + "\n")
        f.write(f"Data: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        for result in results:
            if result is None:
                continue
                
            f.write(f"TESTE: {result['test_name']}\n")
            f.write("-" * 30 + "\n")
            f.write(f"Script: {result['script']}\n")
            f.write(f"Args: {' '.join(result['args'])}\n")
            
            perf = result['performance']
            f.write(f"CPU Médio: {perf['cpu_avg']:.1f}%\n")
            f.write(f"CPU Máximo: {perf['cpu_max']:.1f}%\n")
            f.write(f"RAM Médio: {perf['memory_avg']:.1f}%\n")
            f.write(f"RAM Máximo: {perf['memory_max']:.1f}%\n")
            f.write(f"Duração: {perf['duration']}s\n\n")
    
    print(f"💾 Resultados salvos: {filename}")

def main():
    print("⚡ COMPARADOR DE PERFORMANCE - TRACKING")
    print("=" * 50)
    
    # Configurações dos testes
    camera_id = "camera_1"
    test_duration = 30  # segundos
    
    # Teste 1: Tracking normal
    test1_args = [
        "--camera", camera_id,
        "--max-frames", str(test_duration * 30),  # ~30 FPS
        "--frame-skip", "1",
        "--confidence", "0.5"
    ]
    
    # Teste 2: Tracking com detecção de movimento
    test2_args = [
        "--camera", camera_id,
        "--max-frames", str(test_duration * 30),
        "--motion-threshold", "25",
        "--min-area", "500",
        "--motion-buffer", "3",
        "--idle-buffer", "10",
        "--confidence", "0.5"
    ]
    
    # Executar testes
    results = []
    
    # Teste 1: Tracking normal
    result1 = run_tracking_test(
        "config_tracking.py",
        test1_args,
        "Tracking Normal (Sem Detecção de Movimento)",
        test_duration
    )
    results.append(result1)
    
    # Aguardar um pouco entre testes
    print("\n⏳ Aguardando 5 segundos entre testes...")
    time.sleep(5)
    
    # Teste 2: Tracking com detecção de movimento
    result2 = run_tracking_test(
        "motion_tracking.py",
        test2_args,
        "Tracking Otimizado (Com Detecção de Movimento)",
        test_duration
    )
    results.append(result2)
    
    # Mostrar resultados
    print_comparison_results(results)
    
    # Salvar resultados
    save_results(results)
    
    print(f"\n✅ Comparação concluída!")
    print("📊 Verifique os resultados acima para ver a diferença de performance.")

if __name__ == "__main__":
    main() 