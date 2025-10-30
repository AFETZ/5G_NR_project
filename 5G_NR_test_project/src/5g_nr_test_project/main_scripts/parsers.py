import json
import csv
import sys
import os

from typing import Dict, Set, Iterable, Any
from pathlib import Path
from pydantic import ValidationError

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from configs.models import ParseResult, EventType
from main_scripts.test_base_parser import TestParser
from support_scripts.progress_bar import ProgressBar


class NJsonParser(TestParser):
    """
    Парсер для считывания информации из Json файлов
    """

    def __init__(self):
        super().__init__()

    @property
    def supported_extensions(self) -> Set[str]:
        return {'.ndjson', '.json'}

    @property
    def parse_name(self) -> str:
        return 'NJSONParser'

    def parse_data_stream(self, file_path: Path) -> Iterable[ParseResult]:
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                progress_bar = ProgressBar.create_parser_progress_bar(file_path)

                for i, line in enumerate(file, 1):
                    self._increment_processed_cnt()

                    if not line.strip():
                        continue

                    try:
                        raw_data = json.loads(line.strip())
                        record = ParseResult(**raw_data)
                        yield record

                    except json.JSONDecodeError as e:
                        self._increment_error_cnt()
                        continue
                    except ValidationError as e:
                        self._increment_validation_error_cnt()
                        continue
                    except Exception:
                        self._increment_error_cnt()
                        continue

                    progress_bar.update(1)

                progress_bar.close()

        except Exception as e:
            raise RuntimeError(f"Ошибка в момент парсинга данных: {e}")

    def validate_file_format(self, file_path: Path) -> bool:
        if super().validate_file_format(file_path) == False:
            return False

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                first_line = file.readline().strip()
                if not first_line:
                    return True

                json.loads(first_line)
                return True

        except Exception:
            return False


class CsvParser(TestParser):

    def __init__(self, delimiter: str = ',', encoding: str = 'utf-8'):
        super().__init__()
        self.delimiter = delimiter
        self.encoding = encoding

    @property
    def supported_extensions(self) -> Set[str]:
        return {'.csv'}

    @property
    def parse_name(self) -> str:
        return 'CSVParser'

    def parse_data_stream(self, file_path: Path) -> Iterable[ParseResult]:
        try:
            with open(file_path, 'r', encoding=self.encoding, newline='') as file:
                progress_bar = ProgressBar.create_parser_progress_bar(file_path)

                reader = csv.DictReader(file, delimiter=self.delimiter)

                for i, row in enumerate(reader, 2):
                    self._increment_processed_cnt()

                    if not any(row.values()):
                        continue

                    record = self._parse_csv_row(row, i)
                    if record is not None:
                        yield record

                    progress_bar.update(1)

                progress_bar.close()

        except UnicodeDecodeError as e:
            self._increment_error_cnt()
            raise ValueError(f"Ошибка в кодировке CSV файла: {e}")
        except csv.Error as e:
            self._increment_error_cnt()
            raise ValueError(f"Ошибка в считывании CSV файла: {e}")
        except Exception as e:
            self._increment_error_cnt()
            raise RuntimeError(f"Ошибка в момент парсинга данных: {e}")


    def _parse_csv_row(self, row: Dict[str, str], row_number: int) -> ParseResult | None:
        """
        Парсинг одной строки, для преобразования в модель данных ParseResult. Также на этом
        этапе происходит валидация при помощи инструмента pydantic
        :param:
            row: - словарь с данными строки
        :return:
            ParseResult | None - модель данных
        """

        try:
            prepared_data = self._prepare_row(row)
            return ParseResult(**prepared_data)

        except ValidationError as e:
            self._increment_error_cnt()
            return None
        except Exception as e:
            self._increment_error_cnt()
            return None

    def _prepare_row(self, row: Dict[str, str]) -> Dict[str, Any]:
        prepared_data = {}

        for key, value in row.items():
            if value and value.strip():
                prepared_data[key] = value.strip()

        return prepared_data

    def validate_file_format(self, file_path: Path) -> bool:
        if super().validate_file_format(file_path) == False:
            return False

        try:
            with open(file_path, 'r', encoding=self.encoding, newline='') as file:
                csv_reader = csv.DictReader(file, delimiter=self.delimiter)

                for row in csv_reader:
                    if not any(row.values()):
                        continue

                    try:
                        prepared_data = self._prepare_row(row)
                        ParseResult(**prepared_data)
                        return True
                    except ValidationError as e:
                        return False

                return True

        except Exception:
            return False


class Ns3CsvParser(TestParser):
    """
    Заглушка для будущего парсера
    """

    def parse_data_stream(self, file_path: Path):
        pass

    def validate_file_format(self, file_path: Path) -> bool:
        pass
