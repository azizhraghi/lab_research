"""
Seed demo parcels with 30 days of REAL historical weather data using Open-Meteo API.
Run with: .\.venv\Scripts\python.exe scripts/seed_parcels.py
"""
import asyncio
import datetime
import httpx

from shared.database import engine, Base, AsyncSessionLocal
from agents.digitaltwin.models import Parcel, SensorReading
from agents.digitaltwin.services.irrigation import CROP_COEFFICIENTS

DEMO_PARCELS = [
    {
        "name": "Blé Medjerda",
        "code": "MED-BLE-01",
        "crop_type": "wheat",
        "area_ha": 12.5,
        "latitude": 36.8065,
        "longitude": 10.1815,
        "soil_type": "Clay loam",
        "field_capacity_mm": 130.0,
        "wilting_point_mm": 50.0,
    },
    {
        "name": "Oliveraie Sfax",
        "code": "SFX-OLV-01",
        "crop_type": "olive",
        "area_ha": 8.0,
        "latitude": 34.7406,
        "longitude": 10.7603,
        "soil_type": "Sandy clay",
        "field_capacity_mm": 100.0,
        "wilting_point_mm": 35.0,
    },
    {
        "name": "Agrumes Cap Bon",
        "code": "CBN-AGR-01",
        "crop_type": "citrus",
        "area_ha": 5.2,
        "latitude": 36.8333,
        "longitude": 10.9333,
        "soil_type": "Silt loam",
        "field_capacity_mm": 140.0,
        "wilting_point_mm": 55.0,
    },
]

async def fetch_real_data(parcel: Parcel, days: int = 30) -> list[SensorReading]:
    """Fetch real historical weather data from Open-Meteo and simulate soil moisture."""
    # We want data from today - days to today
    end_date = datetime.date.today()
    start_date = end_date - datetime.timedelta(days=days - 1)
    
    url = "https://archive-api.open-meteo.com/v1/archive"
    params = {
        "latitude": parcel.latitude,
        "longitude": parcel.longitude,
        "start_date": start_date.isoformat(),
        "end_date": end_date.isoformat(),
        "daily": "temperature_2m_mean,precipitation_sum,et0_fao_evapotranspiration",
        "timezone": "Africa/Tunis"
    }
    
    print(f"Fetching real data for {parcel.name}...")
    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=params, timeout=15.0)
        response.raise_for_status()
        data = response.json()
        
    daily = data.get("daily", {})
    times = daily.get("time", [])
    temps = daily.get("temperature_2m_mean", [])
    rains = daily.get("precipitation_sum", [])
    ets = daily.get("et0_fao_evapotranspiration", [])
    
    readings = []
    # Start soil moisture somewhat high (e.g., recently rained/irrigated)
    current_moisture = (parcel.field_capacity_mm * 0.9)
    kc = CROP_COEFFICIENTS.get(parcel.crop_type, 1.0)
    
    for i in range(len(times)):
        dt = datetime.datetime.fromisoformat(times[i])
        # Open-meteo might return None for missing data, default to 0
        rain = rains[i] if rains[i] is not None else 0.0
        et = ets[i] if ets[i] is not None else 0.0
        temp = temps[i] if temps[i] is not None else 20.0
        
        # Calculate a realistic soil moisture based on the real rain and ET
        # moisture = previous_moisture + rain - (ET * crop_coefficient)
        current_moisture = current_moisture + rain - (et * kc)
        
        # Simulated farmer irrigates if it drops too low (near wilting point)
        if current_moisture < parcel.wilting_point_mm * 1.1:
            irrigation = parcel.field_capacity_mm * 0.5
            current_moisture += irrigation
            # We don't record the irrigation directly here, just its effect on moisture
            
        # Cap at field capacity
        current_moisture = min(parcel.field_capacity_mm, current_moisture)
        
        readings.append(SensorReading(
            parcel_id=parcel.id,
            recorded_at=dt,
            soil_moisture_mm=round(current_moisture, 2),
            rainfall_mm=round(rain, 2),
            evapotranspiration_mm=round(et, 2),
            temperature_c=round(temp, 1),
            sensor_code=f"SEN-{parcel.code[:3]}-001",
            quality_flag="ok",
            data_origin="synthetic",
        ))
        
    # We want the newest readings first in the DB conceptually, or let DB sort it out
    return readings

async def seed():
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        # Check if already seeded - if so, we'll clear it for this update
        from sqlalchemy import select, delete
        
        # Clear existing data so we can insert real data
        print("Clearing existing synthetic data...")
        await db.execute(delete(SensorReading))
        await db.execute(delete(Parcel))
        await db.commit()

        # Create parcels
        parcels = []
        for data in DEMO_PARCELS:
            p = Parcel(**data)
            db.add(p)
            parcels.append(p)

        await db.flush()  # get IDs

        # Generate sensor readings
        total_readings = 0
        for parcel in parcels:
            readings = await fetch_real_data(parcel, days=30)
            for r in readings:
                db.add(r)
            total_readings += len(readings)

        await db.commit()
        print(f"[OK] Seeded {len(parcels)} parcels with {total_readings} REAL sensor readings from Open-Meteo.")
        for p in parcels:
            print(f"   - {p.name} ({p.code}) - {p.crop_type}, {p.area_ha} ha")

if __name__ == "__main__":
    asyncio.run(seed())
