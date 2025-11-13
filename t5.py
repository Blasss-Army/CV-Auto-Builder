import os, re, time
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
from typing import Dict, Optional

USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"
def bootstrap_google_session(max_wait_s: int = 180) -> str:
    os.makedirs(USER_DATA_DIR, exist_ok=True)
    with sync_playwright() as p:
        ctx = p.chromium.launch_persistent_context(
            USER_DATA_DIR,
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        page = ctx.new_page()
        page.goto("https://accounts.google.com/", timeout=60000)
        print("➡️ Inicia sesión (correo, pass, 2FA). No cierres hasta que ponga 'Sesión OK'.")
        t0 = time.time()
        ok = False
        while time.time() - t0 < max_wait_s:
            try:
                page.wait_for_load_state("domcontentloaded", timeout=2000)
                u = page.url.lower()
                if "myaccount.google.com" in u or ("signin" not in u and "servicelogin" not in u):
                    ok = True
                    break
            except Exception:
                pass
        ctx.close()
    return "✅ Sesión OK" if ok else "⚠️ No se detectó sesión. Repite el login."

bootstrap_google_session()