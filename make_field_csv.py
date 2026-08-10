"""make_field_csv.py — build a gap-free field-reading CSV for calibration testing.

The readings are SYNTHETIC, not measurements. They are generated forward from a
known crop coefficient and field capacity using the same water balance the
calibrator fits, so a calibration run should recover TRUE_KC / TRUE_FC almost
exactly. That makes it a real test of the fitter rather than a smoke test of the
route: if the returned parameters drift from these, the grid search is wrong.

Import the result through the UI ("Import CSV" on the IoT page) or:
    curl -X POST -F "file=@field_readings.csv" \
      http://127.0.0.1:8000/api/twin/parcels/1/readings/import

The importer forces data_origin="field_import", which IS calibration-eligible
(unlike seed_dev.py's "seed_dev" rows, which are deliberately excluded). The
sensor code below is deliberately not a real sensor id so the provenance stays
visible in the readings table. Keep it stable: sensor_code is part of the CSV
upsert key, so changing it creates a SECOND parallel series instead of updating
the first — and two series on the same day means the calibrator silently keeps
one and discards the other (calibration.py:61-64).

Run from repo root:  python make_field_csv.py
"""
import csv
import datetime as dt

DAYS = 21
SENSOR_CODE = "SIM-CAL-01"
OUTFILE = "field_readings.csv"

# Ground truth the calibrator should recover. Both must be reachable on its
# grid: kc multipliers are 0.60..1.40 in 0.05 steps off the crop's FAO-56 base
# (wheat = 0.95), fc multipliers are 0.85..1.15 off the parcel's stored value.
WHEAT_BASE_KC = 0.95
TRUE_KC = round(WHEAT_BASE_KC * 1.20, 4)   # 1.14
TRUE_FC = 120.0 * 1.05                     # 126.0 — parcel 1 stores 120.0
START_MOISTURE = 112.0

# Weather, held fixed so the file is reproducible. ET0 is reference ET; the crop
# coefficient is applied by the model, not baked in here.
ET0 = [4.8, 5.1, 5.4, 4.9, 5.6, 6.0, 5.2, 4.4, 3.9, 4.6,
       5.3, 5.8, 6.1, 5.5, 4.7, 4.2, 5.0, 5.7, 6.2, 5.4, 4.9]

# Day 17's downpour is deliberately large enough to push the profile PAST
# TRUE_FC so the balance clips there. Without a day at capacity, field capacity
# is not identifiable at all: every candidate above the wettest reading predicts
# an identical trajectory, and the strict `<` at calibration.py:105 just keeps
# the lowest value on the grid. The run still succeeds and still recovers the
# crop coefficient — it simply returns the parcel's existing fc, which reads as
# "calibration did nothing". check_saturation() below guards against that.
RAIN = {3: 12.5, 4: 6.0, 11: 3.5, 17: 45.0}

# Irrigation must be logged as IrrigationEvents too — the calibrator sums those
# per calendar day. Left out of the log, the fit sees water arriving from nowhere.
IRRIGATION = {7: 30.0, 14: 25.0}

TEMPS = [26.5, 27.1, 28.4, 24.0, 23.2, 29.6, 30.1, 28.8, 26.0, 25.4,
         27.7, 29.0, 31.2, 30.4, 27.3, 24.9, 26.8, 28.1, 30.8, 29.2, 27.0]


def build():
    today = dt.date.today()
    start = today - dt.timedelta(days=DAYS - 1)
    moisture = START_MOISTURE
    rows = []
    saturated_days = []
    for day in range(DAYS):
        date = start + dt.timedelta(days=day)
        rain = RAIN.get(day, 0.0)
        irrig = IRRIGATION.get(day, 0.0)
        if day > 0:
            moisture = min(
                TRUE_FC,
                max(0.0, moisture + rain + irrig - ET0[day] * TRUE_KC),
            )
        if abs(moisture - TRUE_FC) < 1e-9:
            saturated_days.append(date.isoformat())
        rows.append({
            # Naive local time — no offset, no trailing Z. 06:00 daily.
            "recorded_at": f"{date.isoformat()}T06:00:00",
            "soil_moisture_mm": round(moisture, 2),
            "rainfall_mm": rain,
            "evapotranspiration_mm": ET0[day],
            "temperature_c": TEMPS[day],
            "sensor_code": SENSOR_CODE,
            "quality_flag": "ok",
        })

    with open(OUTFILE, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)

    peak = max(r["soil_moisture_mm"] for r in rows)
    print(f"{OUTFILE}: {len(rows)} rows, {start} .. {today} (gap-free)")
    print(f"ground truth  kc={TRUE_KC}  field_capacity_mm={TRUE_FC}")
    if saturated_days:
        print(f"saturates on {len(saturated_days)} day(s): {', '.join(saturated_days)}"
              f"  -- field capacity IS identifiable")
    else:
        print(f"WARNING: peak moisture {peak} never reaches {TRUE_FC}. The fit will"
              f" recover kc but leave field capacity at the parcel's stored value.")
    print("irrigation to log as events (amount_mm @ date):")
    for day, amount in sorted(IRRIGATION.items()):
        print(f"  {amount:>5.1f} mm  {(start + dt.timedelta(days=day)).isoformat()}T07:00")


if __name__ == "__main__":
    build()
