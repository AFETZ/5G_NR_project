import json
from pathlib import Path
from collections import defaultdict


def analyze_dataset(file_path):
    """
    Анализ сгенерированного датасета
    """
    with open( file_path, 'r', encoding='utf-8' ) as f:
        events = [json.loads( line ) for line in f]

    print( "=== АНАЛИЗ ТЕСТОВОГО ДАТАСЕТА ===" )
    print( f"Всего событий: {len( events )}" )

    # Базовая статистика
    tx_events = [e for e in events if e['event'] == 'tx']
    rx_events = [e for e in events if e['event'] == 'rx']

    print( f"TX событий: {len( tx_events )}" )
    print( f"RX событий: {len( rx_events )}" )

    # Статистика по приложениям
    app_stats = defaultdict( lambda: {'tx': 0, 'rx': 0} )
    for event in events:
        app_stats[event.get( 'app', 'UNKNOWN' )][event['event']] += 1

    print( "\n=== СТАТИСТИКА ПО ПРИЛОЖЕНИЯМ ===" )
    for app, stats in app_stats.items():
        pdr = stats['rx'] / stats['tx'] if stats['tx'] > 0 else 0
        print( f"{app}: TX={stats['tx']}, RX={stats['rx']}, PDR={pdr:.2f}" )

    # Аномалии
    pkt_ids = defaultdict( list )
    for event in events:
        pkt_ids[event['pkt_id']].append( event )

    duplicates = [pid for pid, events_list in pkt_ids.items() if len( events_list ) > 2]
    orphan_rx = [pid for pid, events_list in pkt_ids.items()
                 if len( [e for e in events_list if e['event'] == 'rx'] ) > 0
                 and len( [e for e in events_list if e['event'] == 'tx'] ) == 0]

    print( "\n=== АНОМАЛИИ ===" )
    print( f"Дубликаты pkt_id: {len( duplicates )}" )
    print( f"RX без TX: {len( orphan_rx )}" )

    # Анализ задержек
    latencies = []
    for pkt_id, events_list in pkt_ids.items():
        tx_events = [e for e in events_list if e['event'] == 'tx']
        rx_events = [e for e in events_list if e['event'] == 'rx']

        if tx_events and rx_events:
            tx_time = min( e['ts_us'] for e in tx_events )
            rx_time = min( e['ts_us'] for e in rx_events )
            latency = rx_time - tx_time
            latencies.append( latency )

    if latencies:
        print( f"\n=== ЗАДЕРЖКИ ===" )
        print( f"Минимальная: {min( latencies ) / 1000:.1f} ms" )
        print( f"Максимальная: {max( latencies ) / 1000:.1f} ms" )
        print( f"Средняя: {sum( latencies ) / len( latencies ) / 1000:.1f} ms" )
        print( f"Отрицательные задержки: {len( [l for l in latencies if l < 0] )}" )


if __name__ == "__main__":
    dataset_path = Path( 'tests/large_test_dataset.ndjson' )
    if dataset_path.exists():
        analyze_dataset( dataset_path )
    else:
        print( "Датасет не найден. Сначала запустите large_test_dataset.py" )