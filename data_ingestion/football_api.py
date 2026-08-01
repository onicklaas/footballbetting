import os
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class FootballAPIClient:
    """
    Klient för att hämta djupgående matchstatistik via API-Sports (API-Football).
    """
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("API_SPORTS_KEY")
        if not self.api_key:
            raise ValueError("API_SPORTS_KEY saknas i .env-filen!")
        
        # API-Sports kräver att nyckeln skickas i headern
        self.headers = {
            'x-apisports-key': self.api_key
        }

    def get_account_status(self):
        """
        Hämtar status för vårt konto. 
        Perfekt för att hålla koll på hur många av våra 100 anrop vi har kvar idag.
        """
        url = f"{self.BASE_URL}/status"
        
        try:
            logging.info("Kontrollerar API-Sports anslutning och token-saldo...")
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"Kunde inte ansluta till API-Sports: {e}")
            return None