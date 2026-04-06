import urllib.request
from bs4 import BeautifulSoup
import re

url = "https://www.topcv.vn/viec-lam/ky-su-ky-thuat-dien-tu-luong-15-20-trieu-dong-ha-noi/2097563.html?ta_source=BoxFeatureJob_LinkDetail"
req = urllib.request.Request(
    url, 
    data=None, 
    headers={
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
        'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1'
    }
)

try:
    response = urllib.request.urlopen(req)
    html = response.read().decode('utf-8')
    soup = BeautifulSoup(html, 'html.parser')

    title = soup.find('h1', class_='job-detail__info--title')
    title_text = title.text.strip() if title else ""
    
    company = soup.find('h2', class_='company-name-label')
    company_text = company.text.strip() if company else ""
    
    jd = soup.find('div', class_='job-detail__information-detail')
    
    print(f"# {title_text}")
    print(f"## {company_text}")
    if jd:
        # Convert simple tags to markdown roughly
        for tag in jd.find_all(['h3', 'strong']):
            print(f"\n### {tag.text.strip()}")
        
        for li in jd.find_all('li'):
            print(f"- {li.text.strip()}")
            
        print("\nRAW HTML snippet as fallback:")
        print(jd.get_text(separator="\n", strip=True))
    else:
        print("Không tìm thấy mô tả công việc. HTML thô:")
        print(html[:1000])

except Exception as e:
    print(e)
