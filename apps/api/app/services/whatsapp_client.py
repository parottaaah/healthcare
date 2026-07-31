import httpx
from fastapi import HTTPException
from app.core.config import settings

class WhatsAppClient:
    def __init__(self):
        self.base_url = "https://graph.facebook.com/v18.0"
        self.phone_number_id = settings.whatsapp_phone_number_id
        self.access_token = settings.whatsapp_access_token
        
    def _get_headers(self):
        return {
            "Authorization": f"Bearer {self.access_token}",
            "Content-Type": "application/json"
        }

    def send_text_message(self, to: str, body: str) -> dict:
        """Sends a plain text message via WhatsApp Cloud API."""
        if not self.phone_number_id or not self.access_token:
            print("Warning: WhatsApp credentials not configured. Skipping message send.")
            return {}
            
        url = f"{self.base_url}/{self.phone_number_id}/messages"
        payload = {
            "messaging_product": "whatsapp",
            "to": to,
            "type": "text",
            "text": {"body": body}
        }
        
        with httpx.Client() as client:
            response = client.post(url, headers=self._get_headers(), json=payload)
            response.raise_for_status()
            return response.json()

    def download_media(self, media_id: str) -> bytes:
        """Resolves a media ID and downloads its content."""
        if not self.access_token:
            raise ValueError("WhatsApp credentials not configured")
            
        url = f"{self.base_url}/{media_id}"
        with httpx.Client() as client:
            # 1. Get the media URL
            response = client.get(url, headers=self._get_headers())
            response.raise_for_status()
            media_url = response.json().get("url")
            
            if not media_url:
                raise ValueError("Could not resolve media URL")
                
            # 2. Download the actual media
            media_response = client.get(media_url, headers=self._get_headers())
            media_response.raise_for_status()
            return media_response.content

whatsapp_client = WhatsAppClient()
