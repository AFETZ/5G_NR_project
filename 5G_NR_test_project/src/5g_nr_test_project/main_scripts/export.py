import os
import sys
import csv
import pandas as pd
import logging

from pathlib import Path
from typing import Dict

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ConnectionMetrics, MetricsResult

logger = logging.getLogger(__name__)


class ComprehensiveMetricsExporter:
    """
    Полнофункциональный экспортер метрик с разделением по группам
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Класс по экспорту данных был инициализирован: {output_dir}")

    def export_metrics(self, metrics_result: MetricsResult, base_filename: str) -> Dict[str, Path]:
        """
        Экспортирует все группы метрик в отдельные файлы
        """

        exported_files = {}

        self._export_overall(metrics_result.overall, base_filename, exported_files)
        self._export_pairs(metrics_result.by_pair, base_filename, exported_files)
        self._export_apps(metrics_result.by_app, base_filename, exported_files)
        self._export_windows(metrics_result.by_window, base_filename, exported_files)
        self._export_summary(metrics_result, base_filename, exported_files)

        logger.info(f"Экспорт данных завершился")
        return exported_files

    def _export_overall(self, overall_metrics: ConnectionMetrics, base_filename: str, exported_files: Dict[str, Path]):
        """
        Экспорт общих метрик
        """

        data = [{
            'tx_count': overall_metrics.pdr_metrics.tx_count,
            'rx_count': overall_metrics.pdr_metrics.rx_count,
            'pdr': overall_metrics.pdr_metrics.pdr,
            'latency_mean': overall_metrics.latency_stats.mean,
            'latency_p50': overall_metrics.latency_stats.p50,
            'latency_p95': overall_metrics.latency_stats.p95,
            'latency_std': overall_metrics.latency_stats.std,
            'latency_count': overall_metrics.latency_stats.count,
            'sinr_avg': overall_metrics.sinr_avg,
            'sinr_count': overall_metrics.sinr_count
        }]

        df = pd.DataFrame(data)
        self._save_dataframe(df, f"{base_filename}_overall", exported_files)

    def _export_pairs(self, pairs_metrics: Dict, base_filename: str, exported_files: Dict[str, Path]):
        """
        Экспорт метрик по парам src-dst
        """

        data = []
        for (src, dst), metrics in pairs_metrics.items():
            data.append({
                'src': src,
                'dst': dst,
                'app': metrics.app or 'N/A',
                'tx_count': metrics.pdr_metrics.tx_count,
                'rx_count': metrics.pdr_metrics.rx_count,
                'pdr': metrics.pdr_metrics.pdr,
                'latency_mean': metrics.latency_stats.mean,
                'latency_p50': metrics.latency_stats.p50,
                'latency_p95': metrics.latency_stats.p95,
                'latency_std': metrics.latency_stats.std,
                'latency_count': metrics.latency_stats.count,
                'sinr_avg': metrics.sinr_avg,
                'sinr_count': metrics.sinr_count
            })

        if data:
            df = pd.DataFrame(data)
            self._save_dataframe(df, f"{base_filename}_pairs", exported_files)

    def _export_apps(self, apps_metrics: Dict, base_filename: str, exported_files: Dict[str, Path]):
        """
        Экспорт метрик по приложениям
        """

        data = []
        for app, metrics in apps_metrics.items():
            data.append({
                'app': app,
                'tx_count': metrics.pdr_metrics.tx_count,
                'rx_count': metrics.pdr_metrics.rx_count,
                'pdr': metrics.pdr_metrics.pdr,
                'latency_mean': metrics.latency_stats.mean,
                'latency_p50': metrics.latency_stats.p50,
                'latency_p95': metrics.latency_stats.p95,
                'latency_std': metrics.latency_stats.std,
                'latency_count': metrics.latency_stats.count,
                'sinr_avg': metrics.sinr_avg,
                'sinr_count': metrics.sinr_count
            })

        if data:
            df = pd.DataFrame(data)
            self._save_dataframe(df, f"{base_filename}_apps", exported_files)

    def _export_windows(self, windows_metrics: Dict, base_filename: str, exported_files: Dict[str, Path]):
        """
        Экспорт метрик по временным окнам
        """

        data = []
        for (window_start, src, dst), metrics in windows_metrics.items():
            data.append({
                'window_start': window_start,
                'src': src,
                'dst': dst,
                'app': metrics.app or 'N/A',
                'tx_count': metrics.pdr_metrics.tx_count,
                'rx_count': metrics.pdr_metrics.rx_count,
                'pdr': metrics.pdr_metrics.pdr,
                'latency_mean': metrics.latency_stats.mean,
                'latency_p50': metrics.latency_stats.p50,
                'latency_p95': metrics.latency_stats.p95,
                'latency_std': metrics.latency_stats.std,
                'latency_count': metrics.latency_stats.count,
                'sinr_avg': metrics.sinr_avg,
                'sinr_count': metrics.sinr_count
            })

        if data:
            df = pd.DataFrame(data)
            self._save_dataframe(df, f"{base_filename}_windows", exported_files)

    def _export_summary(self, metrics_result: MetricsResult, base_filename: str, exported_files: Dict[str, Path]):
        """
        Экспорт сводной статистики и аномалий
        """

        summary_data = [{
            'total_processed': metrics_result.processed_cnt,
            'successfully_matched': metrics_result.success_cnt,
            'success_rate': metrics_result.success_cnt / metrics_result.processed_cnt if metrics_result.processed_cnt > 0 else 0,
            'overall_pdr': metrics_result.overall.pdr_metrics.pdr,
            'overall_tx_count': metrics_result.overall.pdr_metrics.tx_count,
            'overall_rx_count': metrics_result.overall.pdr_metrics.rx_count,
            'overall_sinr_avg': metrics_result.overall.sinr_avg,
            'overall_sinr_count': metrics_result.overall.sinr_count,
            'unique_src_dst_pairs': len(metrics_result.by_pair),
            'unique_apps': len(metrics_result.by_app),
            'time_windows': len(metrics_result.by_window)
        }]

        summary_df = pd.DataFrame(summary_data)
        self._save_dataframe(summary_df, f"{base_filename}_summary", exported_files)

        # Аномалии
        anomalies_data = [{
            'anomaly_type': anomaly_type,
            'count': count
        } for anomaly_type, count in metrics_result.anomalies.items()]

        if anomalies_data:
            anomalies_df = pd.DataFrame(anomalies_data)
            self._save_dataframe(anomalies_df, f"{base_filename}_anomalies", exported_files)

    def _save_dataframe(self, df: pd.DataFrame, name: str, exported_files: Dict[str, Path]):
        """
        Сохраняет DataFrame в CSV и Parquet
        """

        try:
            csv_path = self.output_dir / f"{name}.csv"
            df.to_csv(csv_path, index=False)
            exported_files[f'{name}_csv'] = csv_path

            parquet_path = self.output_dir / f"{name}.parquet"
            df.to_parquet(parquet_path, index=False, engine='pyarrow')
            exported_files[f'{name}_parquet'] = parquet_path

            logger.debug(f"Exported {name}: {len(df)} records")

        except Exception as e:
            logger.error(f"Failed to export {name}: {e}")
            raise


def export_comprehensive(metrics_result: MetricsResult, output_dir: Path, filename: str = "metrics") -> Dict[str, Path]:
    """
    Комплексный экспорт всех метрик
    """

    exporter = ComprehensiveMetricsExporter(output_dir)
    return exporter.export_metrics(metrics_result, filename)
