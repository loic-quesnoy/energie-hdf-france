import requests
import json
from datetime import datetime
from pathlib import Path
from loguru import logger

logger.add("data/pipeline.log", rotation="10 MB", retention="10 days", level="INFO")

def extract_regional_energy_data(region:str, date:str):
    logger.info(f"Début de l'extraction des données depuis l'ODRÉ pour la date du {date} et la région {region}")

    try:
        url = f"https://odre.opendatasoft.com/api/explore/v2.1/catalog/datasets/eco2mix-regional-tr/records?where=libelle_region='{region}'and date='{date}'&order_by=heure&limit=100"
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        timestamp = datetime.now().strftime("%Y%m%d")
        filename = Path(f"data/raw/energy_raw_{timestamp}_{date}_{region}.json")
        filename.parent.mkdir(parents=True, exist_ok=True)

        with open(filename, "w", encoding="utf-8") as f:
            json.dump(response.json(), f, ensure_ascii=False, indent=4)

        logger.success(f"Extraction réussie, fichier sauvegardé sous : {filename}")
        return filename

    except requests.exceptions.RequestException as e:
        logger.error(f"Erreur lors de l'extraction : {e}")
        raise e