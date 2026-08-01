import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database import DatabaseManager

def main():
    db = DatabaseManager()
    
    # 1. Hämta alla matcher från databasen
    matches = db.get_all_matches()
    if not matches:
        print("Databasen är tom. Kör main.py först för att hämta data.")
        db.close()
        return

    print("Hittade följande kommande matcher:\n")
    for i, (match_id, home, away, commence) in enumerate(matches):
        print(f"{i+1}. {home} vs {away} (Start: {commence})")
        
    # 2. Välj den första matchen för att demonstrera funktionen
    first_match_id = matches[0][0]
    match_name = f"{matches[0][1]} vs {matches[0][2]}"
    
    # The Odds API använder nycklar som 'bet365', 'unibet', 'pinnacle', 'nordicbet'
    # Vi testar med 'unibet' som standard.
    bookmaker = 'unibet' 
    market = 'h2h'
    
    print(f"\n--- Oddsutveckling för {match_name} ---")
    print(f"Bookmaker: {bookmaker.capitalize()} | Marknad: {market.upper()}\n")
    
    timeline = db.get_odds_timeline(first_match_id, bookmaker, market)
    
    if not timeline:
        print(f"Hittade inga odds för {bookmaker}. Det kan bero på att denna bookmaker inte erbjöd odds för matchen just nu.")
        print("Tips: Öppna din SQLite-databas (t.ex. med DB Browser for SQLite) för att se vilka bookmakers som finns sparade.")
    else:
        # Skriv ut en snygg tidslinje
        current_selection = ""
        for selection, odds, update_time in timeline:
            # Skapa ett visuellt mellanrum när vi byter från t.ex. Hemmalag till Oavgjort
            if selection != current_selection:
                print(f"\nUtfall: {selection}")
                current_selection = selection
                
            print(f"  -> Odds: {odds:<5} | Tid: {update_time}")
            
    db.close()

if __name__ == "__main__":
    main()