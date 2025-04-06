from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
import gridfs
import io
import os
from bson import ObjectId

app = FastAPI()

# MongoDB Atlas Connection (Local Server Credentials)
MONGO_URI = "mongodb+srv://local_a:local_a@fl.yreoibi.mongodb.net/?retryWrites=true&w=majority&appName=FL"

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
    client.admin.command("ping")  # Test connection
    print("✅ Successfully connected to MongoDB (Local Server)!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# Select Database and GridFS
db = client["fl_model_db"]
fs = gridfs.GridFS(db)

@app.post("/upload/")
async def upload_local_model(username: str, file: UploadFile = File(...)):
    """
    Local Server: Uploads a local model file.
    """
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        # Save to GridFS with metadata
        file_id = fs.put(file_content, filename=file.filename, content_type="application/octet-stream",
                         metadata={"uploader": username, "file_type": "local"})

        return JSONResponse(content={"status": "success", "file_id": str(file_id)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.get("/download-global/")
async def download_global_model():
    """
    Local Server: Downloads the latest global model.
    """
    try:
        global_model = db.fs.files.find_one({"metadata.file_type": "global"})
        if not global_model:
            raise HTTPException(status_code=404, detail="No global model found.")

        file_data = fs.get(global_model["_id"])
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_data.filename}"}
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="Global model not found.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving global model: {str(e)}")