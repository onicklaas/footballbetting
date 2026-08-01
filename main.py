from data_ingestion.api_client import OddsAPIClient
from database.database import DatabaseManager

def process_api_data(api_data, db):
    """
    Kärnlogiken för att packa upp JSON från The Odds API
    och omvandla det till listor som databasen kan ta emot via executemany.
    """
    matches_to_insert = []
    odds_to_insert = []

    for match in api_data:
        # 1. Bygg data för matchen
        matches_to_insert.append((
            match['id'],
            match['sport_key'],
            match['home_team'],
            match['away_team'],
            match['commence_time']
        ))

        # 2. Dyk ner i bookmakers för denna match
        for bookmaker in match.get('bookmakers', []):
            bm_key = bookmaker['key']
            bm_update = bookmaker['last_update']

            # 3. Dyk ner i marknader (t.ex. 'h2h', 'totals')
            for market in bookmaker.get('markets', []):
                market_key = market['key']

                # 4. Hämta de faktiska utfallen och oddsen
                for outcome in market.get('outcomes', []):
                    odds_to_insert.append((
                        match['id'],
                        bm_key,
                        market_key,
                        outcome['name'],       # t.ex. "Arsenal", "Chelsea", eller "Draw"
                        outcome['price'],      # Det faktiska decimaloddset
                        bm_update
                    ))

    # Skicka batchen till databasen
    if matches_to_insert:
        db.save_matches_batch(matches_to_insert)
    if odds_to_insert:
        db.save_odds_batch(odds_to_insert)

def main():
    print("Startar bettinganalysverktyget v1...")
    
    db = DatabaseManager()
    client = OddsAPIClient()
    
    # En lista med de ligor vi vill övervaka. 
    # Detta gör det extremt enkelt att lägga till Serie A eller Allsvenskan i framtiden.
    leagues = ["soccer_epl", "soccer_spain_la_liga"]
    
    for league in leagues:
        print(f"\nHämtar data för {league}...")
        api_data = client.get_odds(sport=league)
        
        if api_data:
            print(f"Hittade {len(api_data)} matcher. Processar data...")
            process_api_data(api_data, db)
        else:
            print(f"Varning: Kunde inte hämta data för {league}.")
    
    db.close()
    print("\nKörning slutförd!")

if __name__ == "__main__":
    main()