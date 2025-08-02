import asyncio
import logging
import re
import httpx
from datetime import datetime, timezone
from azure.data.tables.aio import TableClient
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv
load_dotenv()

from app.core.config import settings


from app.services.sharepoint import sharepoint_service

# Configuration
CLIENT_ID = settings.azure_client_id
TABLE_NAME = settings.azure_table_name
TABLE_URL = settings.azure_table_url
AUTH_KEY = settings.auth_key_supabase
URL_SUPABASE = settings.supabase_url_sync

# Nouvelles catégories SharePoint
SHAREPOINT_CATEGORIES = {
    "00 - A traiter",
    "01.1 - Créanciers", 
    "01.2 - Tickets",
    "02 - Débiteurs", 
    "03 - Banque"
}

# Pattern pour reconnaître les années (4 chiffres)
re_year = re.compile(r"^\d{4}$")


async def crawl_sharepoint_clients():
    """
    Crawle la structure SharePoint /Business/01 - Clients pour indexer tous les dossiers
    Structure attendue:
    /Business/01 - Clients/
    ├── [Nom Client]/
    │   ├── 2024/
    │   │   ├── 00 - A traiter/
    │   │   ├── 01.1 - Créanciers/
    │   │   ├── 01.2 - Tickets/
    │   │   ├── 02 - Débiteurs/
    │   │   └── 03 - Banque/
    """
    logging.info("Début synchronisation SharePoint")
    
    try:
        # Navigation vers le dossier clients
        
        main_folder = "Ratios Conseils Sàrl - Commun"
        main_content = await sharepoint_service.list_folder_contents(main_folder)
        
        # Chercher le dossier Business
        business_folder = None
        for item in main_content:
            if item.get("folder") and "business" in item["name"].lower():
                business_folder = item["name"]
                break
        
        if not business_folder:
            logging.error(f"Dossier 'Business' introuvable dans {main_folder}")
            return []
            
        business_path = f"{main_folder}/{business_folder}"
        business_content = await sharepoint_service.list_folder_contents(business_path)
        
        # Chercher le dossier clients
        clients_folder = None
        for item in business_content:
            if item.get("folder") and "client" in item["name"].lower():
                clients_folder = item["name"]
                break
                
        if not clients_folder:
            logging.error(f"Dossier 'Clients' introuvable dans {business_path}")
            return []
            
        clients_path = f"{business_path}/{clients_folder}"
        clients_folders = await sharepoint_service.list_folder_contents(clients_path)
        
        results = []
        
        for client_folder in clients_folders:
            if client_folder.get("folder") is None:  # Skip files, only folders
                continue
                
            client_name = client_folder["name"]
            client_folder_id = client_folder["id"]
            
            # Lister les années pour ce client
            client_path = f"{clients_path}/{client_name}"
            year_folders = await sharepoint_service.list_folder_contents(client_path)
            
            for year_folder in year_folders:
                if year_folder.get("folder") is None:
                    continue
                    
                year_name = year_folder["name"]
                
                # Vérifier que c'est bien une année (4 chiffres)
                if not re_year.match(year_name):
                    continue
                
                # Lister les catégories pour cette année
                year_path = f"{client_path}/{year_name}"
                category_folders = await sharepoint_service.list_folder_contents(year_path)
                
                for cat_folder in category_folders:
                    if cat_folder.get("folder") is None:
                        continue
                        
                    category_name = cat_folder["name"]
                    
                    # Vérifier que c'est une catégorie connue
                    if category_name not in SHAREPOINT_CATEGORIES:
                        continue
                    
                    # Construire le chemin complet pour l'upload
                    folder_path = f"{year_path}/{category_name}"
                    
                    result = {
                        "client": client_name,
                        "client_folder_id": client_folder_id,
                        "year": year_name,
                        "category": category_name,
                        "folder_path": folder_path,
                        "folder_id": cat_folder["id"]
                    }
                    
                    results.append(result)
        
        logging.info(f"Synchronisation terminée: {len(results)} dossiers indexés")
        return results
        
    except Exception as e:
        logging.error(f"Erreur lors du crawl SharePoint: {str(e)}")
        raise


async def upsert_sharepoint_index(rows):
    """
    Met à jour l'index Azure Table avec les données SharePoint
    """
    logging.info(f"Mise à jour de l'index: {len(rows)} entrées")
    
    credential = DefaultAzureCredential(managed_identity_client_id=CLIENT_ID)
    table = TableClient(endpoint=TABLE_URL, table_name=TABLE_NAME, credential=credential)

    async with table:
        # Créer la table si elle n'existe pas
        try:
            await table.create_table()
        except Exception:  # ResourceExistsError
            pass

        for r in rows:
            entity = {
                "PartitionKey": r["client"],
                "RowKey": f"{r['year']}_{r['category']}",
                "client_folder_id": r["client_folder_id"],
                "folder_id": r["folder_id"],  # Garder pour compatibilité
                "folder_path": r["folder_path"],  # Nouveau: chemin SharePoint complet
                "updated_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                "source": "sharepoint"  # Identifier la source
            }
            
            await table.upsert_entity(entity=entity, mode="merge")

    logging.info("Index Azure Table mis à jour avec succès")


async def send_to_supabase(folders):
    """
    Envoie les données des clients uniques vers Supabase
    """
    
    # Extraire les clients uniques avec leur ID SharePoint
    clients_map = {}
    for folder in folders:
        client_name = folder["client"]
        client_id = folder["client_folder_id"]
        if client_name not in clients_map:
            clients_map[client_name] = client_id
    
    # Préparer les données au format attendu
    items = [
        {"sharepoint_id": sharepoint_id, "nom": nom}
        for nom, sharepoint_id in clients_map.items()
    ]
    
    data = {"items": items}
    
    logging.info(f"📤 Envoi de {len(items)} clients vers Supabase")
    
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                URL_SUPABASE,
                json=data,
                headers={
                    "x-auth-key": AUTH_KEY,
                    "Content-Type": "application/json"
                }
            )
            response.raise_for_status()
            logging.info(f"✅ Données envoyées à Supabase avec succès: {response.status_code}")
            return response.json() if response.text else None
    except httpx.HTTPStatusError as e:
        logging.error(f"❌ Erreur HTTP lors de l'envoi à Supabase: {e.response.status_code} - {e.response.text}")
        raise
    except Exception as e:
        logging.error(f"❌ Erreur lors de l'envoi à Supabase: {str(e)}")
        raise


async def main():
    """Point d'entrée principal pour la synchronisation SharePoint"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(message)s"
    )
    
    # Réduire les logs verbeux des librairies externes
    logging.getLogger("azure").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("aiohttp").setLevel(logging.WARNING)
    
    try:
        # Crawl SharePoint
        folders = await crawl_sharepoint_clients()
        
        # Mise à jour de l'index
        await upsert_sharepoint_index(folders)
        
        # Envoi des données clients vers Supabase
        if folders:
            try:
                await send_to_supabase(folders)
            except Exception as e:
                logging.warning(f"⚠️ Échec de l'envoi à Supabase (non bloquant): {str(e)}")
                # On continue même si l'envoi à Supabase échoue
        
        logging.info(f"Synchronisation SharePoint terminée: {len(folders)} dossiers indexés")
        
    except Exception as e:
        logging.error(f"Erreur lors de la synchronisation: {str(e)}")
        raise


if __name__ == "__main__":
    asyncio.run(main())