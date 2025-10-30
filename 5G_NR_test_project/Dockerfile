FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ make && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml poetry.lock* ./

RUN pip install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --without dev --no-root

COPY . .

RUN mkdir -p artifacts plots parsed_files logs

RUN pip install -e .

ENV PYTHONPATH=/app/src

CMD ["python", "-m", "src.5g_nr_test_project.cli", "--help"]
