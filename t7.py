from playwright.sync_api import sync_playwright
import os, re

USER_DATA_DIR = r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\JoinProfile"
URL = "https://join.com/companies/neurosoft-bio2/14743853/apply/authentication?trackId=TU_TRACKID_REAL"

with sync_playwright() as p:
    print("[DEBUG] PROFILE:", repr(USER_DATA_DIR))
    ctx = p.chromium.launch_persistent_context(
        USER_DATA_DIR,
        headless=False,
        args=["--disable-blink-features=AutomationControlled"],
    )
    page = ctx.new_page()
    page.goto(URL, timeout=30000, wait_until="domcontentloaded")
    print("[DEBUG] antes de clicar:", page.url)

    # Botón Google (varios textos posibles)
    for txt in ["Continue with Google", "Sign in with Google", "Continuar con Google", "Acceder con Google"]:
        loc = page.get_by_role("button", name=txt)
        if loc.count() > 0:
            loc.first.click(timeout=10000)
            break

    # Si hay ida a Google y vuelta…
    try:
        page.wait_for_url(re.compile(r".*accounts\.google\.com.*"), timeout=8000)
    except:
        pass
    page.wait_for_load_state("networkidle")
    print("[DEBUG] después del login:", page.url)
    ctx.close()