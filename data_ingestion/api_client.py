import os
import requests
import logging
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class OddsAPIClient:
    BASE_URL = "https://api.the-odds-api.com/v4/sports"

    def __init__(self):
        load_dotenv()
        self.api_key = os.getenv("ODDS_API_KEY")
        if not self.api_key:
            raise ValueError("API-nyckel saknas i .env-filen!")

    def get_odds(self, sport="soccer_epl", regions="eu", markets="h2h,totals"):
        """
        Hämtar aktuella odds.
        sport: 'soccer_epl' (Premier League) eller 'soccer_spain_la_liga' (La Liga)
        """
        url = f"{self.BASE_URL}/{sport}/odds"
        params = {
            "apiKey": self.api_key,
            "regions": regions,
            "markets": markets,
            "oddsFormat": "decimal"
        }

        try:
            logging.info(f"Hämtar odds för {sport}...")
            response = requests.get(url, params=params)
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            logging.error(f"API-fel: {e}")
            return None