import json
from pathlib import Path

import polars as pl
import pytest
import requests

from src.extract import extract_regional_energy_data
from src.load import get_last_imported_date, run_loading
from src.transform import run_transformation


@pytest.fixture
def fake_json_data():
    return {
        "total_count": 2,
        "results": [
            {
                "code_insee_region": "32",
                "libelle_region": "Hauts-de-France",
                "nature": "Données temps réel",
                "date": "2026-03-25",
                "heure": "03:30",
                "date_heure": "2026-03-25T02:30:00+00:00",
                "consommation": 4682,
                "thermique": 420,
                "nucleaire": 5292,
                "eolien": 3079,
                "solaire": 0,
                "hydraulique": 7,
                "pompage": "0",
                "bioenergies": 95,
                "ech_physiques": -4206,
                "stockage_batterie": "-6",
                "destockage_batterie": "0",
                "tco_thermique": 8.97,
                "tch_thermique": 17.53,
                "column_68": None,
            }
        ],
    }


def test_extract_success(mocker, fake_json_data, tmp_path):
    mock_response = mocker.Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = fake_json_data
    mocker.patch("requests.get", return_value=mock_response)

    mocker.patch("src.extract.Path", lambda *args: tmp_path / "energy_raw_test.json")

    output_file = extract_regional_energy_data(region="Hauts-de-France", date="2026-03-25")

    assert output_file.exists()
    with open(output_file) as f:
        saved_data = json.load(f)
    assert saved_data["total_count"] == 2


def test_extract_api_failure(mocker):
    mocker.patch("requests.get", side_effect=requests.exceptions.HTTPError("API Down"))

    with pytest.raises(requests.exceptions.RequestException):
        extract_regional_energy_data(region="Hauts-de-France", date="2026-03-25")


def test_run_transformation_logic(mocker, fake_json_data, tmp_path):
    input_file = tmp_path / "raw_input.json"
    input_file.write_text(json.dumps(fake_json_data))

    mocker.patch("src.transform.len", return_value=96)

    real_write_parquet = pl.DataFrame.write_parquet

    def mock_write_parquet(df, file_path, *args, **kwargs):
        actual_filename = Path(file_path).name
        target_path = tmp_path / actual_filename

        real_write_parquet(df, target_path, *args, **kwargs)

    mocker.patch.object(
        pl.DataFrame, "write_parquet", autospec=True, side_effect=mock_write_parquet
    )

    run_transformation(input_file)

    consumption_file = tmp_path / "hdf_consumption.parquet"
    production_file = tmp_path / "hdf_production.parquet"

    assert consumption_file.exists(), "Le fichier hdf_consumption.parquet n'a pas été généré !"
    assert production_file.exists(), "Le fichier hdf_production.parquet n'a pas été généré !"

    # Vérification de la structure finale de la consommation
    df_cons = pl.read_parquet(consumption_file)
    assert "datetime" in df_cons.columns
    assert "consumption_mwh" in df_cons.columns
    assert df_cons["consumption_mwh"][0] == 4682


def test_run_loading_missing_files(mocker):
    mocker.patch("src.load.create_engine")
    mocker.patch("src.load.Path.exists", return_value=False)

    run_loading()


def test_get_last_imported_date_empty_db(mocker):
    mock_engine = mocker.MagicMock()
    mock_connection = mocker.MagicMock()
    mock_result = mocker.MagicMock()

    mock_result.scalar.return_value = None
    mock_connection.execute.return_value = mock_result

    mock_engine.connect.return_value.__enter__.return_value = mock_connection
    mocker.patch("src.load.create_engine", return_value=mock_engine)

    fallback_date = get_last_imported_date()

    assert fallback_date is not None
