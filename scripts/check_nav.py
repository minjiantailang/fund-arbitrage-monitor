import requests
import re

def check_160637():
    url = "http://fund.eastmoney.com/Data/Fund_JJJZ_Data.aspx?t=1&lx=1&letter=&gsid=&text=&sort=zdf,desc&page=1,99999&dt=1583566665047&atfc=&onlySale=0"
    print(f"Fetching {url}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    res = requests.get(url, headers=headers)
    print(f"Status: {res.status_code}")
    
    target = '"000001"'
    idx = res.text.find(target)
    if idx != -1:
        print(f"Found data raw: {res.text[idx:idx+200]}")
    else:
        print("160637 not found in response!")

if __name__ == "__main__":
    check_160637()
