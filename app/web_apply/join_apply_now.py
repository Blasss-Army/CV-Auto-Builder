
import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

load_dotenv()
# app/web_apply/join_apply_now.py

import os
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

# Cargamos las variables del .env (entre ellas CANDIDATE_EMAIL)
load_dotenv()

# URL por defecto (la de tu oferta)
DEFAULT_JOIN_URL = "https://join.com/companies/neurosoft-bio2/15111253-ai-and-software-internship?pid=e65242534431eadcb0c9"


def _fill_email_and_continue(page):
    """
    Estamos en la pantalla de autenticación de join.com
    (la que tiene el campo 'Email' y el botón 'Continue').

    Esta función:
      - coge tu email del .env,
      - lo escribe en el input,
      - pulsa el botón 'Continue',
      - espera unos segundos,
      - devuelve (ok, mensaje).
    """

    candidate_email = os.getenv("EMAIL", "")

    if not candidate_email:
        return False, "⚠️ No hay CANDIDATE_EMAIL definido en el .env."

    # 1) Localizar el campo de email
    email_input = page.locator(
        "input[type='email'], "
        "input[name*='email' i], "
        "input[placeholder*='email' i]"
    )

    if email_input.count() == 0:
        return False, "❌ No encontré ningún campo de email en la pantalla de autenticación."

    try:
        email_input.first.fill(candidate_email)
    except Exception as e:
        return False, f"❌ No pude rellenar el email: {e}"

    # 2) Localizar el botón 'Continue'
    continue_button = page.get_by_role("button", name="Continue")

    if continue_button.count() == 0:
        # Fallback: buscar por texto
        continue_button = page.get_by_text("Continue", exact=False)

    if continue_button.count() == 0:
        return False, "❌ No encontré el botón 'Continue' después de rellenar el email."

    try:
        continue_button.first.scroll_into_view_if_needed()
        continue_button.first.click()
        # Esperamos un poco a que cargue lo que venga después
        page.wait_for_timeout(3000)
    except Exception as e:
        return False, f"❌ Error al hacer click en 'Continue': {e}"

    return True, f"✅ Email '{candidate_email}' rellenado y 'Continue' pulsado."




def click_on_apply(url: str = DEFAULT_JOIN_URL):
    
    if not url or not url.strip():
        url = DEFAULT_JOIN_URL

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()

            # 1) Ir a la página de la oferta
            page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=60_000)

            # 2) Buscar y hacer click en 'Apply Now'
            apply_button = page.get_by_role("button", name="Apply Now")
            if apply_button.count() == 0:
                apply_button = page.get_by_text("Apply Now", exact=False)

            if apply_button.count() == 0:
                browser.close()
                msg = "❌ No encontré ningún botón con el texto 'Apply Now' en la página."
                return msg, url

            apply_button.first.scroll_into_view_if_needed()
            apply_button.first.click()

            # Esperar a que cargue la pantalla de autenticación
            page.wait_for_timeout(3000)
            page.wait_for_load_state("networkidle", timeout=60_000)

            updated_page = page.url
            browser.close()

            # Mensaje de resumen
            msg = (
                "✅ Flujo join.com (primer paso) completado.\n\n"
                "- Se abrió la oferta y se pulsó **'Apply Now'**.\n"
                f"- nueva url: {updated_page}`\n"        # ← muy importante: la URL actual tras el click
            )

            return msg, updated_page

    except PwTimeout:
        return "⏱️ Timeout cargando alguna de las páginas de join.com.", None
    except Exception as e:
        return f"❌ Error usando Playwright: {e}", None 
    

def logging_with_google(url: str = DEFAULT_JOIN_URL):

    from playwright.sync_api import sync_playwright
    import re

    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                os.getenv("GOOGLE_PROFILE_DIR"),
                headless=False,
                args=["--disable-blink-features=AutomationControlled"],
            )
            ctx.set_default_timeout(15000)
            ctx.set_default_navigation_timeout(30000)

            page = ctx.new_page()
            page.goto(url=url)
            page.wait_for_load_state("domcontentloaded")

            # 1) Click en "Continue with Google"
            btn = page.get_by_role("button", name="Continue with Google")
            btn.wait_for(state="visible")
            btn.click()

            # 2) El flujo suele seguir en LA MISMA pestaña: ve a accounts.google.com y vuelve
            print("[INFO] Esperando navegación a Google (si ocurre)…")
            try:
                page.wait_for_url(re.compile(r".*accounts\.google\.com.*"), timeout=8000)
                # Si aparece un selector de cuentas, intenta elegir tu email
                try:
                    page.get_by_text(os.getenv("GOOGLE_EMAIL"), exact=True).click()
                except:
                    pass  # muchas veces ya estás logueado y redirige solo
            except:
                pass  # a veces no muestra la URL de Google porque ya hay sesión válida

            # 3) Espera volver autenticado a join.com
            page.wait_for_load_state("networkidle")
            page.wait_for_url(re.compile(r".*join\.com.*"), timeout=15000)


            # 4) (EJEMPLO) Interactuar ya autenticado: buscar un campo del formulario o un botón "Continue"
            # Ajusta a lo que veas en la página de tu oferta
            try:
                # ejemplo típico: botón "Continue" o un input del formulario
                page.get_by_role("button", name=re.compile(r"Continue|Next", re.I)).wait_for(state="visible", timeout=5000)
        
            except:
               pass

            page.wait_for_timeout(5000)
            updated_page = page.url
            ctx.close()  # cierra si quieres


            # Mensaje de resumen
            msg = (
                "✅ Tool usada correctamente.\n\n"
                "- Se loggeo con el correo indicado en **'google'**.\n"
                f"- nueva url: {updated_page}`\n"        # ← muy importante: la URL actual tras el click
            )

            return msg, updated_page
    


    except PwTimeout:
        return "⏱️ Timeout durante el login con Google.", url
    except Exception as e:
        return f"❌ Error Playwright: {e}", url


