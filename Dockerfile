# syntax=docker/dockerfile:1

FROM python:3.9

WORKDIR /app

COPY ./requirements.txt /app/requirements.txt

RUN pip install -r requirements.txt

COPY . /app

ENTRYPOINT [ "python" ]

# CMD [ "python3", "-m" , "flask", "run", "--host=0.0.0.0"]
CMD [ "main.py" ]