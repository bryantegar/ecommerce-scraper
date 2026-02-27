from camoufox.sync_api import Camoufox
import json

with Camoufox(
    os=["windows", "macos", "linux"],
    headless=False             
) as browser:
    page = browser.new_page()
    page.goto("https://shopee.co.id/buyer/login")
    
    cookies = page.context.cookies()  

    print("Login From Browser")
    page.wait_for_event('close', timeout=0)
    cookies_list = page.context.cookies()
    
    print(cookies)
    with open("shopee_cookies.json", "w", encoding="utf-8") as f:
        json.dump(cookies_list, f, indent=2, ensure_ascii=False)
    print("Browser Close")
    
    
    