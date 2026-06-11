from loguru import logger
import sys

from src.extract import extract_regional_energy_data
from src.transform import run_transformation

logger.add("data/pipeline.log", rotation="10 MB", level="INFO")

REGION = "Hauts-de-France"

def main():
    logger.info("=== DÉMARRAGE DU PIPELINE ÉNERGÉTIQUE REGIONAL ===")

    try:
        #TODO récuperer la date du dernier enregistrement

        path = extract_regional_energy_data(REGION, "2026-06-09")

        run_transformation(path)

        # run_loading()

        logger.success("=== PIPELINE EXÉCUTÉ AVEC SUCCÈS DE A À Z ===")

    except Exception as e:
        logger.critical(f"Le pipeline a échoué en cours de route : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()