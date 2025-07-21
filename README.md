## code get_graph_token (main)

async def main():
    headers = {"Authorization": f"Bearer {token}"}
    async with httpx.AsyncClient(
        base_url="https://graph.microsoft.com/v1.0",
        headers=headers,
        timeout=30
    ) as client:
        me_drive = await client.get("/me/drive")
        me_drive.raise_for_status()
        print("Mon drive ID : " + me_drive.json()["id"])