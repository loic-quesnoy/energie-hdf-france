import datetime
import os
from pathlib import Path

import polars as pl
from dateutil.relativedelta import relativedelta
from dotenv import load_dotenv
from loguru import logger
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = f"postgresql://{os.getenv('SUPABASE_USER')}:{os.getenv('SUPABASE_PWD')}@{os.getenv('SUPABASE_HOST')}:{os.getenv('SUPABASE_PORT')}/{os.getenv('SUPABASE_DB')}"


def run_loading():
    logger.info("3/3 : Démarrage de la brique de Chargement (Load)...")

    if not DATABASE_URL:
        logger.critical(
            "La variable DATABASE_URL est manquante dans le fichier .env ! "
            "Impossible de se connecter à la base de données."
        )
        return

    engine = create_engine(DATABASE_URL)
    processed_dir = Path("data/processed")

    tables_to_load = [
        ("hdf_consumption.parquet", "hdf_consumption"),
        ("hdf_production.parquet", "hdf_production"),
    ]

    try:
        for file_name, table_name in tables_to_load:
            file_path = processed_dir / file_name

            if not file_path.exists():
                logger.warning(
                    f"Le fichier {file_name} est introuvable dans {processed_dir}. Étape ignorée."
                )
                continue

            logger.info(f"Lecture de {file_name}...")
            df = pl.read_parquet(file_path)

            logger.info(f"Insertion de {len(df)} lignes dans la table '{table_name}'...")

            df.write_database(
                table_name=table_name,
                connection=engine,
                if_table_exists="append",
            )
            logger.success(f"Table '{table_name}' mise à jour avec succès.")

        logger.success("=== LE CHARGEMENT DANS SUPABASE EST TERMINÉ===")

    except Exception as e:
        logger.error(f"Une erreur critique est survenue lors du chargement : {e}")
        raise e


def get_last_imported_date() -> datetime.date:
    engine = create_engine(DATABASE_URL)

    try:
        with engine.connect() as connection:
            # Requête SQL pour choper la date maximale
            query = text("SELECT MAX(datetime) AT TIME ZONE 'Europe/Paris' FROM hdf_consumption")
            result = connection.execute(query).scalar()

            if result is not None:
                logger.info(f"Dernière date trouvée en base de données : {result}")
                return result
            else:
                logger.warning("La table existe mais elle est vide (Première insertion).")
                return (datetime.date.today() - relativedelta(months=1)).replace(
                    day=1
                ) - datetime.timedelta(days=1)

    except Exception as e:
        logger.warning(f"Impossible de lire la dernière date : {e}")
