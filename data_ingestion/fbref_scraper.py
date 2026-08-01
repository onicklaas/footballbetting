from playwright.sync_api import sync_playwright
import pandas as pd
import time
import logging
from bs4 import BeautifulSoup
from io import StringIO

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

class FBrefScraper:
    """
    Web scraper för FBref.com som använder en riktig (headless) Chromium-webbläsare
    för att komma förbi Cloudflares anti-bot-skydd.
    """
    def __init__(self):
        pass

    def _get_html(self, url):
        """Hämtar HTML via din riktiga Chrome-webbläsare."""
        html = ""
        with sync_playwright() as p:
            browser = p.chromium.launch(
                headless=False,
                channel="chrome",
                args=['--disable-blink-features=AutomationControlled']
            )
            context = browser.new_context()
            page = context.new_page()
            
            try:
                logging.info(f"Navigerar direkt till {url}...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                # Om molnet dyker upp hinner du klicka, annars rullar det på direkt
                logging.info("Väntar 12 sekunder (lös eventuell CAPTCHA manuellt om den dyker upp)...")
                page.wait_for_timeout(12000) 
                
                html = page.content()
            except Exception as e:
                logging.error(f"Ett Playwright-fel uppstod: {e}")
            finally:
                browser.close()
                
        return html

    def get_match_stats(self, match_url):
        """Hämtar tabeller från FBref."""
        html = self._get_html(match_url)
        if not html:
            return None

        soup = BeautifulSoup(html, 'lxml')
        
        try:
            tables = pd.read_html(StringIO(str(soup)))
            logging.info(f"Hittade {len(tables)} HTML-tabeller på sidan.")
            return tables
        except ValueError:
            logging.error("Hittade inga tabeller.")
            return None