# FROM selenium/standalone-firefox

# RUN sudo apt-get update && sudo apt-get install -y \
#     python3.12-venv

# WORKDIR /app/zazatappo-vacanzi

# RUN sudo python3 -m venv /app/venv

# COPY requirements.txt .

# RUN sudo /app/venv/bin/pip install -r requirements.txt

# COPY . . 

# CMD ["/app/venv/bin/python", "main.py"]

FROM python:3.12.9-slim

RUN apt-get update && apt-get install -y \
    chromium chromium-driver

WORKDIR /app/zazatappo-vacanzi

COPY requirements.txt .

RUN pip install -r requirements.txt

COPY . . 

CMD ["python", "main.py"]