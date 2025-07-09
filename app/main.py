from fastapi import FastAPI, UploadFile, File, Form, HTTPException, BackgroundTasks
from pathlib import Path
import mimetypes
import uuid
import aiofiles
from storage import upload_file

from dotenv import load_dotenv
load_dotenv()

app = FastAPI(title="Ratios Automation Webhook")


MAX_FILE_SIZE = 300 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".jpeg", ".png", ".jpg"}

@app.post("/webhook")
async def receive_document (
    background_tasks: BackgroundTasks, #Pour déclencher l'OCR en tâche de fond
    client_id : str = Form(..., description="Customer's folder ID"),
    file : UploadFile = File(..., description="File for processing")
):

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (max 300mo)")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, f"Extension {suffix} non autorisée")
    
    mime = file.content_type or mimetypes.guess_type(file.filename)[0]
    new_name = f"={client_id}_{uuid.uuid4().hex}{suffix}"
    blob_url = await upload_file(content, new_name, mime)

    return {
        "status": "accepted",
        "blob_url": blob_url,
        "orginal_name": file.filename,
        "size_bytes": len(content)
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)



