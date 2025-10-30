import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ParseResult, EventType


RAW_TEST_DATA = [
    {"ts_us": 0, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a1", "app": "BSM", "bytes": 250, "rssi_dbm": -65, "sinr_db": 18.2},
    {"ts_us": 200, "event": "rx", "src": "car_33", "dst": "car_12", "pkt_id": "a1", "app": "BSM", "bytes": 250, "rssi_dbm": -67, "sinr_db": 17.5},
    {"ts_us": 1000, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a2", "app": "BSM", "bytes": 250},
    {"ts_us": 2000, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a3", "app": "BSM", "bytes": 250},
    {"ts_us": 2150, "event": "rx", "src": "car_33", "dst": "car_12", "pkt_id": "a3", "app": "BSM", "bytes": 250},
    {"ts_us": 3000, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a4", "app": "BSM", "bytes": 250},
    {"ts_us": 3250, "event": "rx", "src": "car_33", "dst": "car_12", "pkt_id": "a4", "app": "BSM", "bytes": 250},
    {"ts_us": 4000, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a5", "app": "BSM", "bytes": 250},
    {"ts_us": 5000, "event": "tx", "src": "car_12", "dst": "car_33", "pkt_id": "a6", "app": "BSM", "bytes": 250},
    {"ts_us": 5100, "event": "rx", "src": "car_33", "dst": "car_12", "pkt_id": "a6", "app": "BSM", "bytes": 250},
    {"ts_us": 50, "event": "tx", "src": "car_33", "dst": "car_12", "pkt_id": "b1", "app": "BSM", "bytes": 250},
    {"ts_us": 90, "event": "rx", "src": "car_12", "dst": "car_33", "pkt_id": "b1", "app": "BSM", "bytes": 250},
    {"ts_us": 1050, "event": "tx", "src": "car_33", "dst": "car_12", "pkt_id": "b2", "app": "BSM", "bytes": 250},
    {"ts_us": 2050, "event": "tx", "src": "car_33", "dst": "car_12", "pkt_id": "b3", "app": "BSM", "bytes": 250},
    {"ts_us": 2250, "event": "rx", "src": "car_12", "dst": "car_33", "pkt_id": "b3", "app": "BSM", "bytes": 250},
]

def get_test_records():
    """Возвращает тестовые данные в виде объектов ParseResult"""
    return [ParseResult(**data) for data in RAW_TEST_DATA]

EXPECTED_RESULTS = {
    'car_12->car_33': {
        'tx_count': 6,
        'rx_count': 4,
        'pdr': 4/6,
        'latencies': [100, 150, 250, 100],
        'mean_latency': 175,
        'p50_latency': 175,
        'p95_latency': 250,
        'std_latency': 62.914
    },
    'car_33->car_12': {
        'tx_count': 3,
        'rx_count': 2,
        'pdr': 2/3,
        'latencies': [40, 200],
        'mean_latency': 120,
        'p50_latency': 120,
        'p95_latency': 200,
        'std_latency': 113.137
    }
}