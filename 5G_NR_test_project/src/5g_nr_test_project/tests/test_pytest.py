import pytest
import math
import os
import sys

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from main_scripts.processor import MetricsCalculator
from tests.test_data import get_test_records, EXPECTED_RESULTS


class TestMetricsCalculations:

    def setup_method(self):
        self.calculator = MetricsCalculator(window_size=1000000)
        self.test_records = get_test_records()

        for record in self.test_records:
            self.calculator.process_record(record)

        self.metrics_result = self.calculator.get_metrics_result()

    def test_car12_to_car33_pdr(self):
        """Тест PDR для car_12 -> car_33"""
        pair_key = ('car_12', 'car_33')
        pair_metrics = self.metrics_result.by_pair[pair_key]
        expected = EXPECTED_RESULTS['car_12->car_33']

        assert pair_metrics.pdr_metrics.tx_count == expected['tx_count']
        assert pair_metrics.pdr_metrics.rx_count == expected['rx_count']
        assert math.isclose( pair_metrics.pdr_metrics.pdr, expected['pdr'], abs_tol=1e-5 )

    def test_car12_to_car33_latency(self):
        """Тест latency для car_12 -> car_33"""
        pair_key = ('car_12', 'car_33')
        pair_metrics = self.metrics_result.by_pair[pair_key]
        expected = EXPECTED_RESULTS['car_12->car_33']

        latency_stats = pair_metrics.latency_stats
        assert math.isclose( latency_stats.mean, expected['mean_latency'], abs_tol=1e-5 )
        assert math.isclose( latency_stats.p50, expected['p50_latency'], abs_tol=1e-5 )
        assert math.isclose( latency_stats.p95, expected['p95_latency'], abs_tol=1e-5 )
        assert math.isclose( latency_stats.std, expected['std_latency'], abs_tol=1e-3 )

    def test_car33_to_car12_pdr(self):
        """Тест PDR для car_33 -> car_12"""
        pair_key = ('car_33', 'car_12')
        pair_metrics = self.metrics_result.by_pair[pair_key]
        expected = EXPECTED_RESULTS['car_33->car_12']

        assert pair_metrics.pdr_metrics.tx_count == expected['tx_count']
        assert pair_metrics.pdr_metrics.rx_count == expected['rx_count']
        assert math.isclose( pair_metrics.pdr_metrics.pdr, expected['pdr'], abs_tol=1e-5 )

    def test_car33_to_car12_latency(self):
        """Тест latency для car_33 -> car_12"""
        pair_key = ('car_33', 'car_12')
        pair_metrics = self.metrics_result.by_pair[pair_key]
        expected = EXPECTED_RESULTS['car_33->car_12']

        latency_stats = pair_metrics.latency_stats
        assert math.isclose(latency_stats.mean, expected['mean_latency'], abs_tol=1e-5)
        assert math.isclose(latency_stats.p50, expected['p50_latency'], abs_tol=1e-5)
        assert math.isclose(latency_stats.p95, expected['p95_latency'], abs_tol=1e-5)
        assert math.isclose(latency_stats.std, expected['std_latency'], abs_tol=1e-3)

    def test_overall_metrics(self):
        """Тест общих метрик"""
        overall = self.metrics_result.overall

        expected_total_tx = 9
        expected_total_rx = 6
        expected_overall_pdr = 6 / 9

        assert overall.pdr_metrics.tx_count == expected_total_tx
        assert overall.pdr_metrics.rx_count == expected_total_rx
        assert math.isclose(overall.pdr_metrics.pdr, expected_overall_pdr, abs_tol=1e-5)

    def test_anomalies_detection(self):
        """Тест обнаружения аномалий"""
        anomalies = self.metrics_result.anomalies

        assert anomalies['rx_without_tx'] >= 0

    def test_processed_count(self):
        """Тест счетчиков обработки"""
        stats = self.calculator.get_curr_stats()

        assert stats['processed_cnt'] == 15
        assert stats['sucess_cnt'] == 6


def test_latency_stats_calculation():
    """Тест расчета статистик latency отдельно"""
    from configs.models import LatencyStats

    latencies = [100, 150, 250, 100]
    stats = LatencyStats.create( latencies )

    expected_mean = 150.0
    expected_p50 = 125.0
    expected_p95 = 250.0

    assert math.isclose(stats.mean, expected_mean, abs_tol=1e-5)
    assert math.isclose(stats.p50, expected_p50, abs_tol=1e-5)
    assert math.isclose(stats.p95, expected_p95, abs_tol=1e-5)