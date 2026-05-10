import cloudscraper, re, html
s=cloudscraper.create_scraper()
for sid in range(5954, 5963):
    h=s.get(f'https://www.figurerealm.com/actionfigure?action=seriesitemlist&id={sid}&ssid=-1', timeout=30).text
    title=re.search(r'<h1>(.*?)</h1>', h, re.S)
    title=html.unescape(re.sub('<[^>]+>',' ',title.group(1))).strip() if title else 'none'
    hdrs=[html.unescape(re.sub('<[^>]+>',' ',x)).strip() for x in re.findall(r'<div class="checkhdr"[^>]*>(.*?)</div>', h, re.S)]
    print(sid, title, 'items', h.count('group="checkitem"'), 'hdrs', hdrs[:12])
