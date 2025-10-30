import sys
import os

from typing import Dict, Set, Iterable, Any
from pathlib import Path
from abc import ABC, abstractmethod

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ParseResult, EventType
from configs.interfaces import ParserInterface


class TestParser(ParserInterface, ABC):
    """
    Тестовый родительский абстрактный парсер,
    для создания первых двух парсеров с расширенным от интерфейса функционалом
    """

    def __init__(self):
        self._processed_cnt = 0
        self._error_cnt = 0
        self._validation_error_cnt = 0

    def get_stats(self) -> Dict[str, int]:
        return {
            'processed_cnt': self._processed_cnt,
            'error_cnt': self._error_cnt,
            'validation_error_cnt': self._validation_error_cnt,
            'success_cnt': self._processed_cnt - self._error_cnt - self._validation_error_cnt,
        }

    def _increment_processed_cnt(self) -> None:
        self._processed_cnt += 1

    def _increment_error_cnt(self) -> None:
        self._error_cnt += 1

    def _increment_validation_error_cnt(self) -> None:
        self._validation_error_cnt += 1

    def validate_file_format(self, file_path: Path) -> bool:
        if not file_path.exists():
            return False
        elif not file_path.is_file():
            return False

        return file_path.suffix.lower() in self.supported_extensions

    def reset_stats(self) -> None:
        self._processed_cnt = 0
        self._error_cnt = 0
        self._validation_error_cnt = 0

    @property
    @abstractmethod
    def supported_extensions(self) -> Set[str]:
        """
        Возвращает все доступные для парсера расширения
        :return:
            Set[str] - множество доступных расширений для файла
        """

        pass

    @property
    @abstractmethod
    def parse_name(self) -> str:
        """
        Уникальное навание парсера
        """

        pass

    @abstractmethod
    def parse_data_stream(self, file_path: Path) -> Iterable[Any]:
        """
        Создает поток обработки данных источника
        :param:
            file_path: - путь, по которому находится источник данных
        :return:
            Iterable[Any]: - создает генератор с обработанными данными
        """

        pass
