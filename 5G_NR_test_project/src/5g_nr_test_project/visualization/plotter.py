import pandas as pd
import numpy as np
import logging
import matplotlib.pyplot as plt

from pathlib import Path

logger = logging.getLogger(__name__)


class Plotter:
    """
    Класс для создания и сохранения графиков по значениям метрик
    """

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Класс граффиков инициализирован. Графики будут сохраняться в: {output_dir}")

    def create_all_plots(self, metrics_dir: Path, pair: str = None) -> bool:
        """
        Создает все три графика из задания
        :param:
            metrics_dir: - путь к директории с данными метрик
            pair: - пара src и dst для фильтрации значений
        """

        try:
            df_pairs, df_windows = self._load_data(metrics_dir)

            self._create_pdr_plot( df_windows, pair )
            self._create_latency_cdf( df_pairs, pair )
            self._create_latency_sinr_plot( df_pairs )

            logger.info("Все графики успешно созданы")
            return True

        except Exception as e:
            logger.error(f"Ошибка при создании графиков: {e}")
            return False

    def _load_data(self, metrics_dir: Path) -> None:
        """
        Функция загружает данные из parquet файлов
        :param:
            metrics_dir: - путь к директории с данными метрик
        """

        try:
            metrics_path = Path(metrics_dir)

            pairs_file = metrics_path / "metrics_pairs.parquet"
            df_pairs = pd.read_parquet(pairs_file)

            windows_file = metrics_path / "metrics_windows.parquet"
            df_windows = pd.read_parquet(windows_file)

            logger.info(f"Загружено {len(df_pairs)} пар и {len(df_windows)} временных окон")
            return df_pairs, df_windows

        except Exception as e:
            logger.error(f"Ошибка при загрузке данных для графика: {e}")
            return None, None

    def _create_pdr_plot(self, df_windows: pd.DataFrame, pair: str = None) -> None:
        """
        Функция создает график PDR по временным окнам
        :param:
            df_windows: - датафрейм с данными для графика
            pair: - пары значений для фильтрации
        """

        try:
            plt.figure(figsize=(10, 6))

            if pair:
                src, dst = pair.split(',')
                data = df_windows[(df_windows['src'] == src) & (df_windows['dst'] == dst)]
                title = f'PDR по времени ({src} -> {dst})'
            else:
                first_pair = df_windows.iloc[0]
                src, dst = first_pair['src'], first_pair['dst']
                data = df_windows[(df_windows['src'] == src) & (df_windows['dst'] == dst)]
                title = f'PDR по времени ({src} -> {dst})'

            if not data.empty:
                plt.plot(data['window_start'], data['pdr'], 'b-o', linewidth=2, markersize=4)
                plt.xlabel('Время (мкс)')
                plt.ylabel('PDR')
                plt.title(title)
                plt.grid(True, alpha=0.3)
                plt.tight_layout()

                filename = f"pdr_{src}_{dst}.png" if pair else "pdr_over_time.png"
                plt.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
                plt.close()
                logger.info(f"Создан график PDR: {filename}")
            else:
                logger.warning("Нет данных для графика PDR")

        except Exception as e:
            logger.error(f"Ошибка создания графика PDF: {e}")
            plt.close()

    def _create_latency_cdf(self, df_pairs: pd.DataFrame, pair: str = None) -> None:
        """
        Функция создает CDF график задержки
        :param:
            df_pairs: - датафрейм с данными для построения графиков
            pair: - пары значений для фильтрации
        """

        try:
            plt.figure(figsize=(10, 6))

            if pair:
                src, dst = pair.split(',')
                data = df_pairs[(df_pairs['src'] == src) & (df_pairs['dst'] == dst)]
                title = f'CDF задержки ({src} -> {dst})'
            else:
                data = df_pairs
                title = 'CDF задержки (все пары)'

            if not data.empty and 'latency_mean' in data.columns:
                latencies = data['latency_mean'].dropna()

                if len(latencies) > 0:
                    sorted_latencies = np.sort(latencies)

                    cdf = np.arange(1, len(sorted_latencies) + 1) / len(sorted_latencies)

                    plt.plot(sorted_latencies, cdf, 'r-', linewidth=2)
                    plt.xlabel('Задержка (мкс)')
                    plt.ylabel('Вероятность')
                    plt.title(title)
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()

                    filename = f"cdf_{src}_{dst}.png" if pair else "latency_cdf.png"
                    plt.savefig(self.output_dir / filename, dpi=150, bbox_inches='tight')
                    plt.close()
                    logger.info(f"Создан CDF график: {filename}")
                    return

            logger.warning("Нет данных для CDF графика")
            plt.close()

        except Exception as e:
            logger.error(f"Ошибка при создания графика CDF: {e}")
            plt.close()

    def _create_latency_sinr_plot(self, df_pairs: pd.DataFrame) -> None:
        """
        Функция создает график зависимости задержки от SINR
        """

        try:
            plt.figure(figsize=(10, 6))

            if 'sinr_avg' in df_pairs.columns and not df_pairs.empty:
                valid_data = df_pairs.dropna(subset=['sinr_avg', 'latency_mean'])

                if not valid_data.empty:
                    plt.scatter(valid_data['sinr_avg'], valid_data['latency_mean'], alpha=0.6)
                    plt.xlabel('SINR (dB)')
                    plt.ylabel('Задержка (мкс)')
                    plt.title('Задержка vs SINR')
                    plt.grid(True, alpha=0.3)
                    plt.tight_layout()

                    plt.savefig(self.output_dir / "latency_vs_sinr.png", dpi=150, bbox_inches='tight')
                    plt.close()
                    logger.info("Создан график Latency vs SINR")
                    return

            plt.text(0.5, 0.5, 'Данные SINR не найдены',
                      ha='center', va='center', transform=plt.gca().transAxes)
            plt.title('Задержка vs SINR (данные отсутствуют)')
            plt.tight_layout()
            plt.savefig(self.output_dir / "latency_vs_sinr.png", dpi=150, bbox_inches='tight')
            plt.close()
            logger.info("Создан график-заглушка Latency vs SINR")

        except Exception as e:
            logger.error(f"Ошибка создания графика Latency vs SINR: {e}")
            plt.close()
