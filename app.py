from fastapi import FastAPI
import boto3
from pytube import YouTube
from pathlib import Path
import uuid
import os
from dotenv import load_dotenv
import mutagen
from pydantic import BaseModel
import yt_dlp


load_dotenv(dotenv_path='.env')
save_path = 'media/'
END_POINT_URL = os.getenv('END_POINT_URL')
MINIO_ACCESS_KEY_ID = os.getenv('MINIO_ACCESS_KEY_ID')
MINIO_SECRET_ACCESS_KEY = os.getenv('MINIO_SECRET_ACCESS_KEY')
REGION_NAME = os.getenv('REGION_NAME')
API_KEY = os.getenv('API_KEY')

app = FastAPI()


class Item(BaseModel):
    api_key: str
    video_link: str


@app.post("/api/file/download")
async def file_downloader(item: Item):
    try:
        if API_KEY == item.api_key:
            session = boto3.session.Session()
            client = session.client('s3',
                                    region_name=REGION_NAME,
                                    endpoint_url=END_POINT_URL,
                                    aws_access_key_id=MINIO_ACCESS_KEY_ID,
                                    aws_secret_access_key=MINIO_SECRET_ACCESS_KEY
                                    )
            uuid_id = str(uuid.uuid4())
            video_filename = uuid_id + '.mp4'
            try:
                youtube = YouTube(item.video_link)
                youtube.streams.get_highest_resolution().download(save_path, filename=video_filename)
            except:
                ydl_opts = {
                    'format': 'best',
                    'outtmpl': save_path+video_filename,
                    'quiet': True,
                }
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info_dict = ydl.extract_info(item.video_link, download=True)
                    info_dict.get('title', 'Untitled')

            video_path = Path(save_path + video_filename)
            mp4 = open(video_path, "rb")
            client.put_object(Bucket='videos', Key=video_filename, Body=mp4,
                              ContentType="video/mp4", )

            audio_file_name = uuid_id + ".wav"
            audio_path = save_path + uuid_id + ".wav"
            cmd_str = f"ffmpeg -i {save_path + video_filename} -ac 1 -ar 16000 {audio_path}"
            os.system(cmd_str)
            mp3 = open(audio_path, "rb")
            client.put_object(Bucket='audios', Key=audio_file_name, Body=mp3,
                              ContentType="audio/x-wav", )
            duration = mutagen.File(mp3).info.length
            os.remove(video_path)
            os.remove(audio_path)

            return {
                'video_file_name': video_filename,
                'video_url': 'videos/' + video_filename,
                'audio_file_name': audio_file_name,
                'audio_url': 'audios/' + audio_file_name,
                'duration': duration,
            }
        else:
            return {'message': 'Something went wrong.'}
    except Exception as ex:
        print(ex)
        return {'message': 'Something went wrong.'}
    
