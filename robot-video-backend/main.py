from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from openai import OpenAI
from dotenv import load_dotenv
import os
import cv2
import base64
import tempfile
import shutil
import requests

load_dotenv()
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

class VideoUrl(BaseModel):
    url: str

def get_video_duration(video_path):
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    frame_count = cap.get(cv2.CAP_PROP_FRAME_COUNT)
    cap.release()
    return int(frame_count / fps)

def extract_base64_frames(video_path, frame_interval=60, max_frames=6):
    cap = cv2.VideoCapture(video_path)
    frames_base64 = []
    idx = 0
    success, frame = cap.read()

    while success and len(frames_base64) < max_frames:
        if idx % frame_interval == 0:
            resized = cv2.resize(frame, (256, 256))  # Resize to reduce token size
            _, buffer = cv2.imencode(".jpg", resized)
            b64 = base64.b64encode(buffer).decode("utf-8")
            frames_base64.append(b64)
        success, frame = cap.read()
        idx += 1
    cap.release()
    return frames_base64

def generate_segment_prompt(base64_images, video_duration_seconds):
    segment_time = video_duration_seconds // len(base64_images)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": (
                        f"These are snapshots from a {video_duration_seconds}-second robot dashcam video. "
                        f"Describe what the robot is doing in each image. Then create a timeline with equal time segments. "
                        f"Use this format:\n\n"
                        f"00:00 - 00:{segment_time:02d} : [Action]\n"
                        f"...\n\nOnly return the timeline, nothing else."
                    )
                }
            ] + [
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/jpeg;base64,{img}"
                    }
                }
                for img in base64_images
            ]
        }
    ]
    return messages

def call_gpt4v_with_frames(base64_images, video_duration_seconds):
    messages = generate_segment_prompt(base64_images, video_duration_seconds)
    response = client.chat.completions.create(
        model="gpt-4-turbo",
        messages=messages,
        max_tokens=800
    )
    return response.choices[0].message.content

@app.post("/analyze/file")
async def analyze_from_file(file: UploadFile = File(...)):
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        shutil.copyfileobj(file.file, tmp)
        video_path = tmp.name

    duration = get_video_duration(video_path)
    frames_base64 = extract_base64_frames(video_path)
    result = call_gpt4v_with_frames(frames_base64, duration)

    os.remove(video_path)
    return {"segments": result.strip()}

@app.post("/analyze/url")
async def analyze_from_url(data: VideoUrl):
    response = requests.get(data.url, stream=True)
    if response.status_code != 200:
        return {"error": "Unable to download video."}

    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
        for chunk in response.iter_content(chunk_size=8192):
            tmp.write(chunk)
        video_path = tmp.name

    duration = get_video_duration(video_path)
    frames_base64 = extract_base64_frames(video_path)
    result = call_gpt4v_with_frames(frames_base64, duration)

    os.remove(video_path)
    return {"segments": result.strip()}
