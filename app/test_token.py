import asyncio, os
from azure.identity.aio import DefaultAzureCredential
from dotenv import load_dotenv; load_dotenv(".env")

async def main():
    cred = DefaultAzureCredential()
    token = await cred.get_token("https://storage.azure.com/.default")
    print("Access token OK :", token.token[:40])

asyncio.run(main())
