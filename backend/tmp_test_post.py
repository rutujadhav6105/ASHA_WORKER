import requests

LOGIN_URL = 'http://127.0.0.1:5000/api/auth/login'
ANC_URL = 'http://127.0.0.1:5000/api/anc/'

resp = requests.post(LOGIN_URL, json={'mobile': '0000000000', 'password': 'admin123'})
print('LOGIN', resp.status_code)
print(resp.text)
if resp.status_code != 200:
    raise SystemExit('Login failed')

token = resp.json()['data']['access_token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}
payload = {'name':'test-post-2','risk_status':'Normal','mobile':'9000000001','village':'TestVillage2'}

r2 = requests.post(ANC_URL, json=payload, headers=headers)
print('POST', r2.status_code)
print(r2.text)
