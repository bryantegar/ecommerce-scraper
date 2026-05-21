from services.service_lazada import ServiceLazada
from cookie_manager.cookie_manager import CookieManager

cm = CookieManager()
cookies = cm.to_playwright_cookies('lazada')
s = ServiceLazada()
resp = s.scrape_lazada_keyword('Dancow', cookies=cookies, page=1)
print('Status:', resp.status_code)
print('Response preview:')
print(resp.text[:1000])
