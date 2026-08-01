import json
from data_ingestion.football_api import FootballAPIClient

def main():
    client = FootballAPIClient()
    
    status_data = client.get_account_status()
    
    if status_data and not status_data.get('errors'):
        print("\nAnslutning lyckades! Här är din kontostatus:")
        # Extraherar den relevanta informationen om våra tokens
        requests_info = status_data['response']['requests']
        print(f"Din nuvarande plan: {status_data['response']['subscription']['plan']}")
        print(f"Använda anrop idag: {requests_info['current']}")
        print(f"Totalt tillåtna per dag: {requests_info['limit_day']}")
    else:
        print("\nNågot gick fel. Kontrollera din API-nyckel eller loggarna.")
        if status_data:
            print("Felmeddelande från API:", status_data.get('errors'))

if __name__ == "__main__":
    main()
    