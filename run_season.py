import time
import random
import re
from bs4 import BeautifulSoup
from data_ingestion.fbref_scraper import FBrefScraper
from database.db_manager import DatabaseManager

print("--- STARTAR SÄSONGS-LOOP MED DYNAMISK SPELARSTATISTIK ---")
scraper = FBrefScraper()
db = DatabaseManager()

stats_url = "https://fbref.com/en/comps/9/Premier-League-Stats"
schedule_url = "https://fbref.com/en/comps/9/schedule/Premier-League-Scores-and-Fixtures"

# ==========================================
# 1. HÄMTA ÖVERGRIPANDE LIGASTATISTIK
# ==========================================
print(f"Hämtar övergripande ligastatistik från: {stats_url}")
stats_html = scraper._get_html(stats_url)

if stats_html:
    # FBref gömmer ofta huvudtabellen också, vi städar koden direkt!
    clean_stats_html = stats_html.replace('<!--', '').replace('-->', '')
    soup_stats = BeautifulSoup(clean_stats_html, 'lxml')
    
    standings_table = None
    # Leta efter tabellen som har 'squad' eller 'team' som kolumn
    for table in soup_stats.find_all('table', class_='stats_table'):
        if table.find(['th', 'td'], {'data-stat': re.compile(r'(squad|team)')}):
            standings_table = table
            break
            
    if standings_table:
        team_stats_list = []
        tbody = standings_table.find('tbody')
        if tbody:
            for row in tbody.find_all('tr'):
                # Fånga lagnamnet oavsett om det är en th- eller td-tagg
                team_cell = row.find(['th', 'td'], {'data-stat': re.compile(r'(squad|team)')})
                if not team_cell or not team_cell.text.strip():
                    continue
                
                team_name = team_cell.get_text(strip=True)
                
                def get_float(data_stat):
                    cell = row.find('td', {'data-stat': data_stat})
                    if cell:
                        val = cell.get_text(strip=True)
                        try:
                            return float(val) if val else 0.0
                        except ValueError:
                            return 0.0
                    return 0.0
                    
                def get_int(data_stat):
                    return int(get_float(data_stat))
                    
                team_data = {
                    "team_name": team_name,
                    "matches_played": get_int('games'),
                    "wins": get_int('wins'),
                    "draws": get_int('ties'),
                    "losses": get_int('losses'),
                    "goals_for": get_int('goals_for'),
                    "goals_against": get_int('goals_against'),
                    "points": get_int('points'),
                    "xg": get_float('xg_for'),
                    "xga": get_float('xg_against')
                }
                team_stats_list.append(team_data)
            
        if team_stats_list:
            db.save_season_stats(team_stats_list)
        else:
            print("Hittade tabellen, men kunde inte extrahera några lag.")
    else:
        print("Kunde inte hitta ligatabellen i HTML-koden.")

print("Väntar 15 sekunder för att undvika Cloudflare-blockering...")
time.sleep(15)

# ==========================================
# 2. HÄMTA MATCHSCHEMA OCH MATCHER
# ==========================================
print(f"Hämtar matchschema från: {schedule_url}")
schedule_html = scraper._get_html(schedule_url)

match_urls = []
if schedule_html:
    soup = BeautifulSoup(schedule_html, 'lxml')
    schedule_table = soup.find('table', id=re.compile('sched'))
    
    if schedule_table:
        for a in schedule_table.find_all('a', href=True):
            href = a['href']
            if '/matches/' in href:
                full_url = f"https://fbref.com{href}" if href.startswith('/') else href
                if full_url not in match_urls and re.search(r'/matches/[a-z0-9]+/', full_url):
                    match_urls.append(full_url)

print(f"Spindeln hittade {len(match_urls)} unika Premier League-matcher!")

for index, url in enumerate(match_urls, start=1):
    print(f"\n[{index}/{len(match_urls)}] Bearbetar match: {url}")
    
    match_id_match = re.search(r'/matches/([a-z0-9]+)/', url)
    match_id = match_id_match.group(1) if match_id_match else "unknown"
    
    html = scraper._get_html(url)
    
    if html:
        soup = BeautifulSoup(html, 'lxml')
        extra_stats = soup.find('div', id='team_stats_extra')
        main_stats = soup.find('div', id='team_stats')
        
        if extra_stats and main_stats:
            extra_text = extra_stats.get_text(separator=' | ', strip=True)
            main_text = main_stats.get_text(separator=' | ', strip=True)
            
            h1_tag = soup.find('h1')
            home_team, away_team = "Home", "Away"
            
            if h1_tag:
                title_text = h1_tag.get_text()
                if " vs. " in title_text:
                    split_teams = title_text.split(" vs. ")
                elif " vs " in title_text:
                    split_teams = title_text.split(" vs ")
                else:
                    split_teams = []

                if len(split_teams) == 2:
                    home_team = split_teams[0].strip()
                    raw_away = split_teams[1]
                    away_team = raw_away.split(" Match Report")[0].strip() if " Match Report" in raw_away else raw_away.strip()

            match_data = {
                "match_id": match_id,
                "home_team": home_team,
                "away_team": away_team
            }
            
            corners = re.search(r'(\d+)\s*\|\s*Corners\s*\|\s*(\d+)', extra_text)
            if corners:
                match_data['home_corners'] = int(corners.group(1))
                match_data['away_corners'] = int(corners.group(2))
                
            fouls = re.search(r'(\d+)\s*\|\s*Fouls\s*\|\s*(\d+)', extra_text)
            if fouls:
                match_data['home_fouls'] = int(fouls.group(1))
                match_data['away_fouls'] = int(fouls.group(2))

            sot_home = re.search(r'Shots on Target\s*\|\s*(\d+)', main_text)
            sot_away = re.search(r'—\s*(\d+)\s*of', main_text)
            if sot_home and sot_away:
                match_data['home_shots_on_target'] = int(sot_home.group(1))
                match_data['away_shots_on_target'] = int(sot_away.group(1))

            db.save_match(match_data)

            # --- DYNAMISK SPELARSTATISTIK ---
            clean_html = html.replace('<!--', '').replace('-->', '')
            dynamic_soup = BeautifulSoup(clean_html, 'lxml')
            all_stats_tables = dynamic_soup.find_all('table', class_='stats_table')
            
            match_players = {}
            
            for table in all_stats_tables:
                current_team = "Unknown"
                caption = table.find('caption')
                
                # Smartare textmatchning för lagnamn
                if caption:
                    cap_text = caption.get_text().lower().replace('&', 'and')
                    norm_home = home_team.lower().replace('&', 'and')
                    norm_away = away_team.lower().replace('&', 'and')
                    
                    if norm_home in cap_text:
                        current_team = home_team
                    elif norm_away in cap_text:
                        current_team = away_team
                    else:
                        # Fallback: Kolla enbart på första ordet (t.ex. "Newcastle")
                        home_first = norm_home.split()[0]
                        away_first = norm_away.split()[0]
                        if home_first in cap_text and away_first not in cap_text:
                            current_team = home_team
                        elif away_first in cap_text and home_first not in cap_text:
                            current_team = away_team
                
                if current_team == "Unknown":
                    continue

                tbody = table.find('tbody')
                if not tbody:
                    continue
                
                for row in tbody.find_all('tr'):
                    if row.get('class') and 'thead' in row.get('class'):
                        continue
                    
                    player_th = row.find('th', {"data-stat": "player"})
                    if not player_th or not player_th.text.strip():
                        continue
                    
                    player_name = player_th.text.strip()
                    
                    if player_name not in match_players:
                        match_players[player_name] = {
                            "match_id": match_id,
                            "team_name": current_team,
                            "player_name": player_name,
                            "nationality": "",
                            "position": "",
                            "age": "",
                            "minutes_played": 0,
                            "yellow_cards": 0,
                            "red_cards": 0,
                            "second_yellow": 0,
                            "fouls_committed": 0,
                            "fouls_drawn": 0,
                            "offsides": 0,
                            "crosses": 0,
                            "interceptions": 0,
                            "tackles_won": 0,
                            "own_goals": 0
                        }

                    def extract_stat(data_stat):
                        cell = row.find('td', {"data-stat": data_stat})
                        if cell:
                            val = cell.get_text(strip=True)
                            try:
                                return int(val) if val.isdigit() else val
                            except ValueError:
                                return 0
                        return None

                    nat = extract_stat('nationality')
                    if nat: match_players[player_name]['nationality'] = nat.split()[-1]
                    
                    pos = extract_stat('position')
                    if pos: match_players[player_name]['position'] = pos
                        
                    age = extract_stat('age')
                    if age: match_players[player_name]['age'] = age
                        
                    mins = extract_stat('minutes')
                    if mins is not None: match_players[player_name]['minutes_played'] = mins

                    stats_map = {
                        'cards_yellow': 'yellow_cards',
                        'cards_red': 'red_cards',
                        'cards_yellow_second': 'second_yellow',
                        'fouls': 'fouls_committed',
                        'fouled': 'fouls_drawn',
                        'offsides': 'offsides',
                        'crosses': 'crosses',
                        'interceptions': 'interceptions',
                        'tackles_won': 'tackles_won',
                        'own_goals': 'own_goals'
                    }

                    for fbref_stat, db_col in stats_map.items():
                        val = extract_stat(fbref_stat)
                        if val is not None:
                            match_players[player_name][db_col] = val

            all_player_stats = list(match_players.values())
            if all_player_stats:
                db.save_player_stats(all_player_stats)

        else:
            print(f"Kunde inte hitta statistik-block för match {match_id}")
    else:
        print(f"Kunde inte hämta HTML för match {match_id}")
            
    print("Väntar 15 sekunder för att undvika Cloudflare-blockering...")
    time.sleep(15)

print("\n--- SÄSONGS-LOOP AVSLUTAD ---")