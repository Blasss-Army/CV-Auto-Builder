
# t5.py
from playwright.sync_api import sync_playwright
import re

URL = "https://join.com/companies/neurosoft-bio2/14743853/apply/authentication?trackId=TU_TRACKID_REAL"
USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"
GOOGLE_EMAIL = "albertoblasco55555@gmail.com"  # opcional: para el selector de cuentas

from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"


# bootstrap_google_session.py
import os, time



import os, time
from playwright.sync_api import sync_playwright

import os
from playwright.sync_api import sync_playwright

USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"

import os
def is_locked(path):
    return any(os.path.exists(os.path.join(path, n))
               for n in ["SingletonLock","SingletonCookie","SingletonSocket"])
print(is_locked(r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"))


def check_google_session() -> bool:
    if not os.path.isdir(USER_DATA_DIR):
        print("Perfil no existe:", USER_DATA_DIR)
        return False
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,              # 👈 importante
            channel="chrome",
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.new_page()
        page.goto("https://myaccount.google.com/?pli=1", timeout=20000)
        page.wait_for_load_state("domcontentloaded")

        # Diagnóstico adicional
        cookies = ctx.cookies()
        g_cookies = [c for c in cookies if ".google" in c["domain"]]
        print("[PROFILE]", repr(USER_DATA_DIR))
        print("[COOKIES] total:", len(cookies), "google*", len(g_cookies))
        print("[BROWSER]", ctx.browser.version)

        u = page.url.lower()
        ok = ("myaccount.google.com" in u) and ("signin" not in u and "servicelogin" not in u)
        print("URL:", u, "| logged:", ok)
        ctx.close()
        return ok

print(check_google_session())
