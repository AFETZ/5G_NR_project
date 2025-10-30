import pandas as pd

from pathlib import Path


def load_metrics_from_parquet(filepath: Path) -> pd.DataFrame:
    """
    Быстрая загрузка метрик из Parquet файла
    """

    return pd.read_parquet(filepath)

def load_metrics_from_csv(filepath: Path) -> pd.DataFrame:
    """
    Быстрая загрузка метрик из CSV файла
    """

    return pd.read_csv(filepath)
