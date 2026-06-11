CREATE TABLE IF NOT EXISTS hdf_consumption (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ NOT NULL,
    consumption_mwh NUMERIC(12, 2) NOT NULL
);

CREATE TABLE IF NOT EXISTS hdf_production (
    id SERIAL PRIMARY KEY,
    datetime TIMESTAMPTZ NOT NULL,
    production_source VARCHAR(50) NOT NULL,
    production_mwh NUMERIC(12, 2) NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_hdf_consumption_date ON hdf_consumption(datetime);
CREATE INDEX IF NOT EXISTS idx_hdf_production_date ON hdf_production(datetime);