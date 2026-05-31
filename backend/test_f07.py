"""Quick verification of all F-07 endpoints."""
import httpx
import json

BASE = "http://127.0.0.1:8000"

tests = [
    ("GET /ping", "GET", "/ping", None),
    ("GET /api/services/types", "GET", "/api/services/types", None),
    ("GET /api/services/nearby (hospital)", "GET", "/api/services/nearby?lat=13.08&lng=80.27&type=hospital&radius=5000", None),
    ("GET /api/services/nearby (police)", "GET", "/api/services/nearby?lat=13.08&lng=80.27&type=police&radius=10000", None),
    ("GET /api/services/nearby (ambulance)", "GET", "/api/services/nearby?lat=13.08&lng=80.27&type=ambulance", None),
    ("GET /api/services/nearby (NO LAT/LNG)", "GET", "/api/services/nearby?type=hospital", 400),
    ("GET /api/services/nearby (INVALID TYPE)", "GET", "/api/services/nearby?lat=13.08&lng=80.27&type=invalid", 400),
    ("GET /api/services/offline-pack", "GET", "/api/services/offline-pack?lat=13.08&lng=80.27", None),
    ("GET /api/services/{bad_id}", "GET", "/api/services/non-existent-id", 404),
]

passed = 0
failed = 0

for name, method, path, expected_status in tests:
    try:
        r = httpx.get(f"{BASE}{path}")
        status = r.status_code
        data = r.json()

        if expected_status and status != expected_status:
            print(f"  FAIL  {name} -> expected {expected_status}, got {status}")
            failed += 1
        elif not expected_status and status != 200:
            print(f"  FAIL  {name} -> expected 200, got {status}")
            print(f"         {json.dumps(data, indent=2)[:200]}")
            failed += 1
        else:
            count = ""
            if "data" in data:
                if "services" in data.get("data", {}):
                    count = f" [{len(data['data']['services'])} services]"
                elif "types" in data.get("data", {}):
                    count = f" [{len(data['data']['types'])} types]"
            source = data.get("meta", {}).get("source", "")
            if source:
                source = f" (source: {source})"
            print(f"  PASS  {name} -> {status}{count}{source}")
            passed += 1
    except Exception as e:
        print(f"  FAIL  {name} -> {e}")
        failed += 1

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed, {passed + failed} total")
if failed == 0:
    print("ALL TESTS PASSED")
else:
    print(f"{failed} TEST(S) FAILED")
