
import os
import re
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
from web_apply.browser_env import get_page
import asyncio

# Cargamos las variables del .env (entre ellas CANDIDATE_EMAIL)
load_dotenv()

# URL por defecto (la de tu oferta)
DEFAULT_JOIN_URL = "https://join.com/companies/neurosoft-bio2/15111253-ai-and-software-internship?pid=e65242534431eadcb0c9"


def click_on_apply(url: str = DEFAULT_JOIN_URL):
    """
    Hace clic en un botón 'Apply' en páginas de join.com SIN romper el estado
    de la pestaña compartida.

    - Si la pestaña ya está en esa URL, NO vuelve a hacer goto.
    - Solo hace goto si estás en otra página.
    """

    APPLY_REGEX = re.compile("apply", re.IGNORECASE)

    if not url or not url.strip():
        url = DEFAULT_JOIN_URL

    try:
        page = get_page()   # 🔑 misma pestaña compartida para todo el flujo

        # 1) Navegar SOLO si no estamos ya en esa URL
        try:
            if page.url != url:
                page.goto(url, timeout=60_000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)
                except PwTimeout:
                    # muchas páginas no llegan a 'networkidle', no es fatal
                    pass
        except PwTimeout:
            return "⏱️ Timeout cargando la página de la oferta.", page.url

        # 2) Buscar y hacer click en un botón con texto 'apply'
        apply_button = page.get_by_role("button", name=APPLY_REGEX)
        if apply_button.count() == 0:
            apply_button = page.get_by_text(APPLY_REGEX, exact=False)

        if apply_button.count() == 0:
            msg = "❌ No encontré ningún botón con el texto 'Apply' en la página."
            return msg, page.url

        apply_button.first.scroll_into_view_if_needed()
        apply_button.first.click()

        # 3) Esperar a que reaccione la página tras el click
        page.wait_for_timeout(3000)
        try:
            page.wait_for_load_state("networkidle", timeout=10_000)
        except PwTimeout:
            # de nuevo, best-effort
            pass

        updated_page = page.url

        msg = (
            "✅ Primer paso completado.\n\n"
            "- Se pulsó **'Apply'**.\n"
            f"- Nueva URL: {updated_page}\n"
        )
        return msg, updated_page

    except PwTimeout:
        return "⏱️ Timeout cargando la página o tras el clic en 'Apply'.", url
    except Exception as e:
        return f"❌ Error usando Playwright: {e}", url

async def click_on_apply_async(url: str = DEFAULT_JOIN_URL):
    """
    Tool ASÍNCRONA para LangGraph / ReAct.
    Corre snapshot_page_sync en un hilo, fuera del event loop.
    """
    return await asyncio.to_thread(click_on_apply, url)



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


def fill_w3global_form(url):
    
    try:
        # with sync_playwright() as p:
        #     browser = p.chromium.launch(headless=False, slow_mo=300)
        #     page = browser.new_page()
            page = get_page()   # 🔑 misma pestaña para todas las tools

            # 1) Ir a la página SOLO si aún no estamos ahí
            if url and page.url != url:
                page.goto(url, wait_until="domcontentloaded")

            # 2) Campos de texto básicos
            page.get_by_placeholder("Enter First Name").fill("Alex")
            page.get_by_placeholder("Enter Last Name").fill("Garcia")
            page.get_by_placeholder("Enter Email Id").fill("alex@example.com")
            page.get_by_placeholder("Phone Number").fill("+41790000000")

            # 3) European Nationality (select normal)
            page.wait_for_selector("select#nationality")
            page.select_option("select#nationality", value="ES")  # Spain (ES)

            # 4) European Work Authorizations (multi-select "raro")

            # Abrir el dropdown haciendo clic en el componente visible
            page.locator("div.ss-main:has-text('European Work Authorizations')").click()

            # Clic en la opción que quieras (ajusta el texto exacto que aparece en la lista)
            page.locator("div.ss-option:has-text('Spain (ES)')").click()

            # Si quieres seleccionar varias autorizaciones, repite el click con otros países
            # page.locator("div.ss-option:has-text('Switzerland (CH)')").click()

            # 5) European Nationality (select normal)
            page.wait_for_selector("select#countryDropdown")
            page.select_option("select#countryDropdown", value="ES")  # Spain (ES)

            # 6) Region(select normal)
            page.wait_for_selector("select#stateDropdown")
            page.select_option("select#stateDropdown", value="Community of Madrid (ES-MD)")  # Spain (ES)

            # 7) Upload Resume
            page.set_input_files("input#file", r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\data\Alberto_Blasco_Resume_GenAI.pdf")

            # Pausa para verlo
            page.wait_for_timeout(5000)
            updated_page = page.url
            #browser.close()

            # Mensaje de resumen
            msg = (
                "✅ Tool usada correctamente.\n\n"
                "- Relleno el formulario\n"
                f"- nueva url: {updated_page}`\n"        # ← muy importante: la URL actual tras el click
            )

            return msg, updated_page
          
            
    except PwTimeout:
        return "⏱️ Timeout durante el login con Google.", url
    except Exception as e:
        return f"❌ Error Playwright: {e}", url
    

