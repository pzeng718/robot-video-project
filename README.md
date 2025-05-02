Frontend (robot-video-ui):
1. cd robot-video-ui
2. npm install
3. npm run dev
4. Access http://localhost:5173/

Backend (robot-video-backend):
1. cd robot-video-backend
2. cp .env.example .env
3. replace openai api key in .env
4. pip install fastapi uvicorn python-multipart python-dotenv opencv-python openai requests
5. uvicorn main:app --reload

To use the app:
1. Access the website
2. Either enter url or upload video file
3. Click Preview Video to preview video uploaded
4. Click "Start Processing" to start the process
5. Once finished you should see success message, and the result will be in "Analysis Result" tab
