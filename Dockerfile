FROM python:3.10-slim

# FFmpeg install for Discord audio
RUN apt-get update && apt-get install -y ffmpeg

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "bot.py"]
