import sqlite3
import logging

class DatabaseManager:
    def __init__(self, db_name="betting_data.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.setup_tables()
        
    def get_all_matches(self):
        """Hämtar alla sparade matcher sorterade på starttid."""
        sql = "SELECT id, home_team, away_team, commence_time FROM matches ORDER BY commence_time ASC"
        self.cursor.execute(sql)
        return self.cursor.fetchall()

    def get_odds_timeline(self, match_id, bookmaker, market="h2h"):
        """
        Hämtar tidslinjen för odds på en specifik match och bookmaker.
        Vi sorterar på utfall (selection) och tidpunkt för att se rörelsen.
        """
        sql = '''
            SELECT selection, odds, bookmaker_update_time 
            FROM odds_history 
            WHERE match_id = ? AND bookmaker = ? AND market = ?
            ORDER BY selection ASC, bookmaker_update_time ASC
        '''
        self.cursor.execute(sql, (match_id, bookmaker, market))
        return self.cursor.fetchall()

    def setup_tables(self):
        # Tabell för matcher (INSERT OR IGNORE används senare för att undvika dubbletter)
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id TEXT PRIMARY KEY,
                sport_key TEXT,
                home_team TEXT,
                away_team TEXT,
                commence_time TEXT
            )
        ''')

        # Lade till bookmaker_update_time för att veta exakt när oddset sattes hos bolaget
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS odds_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                match_id TEXT,
                bookmaker TEXT,
                market TEXT,
                selection TEXT,
                odds REAL,
                bookmaker_update_time TEXT,
                inserted_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS match_stats (
                match_id TEXT,
                team TEXT,
                opponent TEXT,
                is_home BOOLEAN,
                goals_scored INTEGER,
                goals_conceded INTEGER,
                xg REAL,
                xga REAL,
                possession REAL,
                shots_on_target INTEGER,
                shots_on_target_conceded INTEGER,
                corners INTEGER,
                corners_conceded INTEGER,
                throw_ins INTEGER,
                yellow_cards INTEGER,
                red_cards INTEGER,
                PRIMARY KEY (match_id, team),
                FOREIGN KEY (match_id) REFERENCES matches (id)
            )
        ''')
        self.conn.commit()
        logging.info("Databas och tabeller är initierade.")

    def save_matches_batch(self, match_data_list):
        """Sparar en lista med matcher. Använder IGNORE för att inte krascha om matchen redan finns."""
        sql = '''INSERT OR IGNORE INTO matches 
                 (id, sport_key, home_team, away_team, commence_time) 
                 VALUES (?, ?, ?, ?, ?)'''
        self.cursor.executemany(sql, match_data_list)
        self.conn.commit()
        logging.info(f"Sparade {self.cursor.rowcount} nya matcher till databasen.")

    def save_odds_batch(self, odds_data_list):
        """Sparar historik för odds i en enda stor batch."""
        sql = '''INSERT INTO odds_history 
                 (match_id, bookmaker, market, selection, odds, bookmaker_update_time) 
                 VALUES (?, ?, ?, ?, ?, ?)'''
        self.cursor.executemany(sql, odds_data_list)
        self.conn.commit()
        logging.info(f"Sparade {len(odds_data_list)} odds-uppdateringar till historiken.")

    def close(self):
        self.conn.close()