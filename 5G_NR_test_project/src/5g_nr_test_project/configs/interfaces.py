import sys
import os

from typing import Iterator, Dict
from pathlib import Path
from abc import ABC, abstractmethod

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ParseResult


class ParserInterface(ABC):
    """
    Интерфейс для возможности создания новых парсеров с единым функционалом
    """

    @abstractmethod
    def parse_data_stream(self, file_path: Path) -> Iterator[ParseResult]:
        """
        Метод парсинга источника данных
        :param:
           file_path: Path - путь к файлу источнику, из которого мы хотим извлечь данные
        :return:
           Iterator[ParserResult] - Генератор, с записями в формате модели данных ParserResult
        """
        pass

    @abstractmethod
    def validate_file_format(self, file_path: Path) -> bool:
        """
        Метод для определения, подходит ли файл под логику обработки парсера
        :param:
            file_path: Path - путь к файлу источнику, из которого мы хотим извлечь данные
        :return:
            bool - Возвращает булевое значение, в котором True - файл может быть обработан парсером, False - нет
        """
        pass

    @abstractmethod
    def get_stats(self) -> Dict[str, int]:
        """
        Пока метод заглушка для возможной будущей реализации сбора статистики по работе парсера, но лучше будет
        использовать метакласс.
        :return:
            Dict[str, int] - словарь со статистикой внутри в формате {
                'processed': X,
                'errors': Y,
                'successful': Z
            }
        """
        pass


# @runtime_checkable
# class ParserProtocol(Protocol):
#     """
#     Интерфейс для всех парсеров
#     """
#
#     def parse_data_stream(self, file_path: Path) -> Iterator[ParseResult]:
#         """
#         Метод парсинга источника данных
#         :param:
#             file_path: Path - путь к файлу источнику, из которого мы хотим извлечь данные
#         :return:
#             Iterator[ParserResult] - Генератор, с записями в формате модели данных ParserResult
#         """
#         ...
#
#
#     def validate_file_format(self, file_path: Path) -> bool:
#         """
#         Метод для определения, подходит ли файл под логику обработки парсера
#         :param:
#             file_path: Path - путь к файлу источнику, из которого мы хотим извлечь данные
#         :return:
#             bool - Возвращает булевое значение, в котором True - файл может быть обработан парсером, False - нет
#         """
#         ...
#
#
#     def get_stats(self) -> dict[str, int]:
#         """
#         Пока метод заглушка для возможной будущей реализации сбора статистики по работе парсера, но лучше будет
#         использовать метакласс.
#         """
#         pass
