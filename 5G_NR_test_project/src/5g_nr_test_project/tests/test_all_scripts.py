# test_parsers_workflow.py
import sys
import os
from pathlib import Path
import csv
import json
from typing import List, Dict, Any
import random

# Добавляем путь к проекту для импорта
current_dir = os.path.dirname( os.path.abspath( __file__ ) )
project_root = os.path.dirname( os.path.join( current_dir, '..', '..' ) )
sys.path.insert( 0, project_root )

from main_scripts.parsers import NJsonParser, CsvParser
from main_scripts.parser_factory import ParserFactory, get_parser_factory
from configs.models import ParseResult


class ParserTester:
    """Комплексный тестер для проверки работоспособности парсеров"""

    def __init__(self):
        self.test_dir = Path( "../main_scripts/test_results" )
        self.test_dir.mkdir( exist_ok=True )
        self.factory = get_parser_factory()
        self.record_count = 30  # Увеличили до 30 записей

    def generate_test_data(self) -> tuple:
        """Генерирует тестовые данные (30 записей)"""
        ndjson_data = []
        csv_data = []

        base_time = 0
        cars = [f"car_{i}" for i in range( 1, 11 )]  # 10 разных автомобилей
        apps = ["BSM", "SPAT", "MAP", "RSI"]

        for i in range( self.record_count ):
            # Базовые данные для записи
            ts_us = base_time + i * 100
            src = random.choice( cars )
            dst = random.choice( [c for c in cars if c != src] )
            pkt_id = f"pkt_{i:03d}"
            app = random.choice( apps )
            bytes_size = random.randint( 200, 500 )

            # Случайно выбираем событие (tx или rx)
            if i % 3 == 0:  # Каждая третья запись - rx, остальные tx
                event = "rx"
                rssi = round( random.uniform( -80, -60 ), 1 )
                sinr = round( random.uniform( 10, 25 ), 1 )
            else:
                event = "tx"
                rssi = round( random.uniform( -70, -50 ), 1 )
                sinr = round( random.uniform( 15, 30 ), 1 )

            # NDJSON запись
            ndjson_record = {
                "ts_us": ts_us,
                "event": event,
                "src": src,
                "dst": dst,
                "pkt_id": pkt_id,
                "app": app,
                "bytes": bytes_size,
                "rssi_dbm": rssi,
                "sinr_db": sinr
            }
            ndjson_data.append( ndjson_record )

            # CSV запись (все значения как строки)
            csv_record = {
                "ts_us": str( ts_us ),
                "event": event,
                "src": src,
                "dst": dst,
                "pkt_id": pkt_id,
                "app": app,
                "bytes": str( bytes_size ),
                "rssi_dbm": str( rssi ) if random.random() > 0.2 else "",  # 20% пустых значений
                "sinr_db": str( sinr ) if random.random() > 0.2 else "",  # 20% пустых значений
                "drop_reason": ""  # Всегда пустое в тестовых данных
            }
            csv_data.append( csv_record )

        return ndjson_data, csv_data

    def create_test_files(self) -> Dict[str, Path]:
        """Создает тестовые файлы разных форматов с 30 записями"""
        test_files = {}
        ndjson_data, csv_data = self.generate_test_data()

        # 1. Создаем корректный NDJSON файл
        ndjson_path = self.test_dir / "test_data_30.ndjson"
        with open( ndjson_path, 'w', encoding='utf-8' ) as f:
            for record in ndjson_data:
                f.write( json.dumps( record ) + '\n' )
        test_files['ndjson'] = ndjson_path

        # 2. Создаем корректный CSV файл
        csv_path = self.test_dir / "test_data_30.csv"
        with open( csv_path, 'w', newline='', encoding='utf-8' ) as f:
            if csv_data:
                writer = csv.DictWriter( f, fieldnames=csv_data[0].keys() )
                writer.writeheader()
                writer.writerows( csv_data )
        test_files['csv'] = csv_path

        # 3. Создаем файл с ошибками для тестирования обработки ошибок
        error_ndjson_data = [
            '{"ts_us": 1000, "event": "tx", "src": "car_1", "dst": "car_2", "pkt_id": "a1", "app": "BSM", "bytes": 250}',
            'INVALID JSON LINE',
            '{"ts_us": "not_number", "event": "tx", "src": "car_1", "dst": "car_2", "pkt_id": "a2", "app": "BSM", "bytes": 250}',
            '{"ts_us": 1100, "event": "invalid_event", "src": "car_1", "dst": "car_2", "pkt_id": "a3", "app": "BSM", "bytes": 250}',
            '{"ts_us": 1200, "event": "tx", "src": "", "dst": "car_2", "pkt_id": "a4", "app": "BSM", "bytes": 250}',
            # Пустой src
            '{"ts_us": 1300, "event": "rx", "src": "car_1", "dst": "", "pkt_id": "a5", "app": "BSM", "bytes": 250}',
            # Пустой dst
        ]

        error_ndjson_path = self.test_dir / "test_errors.ndjson"
        with open( error_ndjson_path, 'w', encoding='utf-8' ) as f:
            for line in error_ndjson_data:
                f.write( line + '\n' )
        test_files['ndjson_errors'] = error_ndjson_path

        print( "✅ Тестовые файлы созданы:" )
        for name, path in test_files.items():
            file_size = path.stat().st_size
            print( f"   - {name}: {path} ({file_size} bytes)" )

        return test_files

    def test_parser_factory(self, test_files: Dict[str, Path]):
        """Тестирует фабрику парсеров"""
        print( "\n🔧 ТЕСТИРОВАНИЕ ФАБРИКИ ПАРСЕРОВ" )
        print( "-" * 50 )

        for format_name, file_path in test_files.items():
            if 'error' not in format_name:
                try:
                    parser = self.factory.get_parser( file_path )
                    print( f"✅ {format_name.upper()}: {parser.__class__.__name__}" )
                    print( f"Поддерживаемые расширения: {parser.supported_extensions}" )
                except Exception as e:
                    print( f"❌ {format_name.upper()}: Ошибка - {e}" )

    def test_njson_parser(self, test_files: Dict[str, Path]):
        """Тестирует NDJSON парсер"""
        print( "\n📄 ТЕСТИРОВАНИЕ NDJSON ПАРСЕРА" )
        print( "-" * 50 )

        # Тестируем корректный файл
        parser = NJsonParser()
        valid_file = test_files['ndjson']

        print( f"Тестируем файл: {valid_file}" )

        try:
            records = list( parser.parse_data_stream( valid_file ) )
            stats = parser.get_stats()

            print( f"✅ Успешно распаршено записей: {len( records )} из {self.record_count}" )
            print( f"📊 Статистика: {stats}" )

            if records:
                print( "\nПримеры записей:" )
                for i in range( min( 2, len( records ) ) ):
                    record = records[i]
                    print( f"  Запись {i + 1}:" )
                    print( f"    ts_us: {record.ts_us}, event: {record.event}" )
                    print( f"    src: {record.src} -> dst: {record.dst}" )
                    print( f"    pkt_id: {record.pkt_id}, app: {record.app}" )
                    print( f"    bytes: {record.bytes}" )

        except Exception as e:
            print( f"❌ Ошибка парсинга: {e}" )

    def test_csv_parser(self, test_files: Dict[str, Path]):
        """Тестирует CSV парсер"""
        print( "\n📊 ТЕСТИРОВАНИЕ CSV ПАРСЕРА" )
        print( "-" * 50 )

        parser = CsvParser()
        csv_file = test_files['csv']

        print( f"Тестируем файл: {csv_file}" )

        try:
            records = list( parser.parse_data_stream( csv_file ) )
            stats = parser.get_stats()

            print( f"✅ Успешно распаршено записей: {len( records )} из {self.record_count}" )
            print( f"📊 Статистика: {stats}" )

            if records:
                print( "\nПримеры записей:" )
                for i in range( min( 2, len( records ) ) ):
                    record = records[i]
                    print( f"  Запись {i + 1}:" )
                    print( f"    ts_us: {record.ts_us}, event: {record.event}" )
                    print( f"    src: {record.src} -> dst: {record.dst}" )
                    print( f"    pkt_id: {record.pkt_id}, app: {record.app}" )
                    print( f"    bytes: {record.bytes}" )
                    if record.rssi_dbm:
                        print( f"    rssi_dbm: {record.rssi_dbm}" )

        except Exception as e:
            print( f"❌ Ошибка парсинга: {e}" )

    def test_streaming_capability(self, test_files: Dict[str, Path]):
        """Тестирует streaming возможности парсеров"""
        print( "\n⚡ ТЕСТИРОВАНИЕ STREAMING РЕЖИМА" )
        print( "-" * 50 )

        # Тестируем NDJSON streaming
        print( "NDJSON Streaming тест:" )
        parser = NJsonParser()
        records_yielded = 0
        start_memory = self._get_memory_usage()

        for record in parser.parse_data_stream( test_files['ndjson'] ):
            records_yielded += 1
            if records_yielded <= 3:
                print( f"  Yielded record {records_yielded}: {record.pkt_id}" )

        end_memory = self._get_memory_usage()
        print( f"  Всего записей через streaming: {records_yielded}" )
        print( f"  Использование памяти: {end_memory - start_memory:.2f} MB" )

        # Тестируем CSV streaming
        print( "\nCSV Streaming тест:" )
        csv_parser = CsvParser()
        records_yielded = 0
        start_memory = self._get_memory_usage()

        for record in csv_parser.parse_data_stream( test_files['csv'] ):
            records_yielded += 1
            if records_yielded <= 3:
                print( f"  Yielded record {records_yielded}: {record.pkt_id}" )

        end_memory = self._get_memory_usage()
        print( f"  Всего записей через streaming: {records_yielded}" )
        print( f"  Использование памяти: {end_memory - start_memory:.2f} MB" )

    def _get_memory_usage(self) -> float:
        """Возвращает использование памяти в MB"""
        try:
            import psutil
            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return 0.0

    def test_validation(self, test_files: Dict[str, Path]):
        """Тестирует валидацию форматов файлов"""
        print( "\n🔍 ТЕСТИРОВАНИЕ ВАЛИДАЦИИ ФАЙЛОВ" )
        print( "-" * 50 )

        parsers = [NJsonParser(), CsvParser()]

        for parser in parsers:
            print( f"\n{parser.__class__.__name__}:" )
            for format_name, file_path in test_files.items():
                is_valid = parser.validate_file_format( file_path )
                status = "✅ ВАЛИДЕН" if is_valid else "❌ НЕВАЛИДЕН"
                print( f"  {file_path.name}: {status}" )

    def test_performance(self, test_files: Dict[str, Path]):
        """Тестирует производительность парсеров"""
        print( "\n⏱️  ТЕСТИРОВАНИЕ ПРОИЗВОДИТЕЛЬНОСТИ" )
        print( "-" * 50 )

        import time

        # NDJSON performance
        parser = NJsonParser()
        start_time = time.time()

        records = list( parser.parse_data_stream( test_files['ndjson'] ) )
        ndjson_time = time.time() - start_time

        print( f"NDJSON парсер: {ndjson_time:.4f} секунд для {len( records )} записей" )
        print( f"Скорость: {len( records ) / ndjson_time:.2f} записей/секунду" )

        # CSV performance
        csv_parser = CsvParser()
        start_time = time.time()

        records = list( csv_parser.parse_data_stream( test_files['csv'] ) )
        csv_time = time.time() - start_time

        print( f"CSV парсер: {csv_time:.4f} секунд для {len( records )} записей" )
        print( f"Скорость: {len( records ) / csv_time:.2f} записей/секунду" )

    def test_edge_cases(self):
        """Тестирует крайние случаи"""
        print( "\n🚩 ТЕСТИРОВАНИЕ КРАЙНИХ СЛУЧАЕВ" )
        print( "-" * 50 )

        # Тест 1: Несуществующий файл
        print( "1. Тест несуществующего файла:" )
        try:
            parser = self.factory.get_parser( Path( "nonexistent_file.xyz" ) )
            print( "❌ Ожидалась ошибка для несуществующего файла" )
        except (ValueError, FileNotFoundError) as e:
            print( f"✅ Корректно обработана ошибка: {e}" )

        # Тест 2: Неподдерживаемый формат
        print( "\n2. Тест неподдерживаемого формата:" )
        unsupported_file = self.test_dir / "test.unsupported"
        unsupported_file.write_text( "some data" )
        try:
            parser = self.factory.get_parser( unsupported_file )
            print( "❌ Ожидалась ошибка для неподдерживаемого формата" )
        except ValueError as e:
            print( f"✅ Корректно обработана ошибка: {e}" )
        finally:
            if unsupported_file.exists():
                unsupported_file.unlink()

    def run_all_tests(self):
        """Запускает все тесты"""
        print( "🚀 ЗАПУСК КОМПЛЕКСНОГО ТЕСТИРОВАНИЯ ПАРСЕРОВ" )
        print( "=" * 60 )
        print( f"📊 Тестируем с {self.record_count} записями на файл" )

        # Создаем тестовые файлы
        test_files = self.create_test_files()

        # Запускаем все тесты
        self.test_parser_factory( test_files )
        self.test_njson_parser( test_files )
        self.test_csv_parser( test_files )
        self.test_streaming_capability( test_files )
        self.test_validation( test_files )
        self.test_performance( test_files )
        self.test_edge_cases()

        print( "\n" + "=" * 60 )
        print( "🎉 ТЕСТИРОВАНИЕ ЗАВЕРШЕНО!" )

        # Очистка тестовых файлов (опционально)
        #self.cleanup_test_files( test_files )

    def cleanup_test_files(self, test_files: Dict[str, Path]):
        """Очищает тестовые файлы"""
        print( "\n🧹 Очистка тестовых файлов..." )
        for file_path in test_files.values():
            if file_path.exists():
                file_path.unlink()
                print( f"   Удален: {file_path}" )

        # Удаляем директорию если пустая
        if self.test_dir.exists() and not any( self.test_dir.iterdir() ):
            self.test_dir.rmdir()
            print( f"   Удалена директория: {self.test_dir}" )


def main():
    """Основная функция запуска тестирования"""
    try:
        tester = ParserTester()
        tester.run_all_tests()
    except Exception as e:
        print( f"❌ Критическая ошибка при тестировании: {e}" )
        import traceback
        traceback.print_exc()
        return 1

    return 0


if __name__ == "__main__":
    exit( main() )
