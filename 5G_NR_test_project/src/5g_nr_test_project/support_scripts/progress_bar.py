from tqdm import tqdm
from pathlib import Path


class ProgressBar:

    @staticmethod
    def create_parser_progress_bar(file_path: Path) -> tqdm:
        """
        Создаем строку прогресса для вывода статуса загрузки файла в консоль
        :param:
            file_path: - путь к файлу, статус которого будет анализировать
        :return:
            tqdm: - Тип данных для быстрого построения строки прогресса
        """

        try:
            total_lines_cnt = ProgressBar.count_lines(file_path)
        except Exception:
            total_lines_cnt = None

        return tqdm(
            desc="Parsing",
            total=total_lines_cnt,
            unit="line",
            ncols=100,
            bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]"
        )

    @staticmethod
    def count_lines(file_path: Path) -> int:
        """
        Подсчет итогового количества строк в файле
        :param
            file_path: - путь к файлу
        :return:
            int: - количество строк
        """

        with open(file_path, "r", encoding='utf-8') as f:
            return sum(1 for _ in f)
