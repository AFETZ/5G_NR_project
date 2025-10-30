import os
import sys
import logging

from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Tuple, Optional, DefaultDict

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ParseResult
from configs.models import LatencyStats, PDRMetrics, ConnectionMetrics, MetricsResult, AggregationType
from main_scripts.export import export_comprehensive

logger = logging.getLogger(__name__)


class MetricsCalculator:
    """
    Класс для реализации подсчета метрик
    """

    def __init__(self, window_size: int = 1000000) -> None:
        """
        :param:
            window_size: - размер временного окна для агрегации
        """

        self.window_size = window_size

        self._reset_accums()

        logger.info(f"MetricsCalculator был инициализирован с window_size = {self.window_size}")

    def _reset_accums(self) -> None:
        """
        Обновление предагрегированных данных
        """

        self.tx_records: Dict[str, Dict] = {}
        self.rx_records: DefaultDict[str, List[Dict]] = defaultdict(list)

        self.accumulated_data = {
            'overall': {
                'tx': 0,
                'rx': 0,
                'latency': [],
                'sinr_sum': 0.0,
                'sinr_count': 0
            },
            'by_pair': defaultdict(
                lambda: {'tx': 0, 'rx': 0, 'latency': [], 'sinr_sum': 0.0, 'sinr_count': 0}
            ),
            'by_app': defaultdict(
                lambda: {'tx': 0, 'rx': 0, 'latency': [], 'sinr_sum': 0.0, 'sinr_count': 0}
            ),
            'by_window': defaultdict(
                lambda: {'tx': 0, 'rx': 0, 'latency': [], 'sinr_sum': 0.0, 'sinr_count': 0}
            )
        }

        self.anomalies = {
            'duplicate_tx': 0,
            'rx_without_tx': 0,
            'direction_mismatch': 0,
            'negative_latency': 0,
            'duplicate_rx': 0
        }

        self.processed_cnt = 0
        self.success_cnt = 0

        # logger.debug(f"")

    def process_record(self, record: ParseResult) -> Optional[Dict]:
        """
        Обработка строки подготовленных данных
        :param:
            record: - строка для обработки
        :return:
            Optional[Dict]: - возвращает итоговый статус обработки строки
        """

        self.processed_cnt += 1

        if record.event == 'tx':
            return self._process_tx(record)
        elif record.event == 'rx':
            return self._process_rx(record)
        else:
            logger.error("Неизвестный тип данных в поле 'event'")
            return None

    def _process_tx(self, tx_record: ParseResult) -> Optional[Dict]:
        """
        Обработка строк с данными по tx
        :param:
            tx_record: - строка с tx для обработки
        :return:
            Optional[Dict]: - возвращает итоговый статус обработки строки
        """

        pkt_id = tx_record.pkt_id

        if pkt_id in self.tx_records:
            self.anomalies['duplicate_tx'] += 1
            logger.warning(f"Обнаружен дубликат TX для pkt_id = {pkt_id}")
            return None

        tx_data = {
            'ts_us': tx_record.ts_us,
            'src': tx_record.src,
            'dst': tx_record.dst,
            'pkt_id': tx_record.pkt_id,
            'app': tx_record.app,
            'bytes': tx_record.bytes
        }
        self.tx_records[pkt_id] = tx_data

        self._update_counters(tx_data, is_tx=True)

        if pkt_id in self.rx_records:
            matched_pairs = []
            for rx_data in self.rx_records[pkt_id]:
                matched_pair = self._match_tx_rx(tx_data, rx_data)
                if matched_pair:
                    matched_pairs.append(matched_pair)
                    self.success_cnt += 1

            del self.rx_records[pkt_id]

            return matched_pairs[0] if matched_pairs else None

        return None

    def _process_rx(self, rx_record: ParseResult) -> Optional[Dict]:
        """
        Обработка строк с данными по rx
        :param:
            rx_record: - строка с rx для обработки
        :return:
            Optional[Dict]: - возвращает итоговый статус обработки строки
        """

        rx_data = {
            'ts_us': rx_record.ts_us,
            'src': rx_record.src,
            'dst': rx_record.dst,
            'pkt_id': rx_record.pkt_id,
            'app': rx_record.app,
            'bytes': rx_record.bytes
        }

        pkt_id = rx_record.pkt_id

        if pkt_id in self.tx_records:
            tx_data = self.tx_records[pkt_id]
            matched_pair = self._match_tx_rx(tx_data, rx_data)
            if matched_pair:
                self.success_cnt += 1
                return matched_pair
        else:
            self.rx_records[pkt_id].append(rx_data)
            self.anomalies['rx_without_tx'] += 1
            logger.debug(f"RX без соответствующего TX для pkt_id = {pkt_id}")

        return None

    def _match_tx_rx(self, tx_data: Dict, rx_data: Dict) -> Optional[Dict]:
        """
        Проверка на соответствие строк tx и rx при одном id пакета
        :param:
            tx_data: - данные по tx
            rx_data: - данные по rx
        :return:
            Optional[Dict]: - возвращает итоговый статус обработки
        """

        if tx_data['src'] != rx_data['dst'] or tx_data['dst'] != rx_data['src']:
            self.anomalies['direction_mismatch'] += 1
            logger.warning(
                f"Несоответствие направления для pkt_id {tx_data['pkt_id']}"
                f"TX: {tx_data['src']} -> {tx_data['tx']} "
                f"RX: {rx_data['src']} -> {rx_data['tx']} "
            )
            return None

        latency = rx_data['ts_us'] - tx_data['ts_us']

        if latency < 0:
            self.anomalies['negative_latency'] += 1
            logger.warning(
                f"Отрицательная задержка {latency} для pkt_id {tx_data['pkt_id']} "
                f"TX: {tx_data['ts_us']}, RX: {rx_data['ts_us']}"
            )
            return None

        matched_pair = {
            'pkt_id': tx_data['pkt_id'],
            'src': tx_data['src'],
            'dst': tx_data['dst'],
            'app': tx_data['app'],
            'latency': latency,
            'tx_ts': tx_data['ts_us'],
            'rx_ts': rx_data['ts_us'],
            'bytes': tx_data['bytes'],
            'window_start': (tx_data['ts_us'] // self.window_size) * self.window_size,
            'sinr_db': rx_data.get('sinr_db')
        }

        self._update_counters(rx_data, is_tx=False)
        # self._update_counters_for_matched_rx(tx_data)
        self._update_latencies(matched_pair)
        self._update_sinr_stats(matched_pair)

        logger.debug(f"Сопоставлена пара pkt_id {tx_data['pkt_id']}, задержка: {latency}")
        return matched_pair

    def _update_counters(self, record: Dict, is_tx: bool) -> None:
        """
        Обновление статистики по tx, rx
        :param:
            record: - строка обрабатываемых данных
            is_tx: - флаг, показывающий каким данным нужно обновить статистику
        """

        key = 'tx' if is_tx else 'rx'

        self.accumulated_data['overall'][key] += 1

        pair_key = (record['src'], record['dst'])
        self.accumulated_data['by_pair'][pair_key][key] += 1

        self.accumulated_data['by_app'][record['app']][key] += 1

        window_id = (record['ts_us'] // self.window_size) * self.window_size
        window_key = (window_id, record['src'], record['dst'])
        self.accumulated_data['by_window'][window_key][key] += 1

    # def _update_counters_for_matched_rx(self, tx_data: Dict) -> None:
    #     """
    #
    #     :param tx_data:
    #     :return:
    #     """
    #
    #     self.accumulated_data['overall']['rx'] += 1
    #
    #     pair_key = (tx_data['src'], tx_data['dst'])
    #     self.accumulated_data['by_pair'][pair_key]['rx'] += 1
    #
    #     self.accumulated_data['by_app'][tx_data['app']]['rx'] += 1
    #
    #     window_id = (tx_data['ts_us'] // self.window_size) * self.window_size
    #     window_key = (window_id, tx_data['src'], tx_data['dst'])
    #     self.accumulated_data['by_window'][window_key]['rx'] += 1

    def _update_latencies(self, matched_pair: Dict) -> None:
        """
        Обновление статистики по latency
        :param:
            matched_pair: - соответствующая пара tx и rx
        """

        latency = matched_pair['latency']

        self.accumulated_data['overall']['latency'].append(latency)

        pair_key = (matched_pair['src'], matched_pair['dst'])
        self.accumulated_data['by_pair'][pair_key]['latency'].append(latency)

        self.accumulated_data['by_app'][matched_pair['app']]['latency'].append(latency)

        window_key = (matched_pair['window_start'], matched_pair['src'], matched_pair['dst'])
        self.accumulated_data['by_window'][window_key]['latency'].append(latency)
        self.accumulated_data['by_window'][window_key]['rx'] += 1

    def _update_sinr_stats(self, matched_pair: Dict) -> None:
        """
        Обновление статистики по SINR
        :param:
            matched_pair: - соответствующая пара tx и rx
        """

        sinr_db = matched_pair.get('sinr_db')

        if sinr_db is not None:
            self.accumulated_data['overall']['sinr_sum'] += sinr_db
            self.accumulated_data['overall']['sinr_count'] += 1

            pair_key = (matched_pair['src'], matched_pair['dst'])
            self.accumulated_data['by_pair'][pair_key]['sinr_sum'] += sinr_db
            self.accumulated_data['by_pair'][pair_key]['sinr_count'] += 1

            self.accumulated_data['by_app'][matched_pair['app']]['sinr_sum'] += sinr_db
            self.accumulated_data['by_app'][pair_key]['sinr_count'] += 1

            window_key = (matched_pair['window_start'], matched_pair['src'], matched_pair['dst'])
            self.accumulated_data['by_window'][window_key]['sinr_sum'] += sinr_db
            self.accumulated_data['by_window'][window_key]['sinr_count'] += 1

    def get_curr_stats(self) -> Dict:
        """
        Получение текущей статистики обработки данных
        :return:
            Dict: - словарь с метриками по обработке данных
        """

        return {
            'processed_cnt': self.processed_cnt,
            'sucess_cnt': self.success_cnt,
            'pending_tx': len(self.tx_records),
            'pending_rx': sum(len(rx_list) for rx_list in self.rx_records.values()),
            'anomalies': self.anomalies.copy(),
            'matched': (
                self.success_cnt / self.processed_cnt if self.processed_cnt > 0 else 0.0
            )
        }

    def get_metrics_result(self) -> MetricsResult:
        """
        Подсчет и возвращение итоговых агрегируемых метрик
        :return:
            MetricsResult: - модель данных для итогового набора метрик
        """

        logger.info("Расчет финальных метрик")

        overall_metrics = self._calculate_overall_metrics()
        by_pair_metrics = self._calculate_pairs_metrics()
        by_app_metrics = self._calculate_app_metrics()
        by_window_metrics = self._calculate_window_metrics()

        metrics_result = MetricsResult(
            overall=overall_metrics,
            by_pair=by_pair_metrics,
            by_app=by_app_metrics,
            by_window=by_window_metrics,
            anomalies=self.anomalies.copy(),
            processed_cnt=self.processed_cnt,
            success_cnt=self.success_cnt
        )

        logger.info("Расчет итоговых метрик закончен")
        return metrics_result

    def _calculate_overall_metrics(self) -> ConnectionMetrics:
        """
        Подсчет метрик по всему датасету
        :return:
            ConnectionMetrics: - Модель данных по статистике для определенной группе
        """

        overall_data = self.accumulated_data['overall']

        pdr_metrics = PDRMetrics.create(
            tx_count=overall_data['tx'],
            rx_count=overall_data['rx']
        )

        latency_stats = LatencyStats.create(overall_data['latency'])

        sinr_avg = overall_data['sinr_sum'] / overall_data['sinr_count'] if overall_data['sinr_count'] > 0 else None

        return ConnectionMetrics(
            src="OVERALL",
            dst="OVERALL",
            pdr_metrics=pdr_metrics,
            latency_stats=latency_stats,
            sinr_avg=sinr_avg,
            sinr_count=overall_data['sinr_count']
        )

    def _calculate_pairs_metrics(self) -> Dict[Tuple[str, str], ConnectionMetrics]:
        """

        :return:
        """

        by_pair_metrics = {}

        for pair_key, data in self.accumulated_data['by_pair'].items():
            src, dst = pair_key

            if data['tx'] == 0 and data['rx'] == 0:
                continue

            pdr_metrics = PDRMetrics.create(
                tx_count=data['tx'],
                rx_count=data['rx']
            )

            latency_stats = LatencyStats.create(data['latency'])

            sinr_avg = data['sinr_sum'] / data['sinr_count'] if data['sinr_count'] > 0 else None

            by_pair_metrics[pair_key] = ConnectionMetrics(
                src=src,
                dst=dst,
                pdr_metrics=pdr_metrics,
                latency_stats=latency_stats,
                sinr_avg=sinr_avg,
                sinr_count=data['sinr_count']
            )

        return by_pair_metrics

    def _calculate_app_metrics(self) -> Dict[str, ConnectionMetrics]:
        """

        :return:
        """

        by_app_metrics = {}

        for app, data in self.accumulated_data['by_app'].items():

            if data['tx'] == 0 and data['rx'] == 0:
                continue

            pdr_metrics = PDRMetrics.create(
                tx_count=data['tx'],
                rx_count=data['rx']
            )

            latency_stats = LatencyStats.create(data['latency'])

            sinr_avg = data['sinr_sum'] / data['sinr_count'] if data['sinr_count'] > 0 else None

            by_app_metrics[app] = ConnectionMetrics(
                src="APP",
                dst=app,
                app=app,
                pdr_metrics=pdr_metrics,
                latency_stats=latency_stats,
                sinr_avg=sinr_avg,
                sinr_count=data['sinr_count']
            )

        return by_app_metrics

    def _calculate_window_metrics(self) -> Dict[Tuple[int, str, str], ConnectionMetrics]:
        """

        :return:
        """

        by_window_metrics = {}

        for window_key, data in self.accumulated_data['by_window'].items():
            window_start, src, dst = window_key

            if data['tx'] == 0 and data['rx'] == 0:
                continue

            pdr_metrics = PDRMetrics.create(
                tx_count=data['tx'],
                rx_count=data['rx']
            )

            latency_stats = LatencyStats.create(data['latency'])

            sinr_avg = data['sinr_sum'] / data['sinr_count'] if data['sinr_count'] > 0 else None

            by_window_metrics[window_key] = ConnectionMetrics(
                src=src,
                dst=dst,
                pdr_metrics=pdr_metrics,
                latency_stats=latency_stats,
                window_start=window_start,
                sinr_avg=sinr_avg,
                sinr_count=data['sinr_count']
            )

        return by_window_metrics

    def export_to_dict(self) -> Dict:
        """

        :return:
        """

        metrics_result = self.get_metrics_result()
        return metrics_result.dict()

    def get_summary(self) -> Dict:
        """

        :return:
        """

        metrics_result = self.get_metrics_result()

        return {
            'overall_pdr': metrics_result.overall.pdr_metrics.pdr,
            'overall_latency_mean': metrics_result.overall.latency_stats.mean,
            'unique_pairs': len(metrics_result.by_pair),
            'unique_apps': len(metrics_result.by_app),
            'time_windows': len(metrics_result.by_window)
        }

    def export_comprehensive(self, output_dir: Path, filename: str = "metrics") -> Dict[str, Path]:
        """
        Комплексный экспорт всех метрик
        """

        return export_comprehensive(self.get_metrics_result(), output_dir, filename)
