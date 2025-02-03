from fastapi import FastAPI, HTTPException, File, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse
from cryptography.fernet import Fernet
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import gridfs
import io
from bson import ObjectId
import uvicorn

# Shared encryption key (pre-generated)
SHARED_KEY = b'sOYmV8-CebMYXZsNaXEJ-ZWBsBkuDzfGCLrG76SSodo='
fernet = Fernet(SHARED_KEY)

app = FastAPI()

# For simulation purposes we use an in-memory store instead of a database.
# In a real setup you might store encrypted files in a secure store.
# Here we simulate storage with a dictionary.
model_store = {}

@app.post("/client-upload/")
async def client_upload(file: UploadFile = File(...), client_id: str = "unknown"):
    """
    Receives an encrypted file upload from a client.
    The file content is decrypted and stored (here in a dict).
    """
    try:
        encrypted_bytes = await file.read()
        # Decrypt the incoming bytes
        decrypted_bytes = fernet.decrypt(encrypted_bytes)
        # For simulation, store the decrypted model file in memory keyed by client_id
        model_store[client_id] = decrypted_bytes
        return JSONResponse(content={"status": "success", "message": f"File received from {client_id}"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Central server upload error: {str(e)}")

@app.get("/client-download/{client_id}")
async def client_download(client_id: str):
    """
    Returns an encrypted file corresponding to a client's stored model.
    """
    try:
        if client_id not in model_store:
            raise HTTPException(status_code=404, detail="No model file found for this client.")
        file_bytes = model_store[client_id]
        # Encrypt before sending
        encrypted_bytes = fernet.encrypt(file_bytes)
        return StreamingResponse(io.BytesIO(encrypted_bytes),
                                 media_type="application/octet-stream",
                                 headers={"Content-Disposition": "attachment; filename=model.keras.enc"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Central server download error: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
