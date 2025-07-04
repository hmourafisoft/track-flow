import pandas as pd
import numpy as np
from collections import defaultdict

def analyze_reid_csv(csv_file):
    """Analisa o arquivo CSV para identificar re-entradas"""
    
    # Ler o arquivo CSV
    df = pd.read_csv(csv_file)
    
    print(f"=== ANÁLISE DE RE-ENTRADAS ===")
    print(f"Arquivo: {csv_file}")
    print(f"Total de linhas: {len(df)}")
    print(f"Total de IDs únicos: {df['Track_ID'].nunique()}")
    print()
    
    # Agrupar por Track_ID e ordenar por Frame
    df_sorted = df.sort_values(['Track_ID', 'Frame'])
    
    # Encontrar re-entradas
    reid_events = []
    track_intervals = defaultdict(list)
    
    for track_id in df_sorted['Track_ID'].unique():
        track_data = df_sorted[df_sorted['Track_ID'] == track_id]
        
        if len(track_data) > 1:
            # Verificar se há gaps nos frames
            frames = track_data['Frame'].values
            for i in range(len(frames) - 1):
                gap = frames[i+1] - frames[i]
                if gap > 5:  # Gap maior que 5 frames indica possível saída
                    reid_events.append({
                        'track_id': track_id,
                        'exit_frame': frames[i],
                        'reentry_frame': frames[i+1],
                        'gap_frames': gap,
                        'exit_timestamp': track_data.iloc[i]['Timestamp'],
                        'reentry_timestamp': track_data.iloc[i+1]['Timestamp']
                    })
        
        # Armazenar intervalo de frames para cada track
        track_intervals[track_id] = {
            'first_frame': track_data['Frame'].min(),
            'last_frame': track_data['Frame'].max(),
            'total_frames': len(track_data)
        }
    
    # Mostrar re-entradas encontradas
    print(f"=== RE-ENTRADAS ENCONTRADAS: {len(reid_events)} ===")
    if reid_events:
        for i, event in enumerate(reid_events[:20]):  # Mostrar apenas as primeiras 20
            print(f"{i+1}. ID {event['track_id']}: Saiu no frame {event['exit_frame']}, "
                  f"retornou no frame {event['reentry_frame']} (gap: {event['gap_frames']} frames)")
        
        if len(reid_events) > 20:
            print(f"... e mais {len(reid_events) - 20} re-entradas")
    else:
        print("Nenhuma re-entrada encontrada no CSV!")
    
    print()
    
    # Estatísticas dos tracks
    print("=== ESTATÍSTICAS DOS TRACKS ===")
    track_stats = []
    for track_id, interval in track_intervals.items():
        track_stats.append({
            'track_id': track_id,
            'first_frame': interval['first_frame'],
            'last_frame': interval['last_frame'],
            'total_frames': interval['total_frames'],
            'duration': interval['last_frame'] - interval['first_frame'] + 1
        })
    
    track_stats.sort(key=lambda x: x['track_id'])
    
    # Mostrar alguns tracks com mais frames
    print("Top 10 tracks com mais frames:")
    track_stats_sorted = sorted(track_stats, key=lambda x: x['total_frames'], reverse=True)
    for i, track in enumerate(track_stats_sorted[:10]):
        print(f"{i+1}. ID {track['track_id']}: {track['total_frames']} frames "
              f"(frames {track['first_frame']}-{track['last_frame']})")
    
    print()
    
    # Verificar se há IDs que aparecem em intervalos muito separados
    print("=== POSSÍVEIS RE-ENTRADAS POR INTERVALO ===")
    potential_reids = []
    
    for track_id in df_sorted['Track_ID'].unique():
        track_data = df_sorted[df_sorted['Track_ID'] == track_id]
        frames = track_data['Frame'].values
        
        if len(frames) > 1:
            # Verificar se há grandes gaps
            for i in range(len(frames) - 1):
                gap = frames[i+1] - frames[i]
                if gap > 10:  # Gap maior que 10 frames
                    potential_reids.append({
                        'track_id': track_id,
                        'gap': gap,
                        'exit_frame': frames[i],
                        'reentry_frame': frames[i+1]
                    })
    
    potential_reids.sort(key=lambda x: x['gap'], reverse=True)
    
    print(f"Tracks com gaps grandes (>10 frames): {len(potential_reids)}")
    for i, reid in enumerate(potential_reids[:10]):
        print(f"{i+1}. ID {reid['track_id']}: Gap de {reid['gap']} frames "
              f"(frame {reid['exit_frame']} → {reid['reentry_frame']})")
    
    return reid_events, track_stats

if __name__ == "__main__":
    csv_file = "final_reid_report_20250703_213209.csv"
    analyze_reid_csv(csv_file) 