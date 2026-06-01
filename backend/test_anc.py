import requests
from app import create_app
from app.extensions import db
BASE='http://localhost:5000/api'
# login
r=requests.post(f'{BASE}/auth/login', json={'mobile':'9876543210','password':'test@123'})
print('Login', r.status_code)
if r.status_code!=200:
    print(r.text); raise SystemExit
token=r.json()['data']['access_token']
headers={'Authorization':f'Bearer {token}'}
# create anc
payload={'beneficiary_name':'ANC Test','asha_id':'ASH001','lmp':'2026-01-01','edd':'2026-10-08','risk_status':'Normal'}
print('Creating ANC payload:',payload)
resp=requests.post(f'{BASE}/anc/', headers=headers, json=payload)
print('ANC status:', resp.status_code)
print(resp.text[:400])
app=create_app()
with app.app_context():
    c=db.session.execute(db.text('SELECT COUNT(*) FROM anc_records')).scalar()
    print('ANC count:', c)
