import os
import sys
import click
import logging

from pathlib import Path
from datetime import datetime

current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.join(current_dir, '..', '..'))
sys.path.insert(0, project_root)

from .main_scripts.parser_factory import get_parser_factory
from .main_scripts.processor import MetricsCalculator
from .visualization.plotter import Plotter


def setup_logging():
    """
    Функция настройки логирования
    """

    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_dir / 'nr_metrics.log', encoding='utf-8')
        ]
    )


@click.group()
def main():
    """
    NR Metrics Processor - CLI for 5G V2X log analysis
    """

    setup_logging()
    logging.info("Расчет по проекту запущен")


@main.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output-file', help='Путь файла, в который нужно записать обработанные данные')
def parse(input_file: str, output_file: str):
    """
    Команда для создания потока данных из источника
    :param:
        input_file: - путь входного файла
        output_file: - путь директории хранения унифицированных файлов
    """

    logging.info(f"Парсинг файла: {input_file}")

    try:
        input_path = Path(input_file).resolve()
        if not input_path.is_file() or not input_path.exists():
            logging.error(f"Файл не был найден: {input_file}")

        project_root_path = Path(__file__).parent.parent.parent
        parsed_files_dir = project_root_path / "parsed_files"
        parsed_files_dir.mkdir(parents=True, exist_ok=True)

        if output_file:
            output_path = Path(output_file).resolve()

            if not output_path.is_file():
                logging.error(f"Выходной файл указан неверно. Не является файлом: {output_path}")
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
        else:
            date = datetime.now().strftime('%Y%m%d')
            output_filename = f"{input_path.stem}_parsed_{date}.json"
            output_path = parsed_files_dir / output_filename

        parser_factory = get_parser_factory()
        logging.info(f"Поиск подходящего для обработки парсера")
        parser = parser_factory.get_parser(input_path)

        logging.info(f"Выполняет работу парсер: {parser.parse_name}")

        with open(output_path, mode='w', encoding='utf-8') as file:
            for record in parser.parse_data_stream(input_path):
                file.write(record.model_dump_json() + '\n')

        logging.info(f"Парсер успешно обработал источник данных: {input_file} -> {output_path}")
        logging.info(f"Парсинг данных завершен")

    except Exception as e:
        logging.error(f"Ошибка в парсинге: {e}")


@main.command()
@click.argument('unified_file', type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./artifacts', help='Директория для хранения итоговых метрик')
@click.option('-w', '--window-size', default=1000000, help='Размер временного интервала, для агрегации метрик')
def metrics(unified_file: str, output_dir: str, window_size: int):
    """
    Команда для расчета итоговых метрик
    :param:
        unified_file: - путь к входному унифицированному файлу
        output_dir: - путь к выходной директории
        window_size: - размер временного интервала, для агрегации метрик
    """

    logging.info(f"Старт расчета метрик из потока данных: {unified_file}")

    try:
        unified_path = Path(unified_file)
        if not unified_path.exists():
            logging.error(f"Указан неверный унифицированный файл с данными: {unified_file}")
            return

        artifacts_dir = Path(output_dir)
        source_name = unified_path.stem
        final_output_dir = artifacts_dir / source_name
        final_output_dir.mkdir(parents=True, exist_ok=True)

        calculator = MetricsCalculator(window_size=window_size)

        parser_factory = get_parser_factory()
        parser = parser_factory.get_parser(unified_path)

        for record in parser.parse_data_stream(unified_path):
            calculator.process_record(record)

        calculator.export_comprehensive(final_output_dir)

        current_proc_stats = calculator.get_curr_stats()
        current_summary = calculator.get_summary()

        click.echo("\n" + "=" * 40)
        click.echo("СТАТИСТИКА ПО ОБРАБОТКЕ")
        click.echo("=" * 40)
        click.echo(f"Количество обработанных записей: {current_proc_stats['processed_cnt']}")
        click.echo(f"Количество успешно связанных записей tx и rx: {current_proc_stats['sucess_cnt']}")
        click.echo(f"Процент связанных записей tx и rx: {current_proc_stats['matched']}")
        click.echo(f"PDR по всему фрейму данных: {current_summary['overall_pdr']}")
        click.echo(f"Среднее значение latency по всему датафрейму: {current_summary['overall_latency_mean']}")
        click.echo(f"Количество уникальных пар объектов: {current_summary['unique_pairs']}")
        click.echo("=" * 40 + "\n")

        logging.info(f"Расчет метрик закончен. Поток данных закрыт")
        logging.info(f"Метрики сохранены в директорию: {final_output_dir}")

    except Exception as e:
        logging.error(f"Ошибка подсчета итоговых метрик: {e}")


@main.command()
@click.argument('metrics_dir', type=click.Path(exists=True))
@click.option('-o', '--output-dir', default='./plots', help='Директория для графиков')
@click.option('--pair', help='Пара для анализа в формате "src,dst"')
def plot(metrics_dir: str, output_dir: str, pair: str = None):
    """
    Команда для построения графиков по рассчитанным метрикам
    """

    logging.info(f"Старт построения графиков из метрик: {metrics_dir}")

    try:
        plots_dir = Path(output_dir)
        source_name = Path(metrics_dir).name
        final_output_dir = plots_dir / source_name
        final_output_dir.mkdir(parents=True, exist_ok=True)

        plotter = Plotter(Path(final_output_dir))
        success = plotter.create_all_plots(Path(metrics_dir), pair)

        if success:
            logging.info(f"Графики сохранены в: {output_dir}")
        else:
            logging.warning(f"При построении графиков возникли ошибки")

    except Exception as e:
        logging.error(f"Ошибка при построении графиков: {e}")


if __name__ == '__main__':
    main()
