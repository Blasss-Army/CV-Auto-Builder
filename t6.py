
import os
from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"

def check_google_session() -> bool:
    if not os.path.isdir(USER_DATA_DIR):
        print("Perfil no existe:", USER_DATA_DIR)
        return False
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,             # 👈 headed
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.new_page()
        # chequeo robusto contra myaccount
        page.goto("https://myaccount.google.com/?pli=1", timeout=20000)
        page.wait_for_load_state("domcontentloaded")
        u = page.url.lower()
        ok = ("myaccount.google.com" in u) and ("signin" not in u and "servicelogin" not in u)
        print("[PROFILE]", repr(USER_DATA_DIR))
        print("URL:", u, "| logged:", ok)
        ctx.close()
        return ok

print(check_google_session())