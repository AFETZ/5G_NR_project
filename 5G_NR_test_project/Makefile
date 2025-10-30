.PHONY: demo clean help docker-test

demo: demo-csv
	@echo "Демо было обработано"

demo-csv:
	@echo "Запуск демо с форматом файла csv: sample.csv"
	python -m src.5g_nr_test_project.cli parse tests/sample.csv -o parsed_files/sample_parsed.json
	python -m src.5g_nr_test_project.cli metrics parsed_files/sample_parsed.json -o artifacts
	python -m src.5g_nr_test_project.cli plot artifacts/sample_parsed -o plots

demo-json:
	@echo "Запуск демо с форматом файла json: sample_big_test.ndjson"
	python -m src.5g_nr_test_project.cli parse tests/sample_big_test.ndjson -o parsed_files/sample_big_test.json
	python -m src.5g_nr_test_project.cli metrics parsed_files/sample_big_test.json -o artifacts
	python -m src.5g_nr_test_project.cli plot artifacts/sample_big_test -o plots

docker-test:
	@echo "Тестирование Docker (только парсинг)"
	docker build -t nr_metrics .
	docker run -v $(PWD)/artifacts:/app/artifacts \
               -v $(PWD)/plots:/app/plots \
               -v $(PWD)/parsed_files:/app/parsed_files \
               -v $(PWD)/logs:/app/logs \
               nr_metrics python -m src.5g_nr_test_project.cli parse tests/sample.csv -o parsed_files/docker_test.json

clean:
	@echo "Очистка директорий с расчетами"
	rm -rf artifacts/* plots/* parsed_files/* logs/* *.log

docker-build:
	@echo "Сборка Docker образа"
	docker build -t nr_metrics .

docker-demo: docker-build
	@echo "Запуск демо в Docker"
	docker run -v $(PWD)/artifacts:/app/artifacts \
               -v $(PWD)/plots:/app/plots \
               -v $(PWD)/parsed_files:/app/parsed_files \
               -v $(PWD)/logs:/app/logs \
               nr_metrics make demo-csv

help:
	@echo "Доступные команды:"
	@echo "make demo         - Запуск демо с sample.csv"
	@echo "make demo-json    - Запуск демо с sample_big_test.ndjson"
	@echo "make docker-test  - Тест Docker"
	@echo "make clean        - Очистка артефактов"
	@echo "make docker-build - Сборка Docker образа"
	@echo "make docker-demo  - Запуск демо в Docker"
	@echo "make help         - Показать справку"
