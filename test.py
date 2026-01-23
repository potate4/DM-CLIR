import requests
from bs4 import BeautifulSoup

url = "https://www.newagebd.net/archive?date=2026-01-22"
html = requests.get(url, headers={"User-Agent": "Mozilla/5.0"}).text
soup = BeautifulSoup(html, "lxml")

hrefs = sorted(set(a["href"] for a in soup.find_all("a", href=True)))
for h in hrefs[:80]:
    print(h)