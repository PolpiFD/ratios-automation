from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pathlib import Path
import mimetypes
import uuid
import aiofiles

app = FastAPI(title="Ratios Automation Webhook")

UPLOAD_DIR = Path("Incoming")
UPLOAD_DIR.mkdir(exist_ok=True)

MAX_FILE_SIZE = 300 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".jpeg", ".png", ".jpg"}

@app.post("/webhook")
async def receive_document (
    client_id : str = Form(..., description="Customer's folder ID"),
    file : UploadFile = File(..., description="File for processing")
):
    """
    1. Vérifier le format et la taille.
    2. Sauvegarder le fichier sous un nom unique : client_id + uuid4.extension
    3. Renvoie un JSON pour récap.
    """
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (max 300mo)")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, f"Extension {suffix} non autorisée")
    
    mime = file.content_type or mimetypes.guess_type(file.filename)[0]

    new_name = f"={client_id}_{uuid.uuid4().hex}{suffix}"
    save_path = UPLOAD_DIR/new_name

    async with aiofiles.open(save_path, "wb") as buffer :
        await buffer.write(content)

    return {
        "message": "Fichier reçu",
        "original_name": file.filename,
        "stored_as": str(save_path),
        "mime_type": mime,
        "size_bytes": len(content)
    }

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)



