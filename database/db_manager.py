import mysql.connector
from mysql.connector import Error
import logging

class DatabaseManager:
    def __init__(self):
        self.host = "127.0.0.1"
        self.database = "football_data"
        self.user = "root"
        self.password = "Nicklas" # Byt ut mot ditt MySQL root-lösenord!

    def connect(self):
        """Skapar och returnerar en anslutning till databasen."""
        try:
            connection = mysql.connector.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password
            )
            return connection
        except Error as e:
            logging.error(f"Kunde inte ansluta till MySQL: {e}")
            return None

    def save_match(self, match_data):
        """Sparar en tvättad match-dictionary till databasen."""
        connection = self.connect()
        if connection is None:
            return

        cursor = connection.cursor()
        
        # SQL-fråga med INSERT IGNORE så vi inte kraschar om samma match_id redan finns
        query = """
            INSERT IGNORE INTO match_stats 
            (match_id, home_team, away_team, home_corners, away_corners, home_fouls, away_fouls, home_shots_on_target, away_shots_on_target)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        values = (
            match_data.get('match_id'),
            match_data.get('home_team'),
            match_data.get('away_team'),
            match_data.get('home_corners'),
            match_data.get('away_corners'),
            match_data.get('home_fouls'),
            match_data.get('away_fouls'),
            match_data.get('home_shots_on_target'),
            match_data.get('away_shots_on_target')
        )

        try:
            cursor.execute(query, values)
            connection.commit()
            print(f"--> Sparade match {match_data.get('match_id')} ({match_data.get('home_team')} vs {match_data.get('away_team')}) till databasen!")
        except Error as e:
            logging.error(f"Fel vid sparande till databasen: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()