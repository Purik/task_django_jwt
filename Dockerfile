FROM python:3.12

RUN pip install poetry==1.8.5

COPY ./pyproject.toml ./poetry.lock /
COPY ./app /app

RUN poetry export -f requirements.txt --output requirements.txt --without-hashes
RUN python3 -m pip install --no-cache-dir --upgrade -r requirements.txt
