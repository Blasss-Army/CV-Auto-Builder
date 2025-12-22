# login_join_with_google.py
import os
import re
import time
from typing import Optional, Dict

from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# URL de JOIN para login con Google (cámbiala si usas otra oferta)
URL = "https://join.com/companies/neurosoft-bio2/14743853/apply/authentication?trackId=TU_TRACKID_REAL"

# Directorio del perfil de Google persistente
USER_DATA_DIR = (
    os.getenv("GOOGLE_PROFILE_DIR")
    or r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"
)

# Opcional: para clickar una cuenta concreta en el selector de Google
GOOGLE_EMAIL = "albertoblasco55555@gmail.com"


# =========================
# 1) BOOTSTRAP GOOGLE LOGIN
# =========================
def bootstrap_google_session() -> bool:
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


# =========================
# 3) COMPROBAR SI LA SESIÓN GOOGLE SIGUE VÁLIDA
# =========================
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

