FROM python:3.8
WORKDIR /YouTube-Video-Downloader-WithBoto3-Integration
RUN mkdir -p media
RUN apt update &&  apt install -y ffmpeg
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install --upgrade pytube
COPY . .
EXPOSE 8020
CMD ["uvicorn", "--host", "0.0.0.0", "--port", "8020", "app:app"]