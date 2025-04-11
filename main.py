# FastAPI 관련 모듈 불러오기
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware

# 소음 제거 및 파일 변환 라이브러리
import noisereduce as nr
import librosa
import soundfile as sf
import subprocess
import os

# 웹 서버의 컨트롤러(리모컨)
app = FastAPI()

# CORS 설정 :
# 프론트엔드와 백엔드가 서로 다른 포트를 사용하지 하기 때문에 요청을 허용하는 설정.
# 보안 문제 때문에 다른 곳에서 하는 요청을 막는다고 함.
# 때문에 설정은 8001번 포트를 사용하는 프론트엔드에서 백엔드로의 요청을 허용함.
# 이걸 몰라서 계속 안 됐던 거였음.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:8001", "http://localhost:8001"],  # 추가 출처 허용
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 함수에 기능 추가해주는 데코레이터라는데, 쉽게 생각해서 /upload 주소로로 post요청오면 실행하는 코드들들
@app.post("/upload")

 # 프론트엔드에서서 업로드한 파일을을 받음
async def upload_file(audio: UploadFile = File(...)):

    #예외처리리
    try:
         # 업로드된 파일의 내용을 비동기로 읽음
         # 비동기로 읽는 이유는 비동기를 안하면 읽는 동안 다른 요청을 못 받음음
        contents = await audio.read()

        # 읽은 내용을 received.webm 파일로 저장
        with open("received.webm", "wb") as f:
            f.write(contents)

        # ffmpeg를 이용
        # WebM → WAV 변환
        # 노이즈 제거할 때는 wav를 사용 (무손실 압축이라 편집하기 좋다고 함함)
        subprocess.run(["ffmpeg", "-y", "-i", "received.webm", "converted.wav"], check=True)

        # 노이즈 제거 코드
        data, rate = librosa.load("converted.wav", sr=None)
        reduced_noise = nr.reduce_noise(y=data, sr=rate)
        sf.write("clean.wav", reduced_noise, rate)

        return {"message": "업로드 및 소음 제거 완료"}
    
    #오류 발생시
    except Exception as e:
         # 서버 로그에 에러 메시지 출력
        print(f"Error in upload: {e}")
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")



#프론트엔드에서 소음 제거된 오디오 파일을 다운로드할 수 있게 전송해는 코드, /download 주소로 get 요청시 실행
@app.get("/download")
async def download_file():
    # clean.wav 위치 경로
    file_path = "clean.wav"

    # 파일이 실제로 존재하지 않으면 오류 메시지 반환
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="clean.wav file not found")
    
    # 파일이 있으면 클라이언트에게 파일을 전송
    return FileResponse(
        path=file_path,          # 보낼 파일 경로    
        media_type="audio/wav",  # 파일의 형태
        filename="processed.wav" # 다운로드될 때 보여질 파일 이름
    )

# 실행: uvicorn main:app --reload
