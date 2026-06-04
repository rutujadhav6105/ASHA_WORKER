from app import create_app
from app.extensions import db

app = create_app()
client = app.test_client()

# Perform login via test client
print("Logging in via test client...")
r = client.post('/api/auth/login', json={'mobile': '9876543210', 'password': 'test@123'})
print("Login status:", r.status_code)
if r.status_code != 200:
    print(r.get_json())
    raise SystemExit

token = r.get_json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Try creating ANC record with beneficiary_name
payload = {
    'beneficiary_name': 'ANC Test Beneficiary',
    'asha_id': 'ASH001',
    'lmp': '2026-01-01',
    'edd': '2026-10-08',
    'risk_status': 'Normal'
}
print("Creating ANC with payload:", payload)
resp = client.post('/api/anc/', headers=headers, json=payload)
print("ANC creation status:", resp.status_code)
print("Response JSON:", resp.get_json())

with app.app_context():
    c = db.session.execute(db.text('SELECT COUNT(*) FROM anc_records WHERE name = :name'), {'name': 'ANC Test Beneficiary'}).scalar()
    print("Database verification: matching ANC record count = ", c)
