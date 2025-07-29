import httpx
from typing import Optional, Dict, Any
from azure.identity.aio import ClientSecretCredential
from ..core.config import settings


class SharePointService:
    """Service pour interagir avec SharePoint via Microsoft Graph API"""
    
    def __init__(self):
        self.base_url = "https://graph.microsoft.com/v1.0"
        self.site_url = settings.sharepoint_site_url
        self.credential = ClientSecretCredential(
            tenant_id=settings.sharepoint_tenant_id,
            client_id=settings.sharepoint_client_id,
            client_secret=settings.sharepoint_client_secret
        )
        self._token_cache = None
        self._site_info = None
        self._drive_info = None
    
    async def get_access_token(self) -> str:
        """Obtient un token d'accès pour Microsoft Graph"""
        scopes = ["https://graph.microsoft.com/.default"]
        token = await self.credential.get_token(*scopes)
        return token.token
    
    async def get_site_info(self) -> Dict[str, Any]:
        """Récupère les informations du site SharePoint"""
        if self._site_info:
            return self._site_info
            
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            # Format: /sites/{hostname}:{serverRelativeUrl}
            url = f"{self.base_url}/sites/{self.site_url}"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            self._site_info = response.json()
            return self._site_info
    
    async def get_drive_info(self) -> Dict[str, Any]:
        """Récupère les informations du drive principal du site"""
        if self._drive_info:
            return self._drive_info
            
        site_info = await self.get_site_info()
        site_id = site_info["id"]
        
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            url = f"{self.base_url}/sites/{site_id}/drive"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            self._drive_info = response.json()
            return self._drive_info
    
    async def list_folder_contents(self, folder_path: str) -> list:
        """Liste le contenu d'un dossier SharePoint"""
        site_info = await self.get_site_info()
        drive_info = await self.get_drive_info()
        
        site_id = site_info["id"]
        drive_id = drive_info["id"]
        
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            # URL pour accéder au dossier par chemin
            if folder_path:
                url = f"{self.base_url}/sites/{site_id}/drives/{drive_id}/root:/{folder_path}:/children"
            else:
                # Racine du drive
                url = f"{self.base_url}/sites/{site_id}/drives/{drive_id}/root/children"
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            return response.json().get("value", [])
    
    async def upload_file_to_folder(self, file_bytes: bytes, filename: str, folder_path: str):
        """Upload un fichier dans un dossier SharePoint spécifique"""
        site_info = await self.get_site_info()
        drive_info = await self.get_drive_info()
        
        site_id = site_info["id"]
        drive_id = drive_info["id"]
        
        token = await self.get_access_token()
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/octet-stream"
        }
        
        async with httpx.AsyncClient(timeout=60) as client:
            # URL pour uploader le fichier
            full_path = f"{folder_path}/{filename}"
            url = f"{self.base_url}/sites/{site_id}/drives/{drive_id}/root:/{full_path}:/content"
            
            response = await client.put(url, headers=headers, content=file_bytes)
            response.raise_for_status()
            
            return response.json()
    
    async def get_folder_by_path(self, folder_path: str) -> Optional[Dict[str, Any]]:
        """Récupère les informations d'un dossier par son chemin"""
        site_info = await self.get_site_info()
        drive_info = await self.get_drive_info()
        
        site_id = site_info["id"]
        drive_id = drive_info["id"]
        
        token = await self.get_access_token()
        headers = {"Authorization": f"Bearer {token}"}
        
        async with httpx.AsyncClient(timeout=30) as client:
            try:
                if folder_path:
                    url = f"{self.base_url}/sites/{site_id}/drives/{drive_id}/root:/{folder_path}"
                else:
                    url = f"{self.base_url}/sites/{site_id}/drives/{drive_id}/root"
                response = await client.get(url, headers=headers)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 404:
                    return None
                raise


# Instance globale du service SharePoint
sharepoint_service = SharePointService()