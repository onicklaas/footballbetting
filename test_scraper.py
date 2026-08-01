from data_ingestion.fbref_scraper import FBrefScraper
from database.db_manager import DatabaseManager
from bs4 import BeautifulSoup
import re

print("--- STARTAR SKRIPTET ---")
scraper = FBrefScraper()
db = DatabaseManager()

test_match_url = "https://fbref.com/en/matches/c0e3342a/Arsenal-Wolverhampton-Wanderers-August-17-2024-Premier-League"

match_id_match = re.search(r'/matches/([a-z0-9]+)/', test_match_url)
match_id = match_id_match.group(1) if match_id_match else "unknown"

print(f"Hämtar källkoden för match {match_id}...")
html = scraper._get_html(test_match_url)

if html:
    soup = BeautifulSoup(html, 'lxml')
    
    extra_stats = soup.find('div', id='team_stats_extra')
    main_stats = soup.find('div', id='team_stats')
    
    if extra_stats and main_stats:
        extra_text = extra_stats.get_text(separator=' | ', strip=True)
        main_text = main_stats.get_text(separator=' | ', strip=True)
        
        match_data = {
            "match_id": match_id,
            "home_team": "Arsenal",
            "away_team": "Wolves"
        }
        
        # 1. Hörnor
        corners = re.search(r'(\d+)\s*\|\s*Corners\s*\|\s*(\d+)', extra_text)
        if corners:
            match_data['home_corners'] = int(corners.group(1))
            match_data['away_corners'] = int(corners.group(2))
            
        # 2. Regelbrott
        fouls = re.search(r'(\d+)\s*\|\s*Fouls\s*\|\s*(\d+)', extra_text)
        if fouls:
            match_data['home_fouls'] = int(fouls.group(1))
            match_data['away_fouls'] = int(fouls.group(2))
            
        # 3. Skott på mål
        sot_home = re.search(r'Shots on Target\s*\|\s*(\d+)', main_text)
        sot_away = re.search(r'—\s*(\d+)\s*of', main_text)
        
        if sot_home and sot_away:
            match_data['home_shots_on_target'] = int(sot_home.group(1))
            match_data['away_shots_on_target'] = int(sot_away.group(1))

        print("\n>>> SPARAR TILL MYSQL DATABASEN <<<")
        db.save_match(match_data)
            
    else:
        print("Kunde inte hitta statistik-blocken på sidan.")
else:
    print("\nMisslyckades att hämta HTML.")

print("--- SKRIPTET AVSLUTAT ---")