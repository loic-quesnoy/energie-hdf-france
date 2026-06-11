import polars as pl
from pathlib import Path
from loguru import logger
import polars.selectors as cs
import json


def run_transformation(input_path:Path) -> None:
    logger.info("Démarrage de la brique Transformation...")

    output_path = Path("data/processed/energy_clean_Hauts-de-France.parquet")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        json_data = json.loads(input_path.read_text())
        df = pl.from_dicts(json_data["results"])

        assert len(df) == 96

        logger.info(f"Fichier brut chargé avec succès. Lignes détectées : {len(df)}")
    except Exception as e:
        logger.error(f"Impossible de lire le fichier JSON : {e}")
        return

    df = df.drop("code_insee_region", "libelle_region", "nature", "date", "heure", 'column_68', 'ech_physiques', 'pompage')
    df = df.select(~cs.starts_with("tch", "tco"))
    df = df.with_columns(
        pl.col("date_heure").str.to_datetime("%Y-%m-%dT%H:%M:%S%z")
    )
    df = df.with_columns(
        pl.col("stockage_batterie", "destockage_batterie").cast(pl.Int64)
    )

    dim_date = df.select([
    pl.col("date_heure").dt.date().alias("date_id"),
    pl.col("date_heure").dt.year().alias("year"),
    pl.col("date_heure").dt.month().alias("month"),
    pl.col("date_heure").dt.day().alias("day"),
]).unique()

    fact_consumption = df.select([
        pl.col("date_heure").dt.date().alias("date_id"),
        pl.col("date_heure").dt.time().alias("time_id"),
        pl.col("consommation").alias("consumption_mwh")
    ])

    fact_production = df.unpivot(
        index=["date_heure"],
        on=~cs.by_name("date_heure", "consommation"),
        variable_name="production_source",
        value_name="production_mwh"
    ).select([
        pl.col("date_heure").dt.date().alias("date_id"),
        pl.col("date_heure").dt.time().alias("time_id"),
        pl.col("production_source"),
        pl.col("production_mwh")
    ])

    dim_date.write_parquet("data/processed/dim_date.parquet")
    fact_consumption.write_parquet("data/processed/fact_consumption.parquet")
    fact_production.write_parquet("data/processed/fact_production.parquet")
    logger.success(f"Données nettoyées et sauvegardées en Parquet : {output_path}")