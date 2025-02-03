# clientB.py (change port and client_id)
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from cryptography.fernet import Fernet
import requests
import io
import uvicorn

SHARED_KEY = b'sOYmV8-CebMYXZsNaXEJ-ZWBsBkuDzfGCLrG76SSodo='
fernet = Fernet(SHARED_KEY)

app = FastAPI()
CENTRAL_SERVER_URL = "http://127.0.0.1:8000"

@app.post("/send-model/")
async def send_model(file: UploadFile = File(...)):
    try:
        file_bytes = await file.read()
        encrypted_bytes = fernet.encrypt(file_bytes)
        files = {"file": ("model.keras.enc", io.BytesIO(encrypted_bytes))}
        params = {"client_id": "clientB"}
        response = requests.post(f"{CENTRAL_SERVER_URL}/client-upload/", files=files, params=params)
        return JSONResponse(content={"status": "success", "central_response": response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Client upload error: {str(e)}")

@app.get("/get-model/")
async def get_model():
    try:
        response = requests.get(f"{CENTRAL_SERVER_URL}/client-download/clientB")
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        encrypted_bytes = response.content
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        return StreamingResponse(io.BytesIO(decrypted_bytes),
                                 media_type="application/octet-stream",
                                 headers={"Content-Disposition": "attachment; filename=model.keras"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Client download error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)
