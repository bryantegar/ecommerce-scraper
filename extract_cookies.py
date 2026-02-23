import json
from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.chromium.launch(headless= True)
    context = browser.new_context()
    page = context.new_page()
    page.goto("https://www.lazada.co.id/")
    
    cookies = context.cookies()
    print(cookies)
    #Save Cookies
    with open("lazada_cookies.json", "w") as f:
        json.dump(cookies, f, indent=4)
        