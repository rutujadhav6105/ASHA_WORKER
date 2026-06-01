import requests, json
from app import create_app
from app.extensions import db

BASE='http://localhost:5000/api'
# login
r=requests.post(f'{BASE}/auth/login', json={'mobile':'9876543210','password':'test@123'})
print('Login', r.status_code)
if r.status_code!=200:
    print(r.text)
    raise SystemExit
token=r.json()['data']['access_token']
headers={'Authorization':f'Bearer {token}'}
# create family
family_payload={'family_head':'Test Head','home_no':'10','address':'Addr','village':'TestVillage','taluka':'T','district':'D','asha_id':'ASH001'}
print('\nCreate family payload:', json.dumps(family_payload))
rf=requests.post(f'{BASE}/families/', headers=headers, json=family_payload)
print('Create family status:', rf.status_code)
print(rf.text[:400])
# if created, add member
if rf.status_code==201:
    fid=rf.json()['data']['id']
    member_payload={'name':'Member One','dob':'1990-01-01','gender':'Female','aadhaar':'111122223333','apl_bpl':'APL'}
    print('\nAdd member payload:', json.dumps(member_payload))
    rm=requests.post(f'{BASE}/families/{fid}/members', headers=headers, json=member_payload)
    print('Add member status:', rm.status_code)
    print(rm.text[:400])
# check counts
app=create_app()
with app.app_context():
    fcount=db.session.execute(db.text('SELECT COUNT(*) FROM families')).scalar()
    mcount=db.session.execute(db.text('SELECT COUNT(*) FROM family_members')).scalar()
    print('\nCounts -> families:', fcount, 'members:', mcount)
