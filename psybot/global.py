from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import JSONResponse, StreamingResponse
from pymongo import MongoClient
from pymongo.server_api import ServerApi
import gridfs
import io
import os
from bson import ObjectId

app = FastAPI()

# MongoDB Atlas Connection
MONGO_URI = "mongodb+srv://global_server:global_server@fl.yreoibi.mongodb.net/?retryWrites=true&w=majority&appName=FL"

try:
    client = MongoClient(MONGO_URI, server_api=ServerApi("1"))
    client.admin.command("ping")
    print("✅ Successfully connected to MongoDB (Global Server)!")
except Exception as e:
    print(f"❌ MongoDB Connection Error: {e}")

# Select Database and GridFS
db = client["fl_model_db"]
fs = gridfs.GridFS(db)

@app.get("/total-users/")
async def get_total_users():
    try:
        users = db.fs.files.distinct("metadata.uploader")
        return JSONResponse(content={"total_users": len(users), "users": users})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching users: {str(e)}")
    
@app.post("/upload/")
async def upload_file(username: str, file: UploadFile = File(...)):
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        file_id = fs.put(file_content, filename=file.filename, content_type="application/octet-stream",
                         metadata={"uploader": username, "file_type": "local"})
        return JSONResponse(content={"status": "success", "file_id": str(file_id)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading file: {str(e)}")

@app.post("/upload-global/")
async def upload_global_model(username: str, file: UploadFile = File(...)):
    """
    Deletes the current global model (if it exists) and uploads a new one.
    """
    try:
        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        # Delete the existing global model
        existing_global = db.fs.files.find_one({"metadata.file_type": "global"})
        if existing_global:
            fs.delete(existing_global["_id"])
        
        # Upload the new global model
        file_id = fs.put(file_content, filename=file.filename, content_type="application/octet-stream",
                         metadata={"uploader": username, "file_type": "global"})
        
        return JSONResponse(content={"status": "success", "file_id": str(file_id)})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error uploading global model: {str(e)}")
    
@app.get("/list-files/")
async def list_user_files(username: str):
    try:
        files = []
        for file in db.fs.files.find({"metadata.uploader": username}):
            files.append({
                "_id": str(file["_id"]),
                "filename": file["filename"],
                "uploader": file["metadata"]["uploader"],
                "file_type": file["metadata"]["file_type"]
            })
        return JSONResponse(content={"files": files})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing files: {str(e)}")

@app.get("/download/")
async def download_file(file_id: str):
    try:
        file_data = fs.get(ObjectId(file_id))
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_data.filename}"}
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="File not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving file: {str(e)}")

@app.get("/download-global/")
async def download_global_model():
    try:
        global_model = db.fs.files.find_one({"metadata.file_type": "global"}, sort=[("uploadDate", -1)])
        if not global_model:
            raise HTTPException(status_code=404, detail="Global model not found.")
        
        file_data = fs.get(global_model["_id"])
        return StreamingResponse(
            io.BytesIO(file_data.read()),
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={file_data.filename}"}
        )
    except gridfs.errors.NoFile:
        raise HTTPException(status_code=404, detail="Global model file not found")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving global model: {str(e)}")
    
@app.delete("/delete-global/")
async def delete_global_model():
    """
    Deletes the file with file_type as 'global'.
    """
    try:
        global_model = db.fs.files.find_one({"metadata.file_type": "global"})
        if not global_model:
            raise HTTPException(status_code=404, detail="Global model not found.")
        
        fs.delete(global_model["_id"])
        return JSONResponse(content={"status": "success", "message": "Global model deleted successfully."})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting global model: {str(e)}")

