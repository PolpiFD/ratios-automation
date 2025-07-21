from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from pathlib import Path
import mimetypes
import uuid
import asyncio

from dotenv import load_dotenv
load_dotenv()

from .storage import upload_file, make_read_sas_url
from .ocr import file_ocr
from .llm import categorisation
from .classement import classer
from jobs.get_graph_token import get_graph_token

app = FastAPI(title="Ratios Automation Webhook")


MAX_FILE_SIZE = 300 * 1024 * 1024
ALLOWED_EXT = {".pdf", ".jpeg", ".png", ".jpg"}

@app.post("/webhook")
async def receive_document (
    client_name : str = Form(..., description="Client's name"),
    client_id : str = Form(..., description="Customer's folder ID"),
    file : UploadFile = File(..., description="File for processing")
):
    print(f"Client id réceptionné via le webhook: {client_id}")
    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(413, "Fichier trop volumineux (max 300mo)")
    suffix = Path(file.filename).suffix.lower()
    if suffix not in ALLOWED_EXT:
        raise HTTPException(400, f"Extension {suffix} non autorisée")
    
    mime = file.content_type or mimetypes.guess_type(file.filename)[0]
    new_name = f"{client_id}_{uuid.uuid4().hex}{suffix}"
    blob_url = await upload_file(content, new_name, mime)
    print(f"Url du document stocké {blob_url}")

    sas_url = make_read_sas_url("file-automation-ratios", new_name)
    print(sas_url)
    asyncio.create_task(process_document_ocr(sas_url, client_id, client_name, file.filename))

    return {
        "status": "accepted",
        "blob_url": blob_url,
        "orginal_name": file.filename,
        "size_bytes": len(content)
    }
# --------------------------------------------------------------------------
async def process_document_ocr(blob_url:str, client_id: str, client_name: str, file_name: str):
    ocr_json = await file_ocr(blob_url)
    category = await categorisation(ocr_json, client_name)
    row_key = f"{category.anne}_{category.categorie}"
    print(row_key)
    classement = await classer (
        blob_url, 
        filename=file_name, 
        client_folder_id=client_id, 
        categorie=row_key, 
        graph_token=get_graph_token()
    )

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

