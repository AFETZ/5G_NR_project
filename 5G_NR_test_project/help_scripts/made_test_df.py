import json
import random
from datetime import datetime
from pathlib import Path


def generate_large_test_dataset():
    """
    Генератор большого тестового датасета с аномалиями
    """
    events = []
    base_time = 1000000  # 1 секунда в микросекундах
    pkt_counter = 0

    # Определяем пары автомобилей и приложения
    pairs = [
        ('car_12', 'car_33', 'BSM'),
        ('car_33', 'car_12', 'BSM'),
        ('car_15', 'car_28', 'CAM'),
        ('car_28', 'car_15', 'CAM'),
        ('car_12', 'car_45', 'DENM'),
        ('car_45', 'car_12', 'DENM')
    ]

    # Нормальные пакеты (70% данных)
    for i in range( 105 ):  # 70% от 150
        src, dst, app = random.choice( pairs )
        pkt_id = f"normal_{pkt_counter}"
        tx_time = base_time + i * 50000  # +50ms каждый пакет

        # TX событие
        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": src,
            "dst": dst,
            "pkt_id": pkt_id,
            "app": app,
            "bytes": random.randint( 200, 300 ),
            "rssi_dbm": round( random.uniform( -85, -65 ), 1 ),
            "sinr_db": round( random.uniform( 10, 25 ), 1 )
        } )

        # 80% пакетов имеют RX (с нормальной задержкой)
        if random.random() < 0.8:
            rx_time = tx_time + random.randint( 50000, 300000 )  # задержка 50-300ms
            events.append( {
                "ts_us": rx_time,
                "event": "rx",
                "src": dst,  # направление меняется
                "dst": src,
                "pkt_id": pkt_id,
                "app": app,
                "bytes": random.randint( 200, 300 ),
                "rssi_dbm": round( random.uniform( -90, -70 ), 1 ),
                "sinr_db": round( random.uniform( 8, 22 ), 1 )
            } )

        pkt_counter += 1

    # АНОМАЛИИ (30% данных)

    # 1. Дубликаты pkt_id (5 случаев)
    for i in range( 5 ):
        tx_time = base_time + 5000000 + i * 100000
        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": "car_12",
            "dst": "car_33",
            "pkt_id": "duplicate_1",  # одинаковый ID
            "app": "BSM",
            "bytes": 250,
            "rssi_dbm": -75.0,
            "sinr_db": 15.0
        } )

    # 2. RX без соответствующего TX (5 случаев)
    for i in range( 5 ):
        rx_time = base_time + 6000000 + i * 100000
        events.append( {
            "ts_us": rx_time,
            "event": "rx",
            "src": "car_99",  # несуществующий источник
            "dst": "car_12",
            "pkt_id": f"orphan_{i}",
            "app": "BSM",
            "bytes": 250,
            "rssi_dbm": -80.0,
            "sinr_db": 12.0
        } )

    # 3. Отрицательные задержки (3 случая)
    for i in range( 3 ):
        rx_time = base_time + 7000000 + i * 100000
        tx_time = rx_time + 100000  # TX позже RX!

        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": "car_12",
            "dst": "car_33",
            "pkt_id": f"negative_latency_{i}",
            "app": "BSM",
            "bytes": 250,
            "rssi_dbm": -70.0,
            "sinr_db": 18.0
        } )

        events.append( {
            "ts_us": rx_time,  # RX раньше TX
            "event": "rx",
            "src": "car_33",
            "dst": "car_12",
            "pkt_id": f"negative_latency_{i}",
            "app": "BSM",
            "bytes": 250,
            "rssi_dbm": -72.0,
            "sinr_db": 16.0
        } )

    # 4. Большие задержки (5 случаев)
    for i in range( 5 ):
        tx_time = base_time + 8000000 + i * 100000
        rx_time = tx_time + 1000000  # задержка 1 секунда

        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": "car_15",
            "dst": "car_28",
            "pkt_id": f"high_latency_{i}",
            "app": "CAM",
            "bytes": 250,
            "rssi_dbm": -85.0,
            "sinr_db": 8.0  # низкий SINR для больших задержек
        } )

        events.append( {
            "ts_us": rx_time,
            "event": "rx",
            "src": "car_28",
            "dst": "car_15",
            "pkt_id": f"high_latency_{i}",
            "app": "CAM",
            "bytes": 250,
            "rssi_dbm": -88.0,
            "sinr_db": 6.0
        } )

    # 5. Пакеты с отсутствующими RSSI/SINR (7 случаев)
    for i in range( 7 ):
        tx_time = base_time + 9000000 + i * 100000
        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": "car_45",
            "dst": "car_12",
            "pkt_id": f"no_signal_{i}",
            "app": "DENM",
            "bytes": 250
            # Отсутствуют rssi_dbm и sinr_db
        } )

    # 6. Рассинхрон по времени (разные приложения для TX/RX)
    for i in range( 3 ):
        tx_time = base_time + 10000000 + i * 100000
        rx_time = tx_time + 150000

        events.append( {
            "ts_us": tx_time,
            "event": "tx",
            "src": "car_12",
            "dst": "car_33",
            "pkt_id": f"app_mismatch_{i}",
            "app": "BSM",  # TX - BSM
            "bytes": 250,
            "rssi_dbm": -75.0,
            "sinr_db": 15.0
        } )

        events.append( {
            "ts_us": rx_time,
            "event": "rx",
            "src": "car_33",
            "dst": "car_12",
            "pkt_id": f"app_mismatch_{i}",
            "app": "CAM",  # RX - CAM (несоответствие!)
            "bytes": 250,
            "rssi_dbm": -77.0,
            "sinr_db": 13.0
        } )

    # Сортируем события по времени
    events.sort( key=lambda x: x['ts_us'] )

    return events


def save_dataset(events, filename=None):
    """
    Сохранение датасета в файл
    """
    if filename is None:
        timestamp = datetime.now().strftime( '%Y%m%d_%H%M%S' )
        filename = f"large_test_dataset_{timestamp}.ndjson"

    output_path = Path( 'tests' ) / filename

    with open( output_path, 'w', encoding='utf-8' ) as f:
        for event in events:
            f.write( json.dumps( event ) + '\n' )

    print( f"Датасет сохранен: {output_path}" )
    print( f"Всего событий: {len( events )}" )

    # Статистика
    tx_count = sum( 1 for e in events if e['event'] == 'tx' )
    rx_count = sum( 1 for e in events if e['event'] == 'rx' )
    print( f"TX: {tx_count}, RX: {rx_count}" )

    return output_path


if __name__ == "__main__":
    # Генерация и сохранение датасета
    events = generate_large_test_dataset()
    save_dataset( events, "large_test_dataset.ndjson" )