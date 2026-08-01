import sys
import os
import time
import logging

# Säkerställ att vi kan importera från våra moduler
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_ingestion.football_api import FootballAPIClient
from database.database import DatabaseManager

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def extract_stat(stats_list, stat_name):
    """Hjälpfunktion för att plocka ut rätt värde ur API-Footballs JSON-struktur."""
    for stat in stats_list:
        if stat['type'] == stat_name:
            val = stat['value']
            # Vissa värden kommer som "55%", vi behöver rensa bort procenttecknet
            if isinstance(val, str) and '%' in val:
                return float(val.replace('%', ''))
            return float(val) if val is not None else 0.0
    return 0.0

def main():
    db = DatabaseManager()
    client = FootballAPIClient()
    
    # Premier League = 39. Vi börjar med förra säsongen (2025) för att bygga träningsdata.
    league_id = 39
    season = 2025
    
    print(f"--- Initierar historisk datahämtning (Liga: {league_id}, Säsong: {season}) ---")
    
    # 1. Hämta hela spelschemat (kostar bara 1 anrop)
    fixtures_data = client.get_fixtures_by_league(league_id, season)
    fixtures_to_save = []
    
    for item in fixtures_data:
        fix = item['fixture']
        teams = item['teams']
        fixtures_to_save.append((
            fix['id'], league_id, season, fix['date'], 
            teams['home']['name'], teams['away']['name'], fix['status']['short']
        ))
        
    if fixtures_to_save:
        db.save_fixtures_batch(fixtures_to_save)
        print(f"Uppdaterade spelschemat. Totalt {len(fixtures_to_save)} matcher registrerade.")
        
    # 2. Hitta matcher som vi saknar statistik för
    # Vi sätter limit till 80 för att lämna 20 anrop i marginal av dina 100 gratisanrop
    missing_fixtures = db.get_finished_fixtures_without_stats(limit=80)
    print(f"Hittade {len(missing_fixtures)} färdigspelade matcher som saknar djuplodande statistik.")
    
    if not missing_fixtures:
        print("All historisk data är redan nedladdad för denna liga!")
        db.close()
        return

    print(f"Laddar ner statistik för {len(missing_fixtures)} matcher. Detta tar en stund...")
    
    stats_to_insert = []
    
    # 3. Hämta statistiken match för match
    for idx, fixture_id in enumerate(missing_fixtures):
        time.sleep(1)  # Pausa i 1 sekund mellan anropen så vi inte blir blockade av API:et
        
        stat_data = client.get_fixture_statistics(fixture_id)
        
        if not stat_data or len(stat_data) < 2:
            continue # Statistiken kanske inte finns tillgänglig för denna match
            
        home_team = stat_data[0]
        away_team = stat_data[1]
        
        home_stats = home_team['statistics']
        away_stats = away_team['statistics']
        
        # Parsa Hemmalaget
        stats_to_insert.append((
            str(fixture_id), home_team['team']['name'], away_team['team']['name'], True,
            0, 0, # Mål (fylls i senare eller via annat API-anrop, vi fokuserar på händelser nu)
            extract_stat(home_stats, 'expected_goals'), extract_stat(away_stats, 'expected_goals'),
            extract_stat(home_stats, 'Ball Possession'),
            extract_stat(home_stats, 'Shots on Goal'), extract_stat(away_stats, 'Shots on Goal'),
            extract_stat(home_stats, 'Corner Kicks'), extract_stat(away_stats, 'Corner Kicks'),
            0, # Inkast saknas ofta här, sätter till 0 tills vidare
            extract_stat(home_stats, 'Yellow Cards'), extract_stat(home_stats, 'Red Cards')
        ))
        
        # Parsa Bortalaget
        stats_to_insert.append((
            str(fixture_id), away_team['team']['name'], home_team['team']['name'], False,
            0, 0,
            extract_stat(away_stats, 'expected_goals'), extract_stat(home_stats, 'expected_goals'),
            extract_stat(away_stats, 'Ball Possession'),
            extract_stat(away_stats, 'Shots on Goal'), extract_stat(home_stats, 'Shots on Goal'),
            extract_stat(away_stats, 'Corner Kicks'), extract_stat(home_stats, 'Corner Kicks'),
            0,
            extract_stat(away_stats, 'Yellow Cards'), extract_stat(away_stats, 'Red Cards')
        ))

        # Ge lite visuell feedback i terminalen
        if (idx + 1) % 10 == 0:
            print(f" -> Hämtat {idx + 1} av {len(missing_fixtures)} matcher...")

    # Spara allt i databasen
    if stats_to_insert:
        db.save_match_stats_batch(stats_to_insert)
        print(f"\nSparade statistik för {len(missing_fixtures)} matcher framgångsrikt!")
        
    db.close()

if __name__ == "__main__":
    main()