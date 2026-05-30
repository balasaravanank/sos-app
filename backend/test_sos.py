"""SOS Core API Test Suite — F-01, F-02, F-03 verification."""

import httpx
import json
import sys

BASE = "http://127.0.0.1:8000/api/sos"
passed = 0
failed = 0


def test(name, fn):
    global passed, failed
    try:
        fn()
        print(f"  PASS: {name}")
        passed += 1
    except Exception as e:
        print(f"  FAIL: {name} -- {e}")
        failed += 1


print("=" * 50)
print("  SOS Core API Test Suite (F-01 to F-03)")
print("=" * 50)

# ------ Test 1: Health check ------
print("\n[1] GET /ping")

def t1():
    r = httpx.get("http://127.0.0.1:8000/ping")
    assert r.status_code == 200
    d = r.json()
    assert d["success"] is True
    assert d["message"] == "server alive"

test("Health check returns 200", t1)

# ------ Test 2: Emergency SOS (F-01) ------
print("\n[2] POST /api/sos/trigger  type=emergency")
sos_id = None

def t2():
    global sos_id
    r = httpx.post(f"{BASE}/trigger", json={
        "type": "emergency", "lat": 13.0827, "lng": 80.2707, "user_id": "test-user-1"
    })
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert d["success"] is True
    assert "sos_id" in d["data"]
    assert d["data"]["status"] == "active"
    assert d["data"]["nearest_ambulance"] is not None
    assert "eta_mins" in d["data"]["nearest_ambulance"]
    sos_id = d["data"]["sos_id"]
    print(f"    sos_id: {sos_id[:12]}...")
    amb = d["data"]["nearest_ambulance"]
    print(f"    Ambulance ETA: {amb['eta_mins']} min (zone: {amb['zone']})")

test("Emergency SOS returns sos_id + nearest ambulance", t2)

# ------ Test 3: Injury SOS (F-02) ------
print("\n[3] POST /api/sos/trigger  type=injury")

def t3():
    r = httpx.post(f"{BASE}/trigger", json={
        "type": "injury", "lat": 13.0827, "lng": 80.2707, "user_id": "test-user-1"
    })
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert d["success"] is True
    assert "sos_id" in d["data"]
    assert d["data"]["nearest_trauma_center"] is not None
    tc = d["data"]["nearest_trauma_center"]
    assert "name" in tc
    assert d["data"]["directions_url"] is not None
    print(f"    Hospital: {tc['name']}")
    print(f"    Distance: {tc['distance_km']} km")
    print(f"    Directions: {d['data']['directions_url'][:70]}...")

test("Injury SOS returns trauma center + directions URL", t3)

# ------ Test 4: Safety Button (F-03) ------
print("\n[4] POST /api/sos/trigger  type=safety")

def t4():
    r = httpx.post(f"{BASE}/trigger", json={
        "type": "safety", "lat": 13.0827, "lng": 80.2707, "user_id": "test-user-2"
    })
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert d["success"] is True
    assert d["data"]["police_notified"] is True
    assert d["data"]["nearest_station"] is not None
    st = d["data"]["nearest_station"]
    assert "contact" in st
    print(f"    Station: {st['name']}")
    print(f"    Contact: {st['contact']}")
    print(f"    ETA: {st['eta_mins']} min")

test("Safety Button notifies police + returns station", t4)

# ------ Test 5: Validation — missing lat/lng ------
print("\n[5] POST /api/sos/trigger  (no lat/lng)")

def t5():
    r = httpx.post(f"{BASE}/trigger", json={"type": "emergency"})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"

test("Missing lat/lng returns 422 validation error", t5)

# ------ Test 6: Invalid type ------
print("\n[6] POST /api/sos/trigger  type=invalid")

def t6():
    r = httpx.post(f"{BASE}/trigger", json={"type": "invalid", "lat": 13.0, "lng": 80.0})
    assert r.status_code == 422, f"Expected 422, got {r.status_code}"

test("Invalid type returns 422", t6)

# ------ Test 7: SOS Status ------
print("\n[7] GET /api/sos/{sos_id}/status")

def t7():
    assert sos_id, "No sos_id from test 2"
    r = httpx.get(f"{BASE}/{sos_id}/status")
    assert r.status_code == 200, f"Got {r.status_code}: {r.text}"
    d = r.json()
    assert d["data"]["status"] == "active"
    assert d["data"]["confirmed_by"] == 0
    print(f"    Status: {d['data']['status']}, confirmed_by: {d['data']['confirmed_by']}")

test("Status check returns active + 0 confirmations", t7)

# ------ Test 8: Crowd Confirm x2 ------
print("\n[8] POST /api/sos/{sos_id}/confirm (x2)")

def t8():
    assert sos_id, "No sos_id from test 2"
    # First confirmation
    r1 = httpx.post(f"{BASE}/{sos_id}/confirm", json={
        "user_id": "bystander-1", "lat": 13.083, "lng": 80.271
    })
    assert r1.status_code == 200
    d1 = r1.json()
    assert d1["data"]["confirmed_by"] == 1
    assert d1["data"]["verified"] is False
    print(f"    Confirm 1: confirmed_by={d1['data']['confirmed_by']}, verified={d1['data']['verified']}")

    # Second confirmation → should verify
    r2 = httpx.post(f"{BASE}/{sos_id}/confirm", json={
        "user_id": "bystander-2", "lat": 13.084, "lng": 80.272
    })
    assert r2.status_code == 200
    d2 = r2.json()
    assert d2["data"]["confirmed_by"] == 2
    assert d2["data"]["verified"] is True
    print(f"    Confirm 2: confirmed_by={d2['data']['confirmed_by']}, verified={d2['data']['verified']}")

test("Crowd confirm increments + verifies at 2", t8)

# ------ Test 9: Status after verification ------
print("\n[9] GET /api/sos/{sos_id}/status (post-verify)")

def t9():
    r = httpx.get(f"{BASE}/{sos_id}/status")
    d = r.json()
    assert d["data"]["status"] == "verified"
    assert d["data"]["confirmed_by"] == 2
    print(f"    Status: {d['data']['status']}, confirmed_by: {d['data']['confirmed_by']}")

test("Status now shows 'verified'", t9)

# ------ Test 10: Invalid SOS ID → 404 ------
print("\n[10] GET /api/sos/fake-id/status")

def t10():
    r = httpx.get(f"{BASE}/fake-id-12345/status")
    assert r.status_code == 404

test("Invalid sos_id returns 404", t10)

# ------ Summary ------
print("\n" + "=" * 50)
print(f"  Results: {passed} passed / {failed} failed / {passed + failed} total")
print("=" * 50)

if failed == 0:
    print("  ALL TESTS PASSED ✅")
else:
    print(f"  {failed} TESTS FAILED ❌")
    sys.exit(1)
