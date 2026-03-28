import requests

BASE_URL = "http://127.0.0.1:8000/api"

def test():
    # 1. Login
    res = requests.post(f"{BASE_URL}/auth/login", data={"username": "jane@tinycrm.com", "password": "pass123"})
    if res.status_code != 200:
        print(f"Login failed: {res.text}")
        return
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    
    # 2. Get Contacts
    res = requests.get(f"{BASE_URL}/contacts", headers=headers)
    print(f"Contacts Status: {res.status_code}")
    print(f"Contacts Count: {len(res.json()) if res.status_code == 200 else 'Error'}")
    if res.status_code == 200:
        print(f"First Contact: {res.json()[0]['name'] if res.json() else 'None'}")
        
    # 3. Get Deals
    res = requests.get(f"{BASE_URL}/deals", headers=headers)
    print(f"Deals Status: {res.status_code}")
    print(f"Deals Count: {len(res.json()) if res.status_code == 200 else 'Error'}")

if __name__ == "__main__":
    test()
