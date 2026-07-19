# Digital Twin Field Operations

## Deployment baseline

Use PostgreSQL for the laboratory deployment. Set DATABASE_URL in the deployment environment, for example:

    DATABASE_URL=postgresql+asyncpg://lab_user:strong_password@db-host:5432/lab_db

SQLite in the project folder is suitable only for local development. Do not store a live laboratory database in a OneDrive-synchronised directory.

Apply migrations before starting the API:

    python -m alembic upgrade head

## Daily workflow

1. Open the parcel in Digital Twin.
2. Refresh its weather forecast.
3. Verify forecast coverage and retrieval time.
4. Run the simulation or constrained irrigation schedule for a horizon within the 16-day forecast window.
5. Review the schedule before any field action. The platform does not control irrigation equipment.

Forecast rows are retained by retrieval time. This makes it possible to compare a past forecast with the weather that occurred.

## Field-data import

Import a UTF-8 CSV with one root-zone observation per day. Required columns:

    recorded_at,soil_moisture_mm,rainfall_mm,evapotranspiration_mm

Optional columns are temperature_c, sensor_code, and quality_flag.

soil_moisture_mm must represent root-zone water storage in millimetres. A single-depth volumetric water-content value must be converted to an agreed root-zone storage measure before import. Imported readings are marked field_import; demo and unknown rows are excluded from calibration.

Record every actual irrigation application with date/time, amount in mm, method, and operator name.

## Calibration workflow

A calibration requires at least 14 consecutive daily, quality-checked field observations. The model fits a bounded crop coefficient and field-capacity candidate, then reports MAE, RMSE, and bias.

A calibration candidate cannot affect simulations or schedules. A named laboratory reviewer must apply it. Applying a profile preserves the previous profile as superseded, records the reviewer and timestamp, and makes the new crop coefficient available to forecast-backed runs.

Do not calibrate from generated, demo, unknown, or unverified sensor data.

## Operational boundaries

- Forecasts are modelled meteorological inputs, not field measurements.
- The water-balance model is decision support. It does not automatically actuate irrigation.
- Crop stage, rooting depth, soil analysis, sensor quality checks, and recorded irrigation volumes remain the laboratory's responsibility.
- Investigate large forecast errors or calibration RMSE before applying a new profile.
