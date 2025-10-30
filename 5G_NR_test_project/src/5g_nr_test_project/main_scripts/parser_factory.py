import os
import sys

from typing import List, Type
from pathlib import Path

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.interfaces import ParserInterface
from main_scripts.parsers import NJsonParser, CsvParser, Ns3CsvParser


class ParserFactory:
    """
    Фабрика для создания парсеров с проверкой соответствия интерфейсу
    """

    def __init__(self):
        self._parser_classes: List[Type[ParserInterface]] = [
            NJsonParser,
            CsvParser#,
            # Ns3CsvParser
        ]

    def get_parser(self, file_path: Path) -> ParserInterface:
        """
        Создает и выбирает, подходящий для обработки парсер
        :param:
            file_path: - путь к файлу, который хотим обработать
        :return:
            ParserInterface - возвращает экземпляр класса парсера, который может обработать файл
        """
        if not file_path.exists():
            raise FileNotFoundError(f"Файл не был найден: {file_path}")

        for parser_class in self._parser_classes:
            parser = parser_class()
            if parser.validate_file_format(file_path):
                return parser

        raise ValueError(f"Не обнаружено подходящего парсера для обработки файла: {file_path}\n"
                         f"Поддерживаемые форматы файлов: {self._get_all_extentions()}")

    def _get_all_extentions(self) -> List[str]:
        """
        Возвращает массив поддерживаемых текущими парсерами форматов файлов
        :return:
            List[str]: - список с поддерживаемыми форматами в виде строк
        """

        extentions = set()
        for parser_class in self._parser_classes:
            parser = parser_class()
            extentions.update(parser.supported_extensions)
        return sorted(extentions)


_default_parser_factory = ParserFactory()

def get_parser_factory() -> ParserFactory:
    """
    Простая функция для получения инициализированной фабрики
    :return:
        ParserFactory: - фабрика парсеров
    """

    return _default_parser_factory
