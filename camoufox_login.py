from camoufox.sync_api import Camoufox

PROFILE_DIR = "./shopee_session"

with Camoufox(
    user_data_dir=PROFILE_DIR, 
    persistent_context=True,  
    headless=False             
) as browser:
    page = browser.new_page()
    page.goto("https://shopee.co.id/buyer/login")
    
    print("Login From Browser")
    page.wait_for_event('close', timeout=0)
    print("Browser Close")
    
    