import logging
import traceback
from ..services.ocr import file_ocr
from ..services.llm import categorisation
from ..services.classement import classer
from jobs.get_graph_token import get_graph_token

async def process_document_async(blob_url: str, client_id: str, client_name: str, file_name: str):
    try:
        logging.info(f"🔄 Début traitement: {file_name}")

        #OCR première page
        ocr_json = file_ocr(blob_url)
        logging.info(f"✅ OCR terminé: {file_name}")

        # Classification LLM
        category = categorisation(ocr_json, client_name)
        logging.info(f"Année détectée : {category.year}")
        row_key = f"{category.year}_{category.name}"
        logging.info(f"🏷️ Catégorie détectée: {row_key}")

        # Classement dans le OneDrive
        classement = await classer(
            blob_url,
            file_name,
            client_id,
            row_key,
            get_graph_token()
        )

        logging.info(f"✅ Document classé: {file_name} → {row_key}")

    except Exception as e:
        logging.error(f"❌ Erreur traitement {file_name}: {str(e)}")
        logging.error(f"Stacktrace: {traceback.format_exc()}")