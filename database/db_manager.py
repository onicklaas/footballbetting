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
        
        query = """
            INSERT IGNORE INTO match_stats 
            (match_id, home_team, away_team, home_corners, away_corners, home_fouls, away_fouls, 
             home_shots_on_target, away_shots_on_target, home_yellow_cards, away_yellow_cards, 
             home_red_cards, away_red_cards, home_possession, away_possession)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
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
            match_data.get('away_shots_on_target'),
            match_data.get('home_yellow_cards'),
            match_data.get('away_yellow_cards'),
            match_data.get('home_red_cards'),
            match_data.get('away_red_cards'),
            match_data.get('home_possession'),
            match_data.get('away_possession')
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

    def save_player_stats(self, player_list):
        """Sparar en lista med spelares matchstatistik till databasen."""
        connection = self.connect()
        if connection is None:
            return

        cursor = connection.cursor()
        
        query = """
            INSERT IGNORE INTO player_match_stats 
            (match_id, team_name, player_name, nationality, position, age, minutes_played, 
             yellow_cards, red_cards, second_yellow, fouls_committed, fouls_drawn, 
             offsides, crosses, interceptions, tackles_won, own_goals)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        
        for p in player_list:
            values = (
                p.get('match_id'),
                p.get('team_name'),
                p.get('player_name'),
                p.get('nationality'),
                p.get('position'),
                p.get('age'),
                p.get('minutes_played'),
                p.get('yellow_cards'),
                p.get('red_cards'),
                p.get('second_yellow'),
                p.get('fouls_committed'),
                p.get('fouls_drawn'),
                p.get('offsides'),
                p.get('crosses'),
                p.get('interceptions'),
                p.get('tackles_won'),
                p.get('own_goals')
            )
            try:
                cursor.execute(query, values)
            except Error as e:
                logging.error(f"Fel vid sparande av spelarstatistik för {p.get('player_name')}: {e}")

        try:
            connection.commit()
            print(f"--> Sparade spelarstatistik ({len(player_list)} spelare) för matchen.")
        except Error as e:
            logging.error(f"Fel vid commit av spelarstatistik: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()

    def save_season_stats(self, team_stats_list):
        """Sparar övergripande ligastatistik per lag."""
        connection = self.connect()
        if connection is None:
            return

        cursor = connection.cursor()
        
        # ON DUPLICATE KEY UPDATE gör att poängen uppdateras om du kör skriptet flera gånger
        query = """
            INSERT INTO season_team_stats 
            (team_name, matches_played, wins, draws, losses, goals_for, goals_against, points, xg, xga)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE 
            matches_played = VALUES(matches_played), wins = VALUES(wins), draws = VALUES(draws), 
            losses = VALUES(losses), goals_for = VALUES(goals_for), goals_against = VALUES(goals_against), 
            points = VALUES(points), xg = VALUES(xg), xga = VALUES(xga)
        """
        
        for t in team_stats_list:
            values = (
                t.get('team_name'), t.get('matches_played'), t.get('wins'), t.get('draws'), 
                t.get('losses'), t.get('goals_for'), t.get('goals_against'), t.get('points'), 
                t.get('xg'), t.get('xga')
            )
            try:
                cursor.execute(query, values)
            except Error as e:
                logging.error(f"Fel vid sparande av lagstatistik för {t.get('team_name')}: {e}")

        try:
            connection.commit()
            print(f"--> Sparade övergripande ligastatistik för {len(team_stats_list)} lag.")
        except Error as e:
            logging.error(f"Fel vid commit av lagstatistik: {e}")
        finally:
            if connection.is_connected():
                cursor.close()
                connection.close()