FROM python:3.12.9-slim

WORKDIR /app/zazatappo-vacanzi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . . 

CMD ["python", "main.py"]