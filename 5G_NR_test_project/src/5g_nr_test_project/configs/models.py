import statistics
import numpy as np

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional, Dict, List, Tuple
from enum import Enum


class EventType(str, Enum):
    """
    Допустимые дискретные значения для поля 'event'
    """

    tx = 'tx'
    rx = 'rx'


class ParseResult(BaseModel):
    """
    Стандартизированная модель данных для всех источников данных
    """

    model_config = ConfigDict(
        frozen=True,
        use_enum_values=True,
        extra='forbid'
    )

    ts_us: int = Field(..., gt=-1)
    event: EventType = Field(...)
    src: str = Field(..., min_length=1)
    dst: str = Field(..., min_length=1)
    pkt_id: str = Field(..., min_length=1)
    app: str = Field(..., min_length=1)
    bytes: int = Field(...)
    rssi_dbm: Optional[float] = Field(None, ge=-120, le=0)
    sinr_db: Optional[float] = Field(None)
    drop_reason: Optional[str] = Field(None)


    # @field_validator('event')
    # @classmethod
    # def event_validator(cls, v):
    #     if v not in ['tx', 'rx']:
    #         raise ValueError('Event must be tx or rx.')
    #     return v


    @field_validator('rssi_dbm')
    @classmethod
    def rssi_validator(cls, v):
        if v is not None:
            if v > 0:
                raise ValueError('rssi_dbm must be < 0')
        return v


class AggregationType(str, Enum):
    """
    Разрешенные типы агрегации метрик
    """

    OVERALL = "overall"
    BY_PAIR = "by_pair"
    BY_APP = "by_app"
    BY_WINDOW = "by_window"


class LatencyStats(BaseModel):
    """
    Модель данных для статистик по latency
    """

    mean: float
    p50: float
    p95: float
    std: float
    count: int

    @classmethod
    def create(cls, latencies: List[float]):
        """
        Подсчет итоговых статистик по latency
        :param:
            latencies: - список значений для подсчета агрегатов
        :return:
            LatencyStats - возвращает модель данных по метрикам latency
        """

        if not latencies:
            return cls(mean=0.0, p50=0.0, p95=0.0, std=0.0, count=0)

        sorted_latencies = sorted(latencies)
        n = len(sorted_latencies)

        return cls(
            mean=statistics.mean(sorted_latencies),
            p50=np.percentile(sorted_latencies, 50),
            p95=np.percentile(sorted_latencies, 95),
            std=statistics.stdev(sorted_latencies) if n > 1 else 0.0,
            count=n
        )


class PDRMetrics(BaseModel):
    """
    Модель данных для статистики по PDR
    """

    tx_count: int
    rx_count: int
    pdr: float

    @classmethod
    def create(cls, tx_count: int, rx_count: int):
        """
        Производит расчет PDR метрик из счетчиков по tx и rx
        :param:
            tx_count: - счетчик по tx
            rx_count: - счетчик по rx
        :return:
            PDRMetrics - рассчитанные метрики PDR
        """

        pdr = rx_count / tx_count if tx_count > 0 else 0.0
        return cls(tx_count=tx_count, rx_count=rx_count, pdr=pdr)


class ConnectionMetrics(BaseModel):
    """
    Модель данных для метрик, подсчитанных под определенную ключевую пару или другое поле группировки
    """

    src: str
    dst: str
    pdr_metrics: PDRMetrics
    latency_stats: LatencyStats
    app: Optional[str] = None
    window_start: Optional[int] = None
    sinr_avg: Optional[float] = None
    sinr_count: Optional[float] = None


class MetricsResult(BaseModel):
    """
    Финальная структура подсчета всех агрегатов, для дальнейшей единой выгрузки
    """

    overall: ConnectionMetrics
    by_pair: Dict[Tuple[str, str], ConnectionMetrics]
    by_app: Dict[str, ConnectionMetrics]
    by_window: Dict[Tuple[int, str, str], ConnectionMetrics]
    anomalies: Dict[str, int]
    processed_cnt: int
    success_cnt: int
