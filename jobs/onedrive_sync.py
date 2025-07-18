import asyncio, os, httpx, logging, re
from datetime import datetime
from azure.data.tables.aio import TableClient
from azure.identity.aio import DefaultAzureCredential
from get_graph_token import get_graph_token

# --------- VARIABLES -------------
CLIENT_ID = os.getenv("AZURE_CLIENT_ID")
DRIVE_ID = os.getenv("DRIVE_ID")
TABLE_NAME = "ClientFolderIndex"
TABLE_URL = "https://storageratios.table.core.windows.net"
ACCOUNT_NAME = os.getenv("AZURE_STORAGE_ACCOUNT_NAME")
# --------- VARIABLES -------------

# ------------- RULES ---------------
CATEGORIES = {
    "00 - A traiter", "01 - Créanciers", "02 - Débiteurs", "03 - Banque",
    "04 - RH", "05 - Cockpit", "06 - Comptabilité Générale", "07 - Stratégie",
    "08 - TVA", "09 - Bouclement"
}

re_year = re.compile(r"^\d{4}$")

# ------------- RULES ---------------

async def list_children(graph: httpx.AsyncClient, item_id: str):
    """Retourne la liste des enfants d'un item OneDrive."""
    resp = await graph.get(f"/drives/{DRIVE_ID}/items/{item_id}/children")
    resp.raise_for_status()
    return resp.json()["value"]

async def crawl_drive(token):
    print("OK CRAWL")
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url="https://graph.microsoft.com/v1.0",
        headers=headers, timeout=30
    ) as graph:
        #1) trouve "01 - Clients" à la racine
        root_children = await list_children(graph, "root")
        clients_item = next(
            it for it in root_children
            if it["name"].strip().startswith("01") and "Client" in it["name"]
        )
        clients_id = clients_item["id"]
        print(clients_id)

        #2) chaque client
        for cli in await list_children(graph, clients_id):
            cli_name = cli["name"]
            cli_id = cli["id"]
            print(cli_name)

            #3) Chaque sous-dossier Année (4 chiffres)
            for yr in await list_children(graph, cli_id):
                if not re_year.match(yr["name"]):
                    continue
                print(yr["name"])
                yr_name = yr["name"]
                yr_id = yr["id"]

                #4) Chaque sous-dossier par année
                for cat in await list_children(graph, yr_id):
                    if cat["name"] not in CATEGORIES:
                        continue
                    yield {
                        "client": cli_name,
                        "client_folder_id": cli_id,
                        "year": yr_name,
                        "category": cat["name"],
                        "folder_id": cat["id"],
                    }

async def upsert_rows(rows):
    """
    Upsert chaque ligne individuellement (plus simple, peu d'entrées).
    Si tu as des milliers de lignes, on pourra grouper par PartitionKey + batch 100.
    """
    credential = DefaultAzureCredential(managed_identity_client_id=CLIENT_ID)
    table = TableClient(endpoint=TABLE_URL, table_name=TABLE_NAME, credential=credential)

    async with table:
        # crée la table si elle n'existe pas (ignore l'erreur si elle existe)
        try:
            await table.create_table()
        except Exception:  # ResourceExistsError
            pass

        for r in rows:
            entity = {
                "PartitionKey": r["client"],
                "RowKey": f"{r['year']}#{r['category']}",
                "client_folder_id": r["client_folder_id"],
                "folder_id": r["folder_id"],
                "updated_utc": datetime.utcnow().isoformat(timespec="seconds"),
            }
            # mode="merge" -> met à jour colonnes, conserve autres
            await table.upsert_entity(entity=entity, mode="merge")


async def main():
    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    token = get_graph_token()
    rows = [r async for r in crawl_drive(token)]
    print(rows)
    await upsert_rows(rows)
    logging.info("sync OK - %d lignes", len(rows))
if __name__ == "__main__":
    asyncio.run(main())