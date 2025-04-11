
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import noisereduce as nr
import librosa
import soundfile as sf
import subprocess
import os

app = FastAPI()

# CORS 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001", "http://localhost:8001"],  # 추가 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/upload")
async def upload_file(audio: UploadFile = File(...)):
    try:
        contents = await audio.read()
        with open("received.webm", "wb") as f:
            f.write(contents)

        # WebM → WAV 변환
        subprocess.run(["ffmpeg", "-y", "-i", "received.webm", "converted.wav"], check=True)

        # 노이즈 제거
        data, rate = librosa.load("converted.wav", sr=None)
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        sf.write("clean.wav", reduced_noise, rate)

        return {"message": "업로드 및 소음 제거 완료"}
    except Exception as e:
        print(f"Error in upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@app.get("/download")
async def download_file():
    file_path = "clean.wav"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="clean.wav file not found")
    return FileResponse(
        path=file_path,
        media_type="audio/wav",
        filename="processed.wav"
    )

# 실행: uvicorn main:app --reload
