import httpx

API_URL = "http://localhost:8000/api"

print("--- Acuifero 4 + Vigia Demo Script (Backend-only Smoke Script) ---")

print("\n1. Triggering Node Video Analysis (simulated)...")
res1 = httpx.post(f"{API_URL}/node/analyze", data={"site_id": "puente-arroyo-01"})
res1.raise_for_status()
data1 = res1.json()
print(f"Node Analysis Complete. Generated Alert Level: {data1['alert']['level']}")

print("\n2. Simulating Offline Mode...")
res2 = httpx.post(f"{API_URL}/settings/connectivity", json={"is_online": False})
res2.raise_for_status()
print(f"Connectivity Status: Online = {res2.json()['is_online']}")

print("\n3. Simulating an offline Volunteer Report (saved to local DB in a real scenario, here we just show the endpoint)...")
res3 = httpx.post(f"{API_URL}/reports", data={
    "site_id": "puente-arroyo-01",
    "reporter_name": "Juan Demo",
    "reporter_role": "Bombero",
    "transcript_text": "El agua ya paso la marca critica del puente, esta subiendo rapido"
})
res3.raise_for_status()
print("Report Submitted. Fused Alert updated locally.")

print("\n4. Toggling Online...")
res4 = httpx.post(f"{API_URL}/settings/connectivity", json={"is_online": True})
res4.raise_for_status()
print(f"Connectivity Status: Online = {res4.json()['is_online']}")

print("\n5. Flushing Sync Queue (simulating Edge -> Central sync)...")
res5 = httpx.post(f"{API_URL}/sync/flush")
res5.raise_for_status()
print(f"Synced Items: {res5.json()['flushed']}")

print("\nDemo Complete!")
print("To view results, ensure the dev servers are running (`./scripts/dev.ps1`) and visit: http://localhost:5173")
