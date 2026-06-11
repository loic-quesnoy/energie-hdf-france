from loguru import logger
import sys
import datetime
import polars as pl


from src.extract import extract_regional_energy_data
from src.transform import run_transformation
from src.load import get_last_imported_date, run_loading

logger.add("data/pipeline.log", rotation="10 MB", level="INFO")

REGION = "Hauts-de-France"

def main():
    logger.info("=== DÉMARRAGE DU PIPELINE ÉNERGÉTIQUE REGIONAL ===")

    try:
        last_imported_date = get_last_imported_date()
        first_date_to_import = last_imported_date + datetime.timedelta(days=1)
        dates_serie = pl.date_range(first_date_to_import, datetime.datetime.now().date() - datetime.timedelta(days=1), interval="1d", eager=True)

        for date in dates_serie:
            path = extract_regional_energy_data(REGION, date.strftime("%Y-%m-%d"))

            run_transformation(path)

            run_loading()

        logger.success("=== PIPELINE EXÉCUTÉ AVEC SUCCÈS DE A À Z ===")

    except Exception as e:
        logger.critical(f"Le pipeline a échoué en cours de route : {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()