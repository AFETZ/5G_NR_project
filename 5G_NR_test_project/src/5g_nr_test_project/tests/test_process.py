import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from main_scripts.processor import MetricsCalculator
from configs.models import ParseResult

# Пример работы с калькулятором (пока без расчета финальных метрик)
# test_directional_metrics.py
calculator = MetricsCalculator()

# Более сложный пример с двумя направлениями
records = [
    # Направление car_12 -> car_33
    ParseResult( ts_us=0, event="tx", src="car_12", dst="car_33", pkt_id="a1", app="BSM", bytes=250 ),
    ParseResult( ts_us=200, event="rx", src="car_33", dst="car_12", pkt_id="a1", app="BSM", bytes=250 ),

    # Направление car_33 -> car_12 (другой пакет!)
    ParseResult( ts_us=1000, event="tx", src="car_33", dst="car_12", pkt_id="b1", app="BSM", bytes=250 ),
    ParseResult( ts_us=1200, event="rx", src="car_12", dst="car_33", pkt_id="b1", app="BSM", bytes=250 ),

    # Еще один пакет в направлении car_12 -> car_33
    ParseResult( ts_us=2000, event="tx", src="car_12", dst="car_33", pkt_id="a2", app="BSM", bytes=250 ),
    # Этот пакет потерян (нет RX)
]

print( "🧪 ТЕСТ НАПРАВЛЕННОСТИ КОММУНИКАЦИЙ" )
print( "=" * 50 )

for i, record in enumerate( records ):
    matched_pair = calculator.process_record( record )
    print( f"Запись {i + 1}: {record.event} {record.src}->{record.dst} (pkt_id: {record.pkt_id})" )
    if matched_pair:
        print( f"  ✅ Сопоставлена: {matched_pair['src']}->{matched_pair['dst']} latency={matched_pair['latency']}мкс" )

print( "\n📊 АККУМУЛЯТОРЫ ПОСЛЕ ОБРАБОТКИ:" )
print(
    f"Overall - TX: {calculator.accumulated_data['overall']['tx']}, RX: {calculator.accumulated_data['overall']['rx']}" )

print( "\n🔍 ДЕТАЛИ ПО ПАРАМ:" )
for pair_key, data in calculator.accumulated_data['by_pair'].items():
    src, dst = pair_key
    print( f"Pair {src}->{dst}: TX={data['tx']}, RX={data['rx']}, Latencies={data['latency']}" )

print( "\n📱 ДЕТАЛИ ПО ПРИЛОЖЕНИЯМ:" )
for app, data in calculator.accumulated_data['by_app'].items():
    print( f"App {app}: TX={data['tx']}, RX={data['rx']}, Latencies={len( data['latency'] )}" )

# Расчет финальных метрик
metrics_result = calculator.get_metrics_result()

print( "\n🎯 ФИНАЛЬНЫЕ МЕТРИКИ:" )
for pair_key, metrics in metrics_result.by_pair.items():
    src, dst = pair_key
    print( f"Направление {src}->{dst}:" )
    print(
        f"  PDR: {metrics.pdr_metrics.pdr:.4f} ({metrics.pdr_metrics.tx_count} TX, {metrics.pdr_metrics.rx_count} RX)" )
    print( f"  Задержка: {metrics.latency_stats.mean:.2f}±{metrics.latency_stats.std:.2f} мкс" )
