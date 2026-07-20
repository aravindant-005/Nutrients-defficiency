import requests

try:
    r = requests.get('http://localhost:8000/health', timeout=5)
    print('health', r.status_code, r.text)
except Exception as e:
    print('health_error', repr(e))

try:
    r2 = requests.post(
        'http://localhost:8000/api/v1/auth/register',
        json={'email': 'testuser@example.com', 'name': 'Test User', 'password': 'Password123'},
        timeout=5,
    )
    print('register', r2.status_code, r2.text)
except Exception as e:
    print('register_error', repr(e))
