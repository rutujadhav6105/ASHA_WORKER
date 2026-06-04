import requests

# First, login to get a fresh token
login_url = 'http://localhost:5000/api/auth/login'
login_data = {'mobile': '0000000000', 'password': 'admin123'}
r = requests.post(login_url, json=login_data)
token = r.json()['data']['access_token']
print(f'Token obtained: {token[:50]}...')

# Now test the dashboard endpoint
url = 'http://localhost:5000/api/reports/dashboard'
headers = {
    'Authorization': f'Bearer {token}',
    'Origin': 'http://localhost:8000'
}
r = requests.get(url, headers=headers, timeout=5)
print(f'Status: {r.status_code}')
print(f'All headers: {dict(r.headers)}')
cors_headers = {k: v for k, v in r.headers.items() if 'access-control' in k.lower()}
print(f'CORS Headers: {cors_headers}')
