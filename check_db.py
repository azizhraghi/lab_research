import httpx

r = httpx.get("http://localhost:8000/api/twin/parcels", timeout=10)
print(f"Status: {r.status_code}")
data = r.json()
print(f"Parcels: {len(data)}")
for p in data:
    print(f"  - {p['name']} ({p['code']}) - {p['crop_type']}")

# Test parcel detail with readings
if data:
    pid = data[0]["id"]
    r2 = httpx.get(f"http://localhost:8000/api/twin/parcels/{pid}", timeout=10)
    print(f"\nDetail status: {r2.status_code}")
    detail = r2.json()
    print(f"Readings: {len(detail.get('latest_readings', []))}")
    print(f"Recommendations: {len(detail.get('latest_recommendations', []))}")

    # Test recommendation
    r3 = httpx.post(f"http://localhost:8000/api/twin/parcels/{pid}/recommend", timeout=15)
    print(f"\nRecommendation status: {r3.status_code}")
    if r3.status_code == 200:
        rec = r3.json()
        print(f"  Irrigation: {rec['recommended_irrigation_mm']} mm")
        print(f"  Confidence: {rec['confidence']}")
        print(f"  Rationale: {rec['rationale'][:100]}...")
