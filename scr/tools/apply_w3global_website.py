# apply_w3global_website.py

import os
import re
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout
from web_apply.browser_env import get_page
import asyncio
from .join_apply_now import click_on_apply


# Cargamos las variables del .env (entre ellas CANDIDATE_EMAIL)
load_dotenv()

# URL por defecto (la de tu oferta)
DEFAULT_JOIN_URL = "https://www.w3global.com/job-openings/job/marketing-manager-pensacola-fl-us?id=W3GEXT-51376&source=EXTERNALWEBSITE"

def click_on_apply_w3global(page, botton_name: str ="Apply Now"):
    # 1.2) Buscar y hacer click en un botón con texto 'apply'
    apply_button = page.get_by_role("button", name= botton_name)

    # 1.3) Si no lo encuentra por rol, lo busca por texto
    if apply_button.count() == 0:
        apply_button = page.get_by_text("Apply Now", exact=False)

    apply_button.first.scroll_into_view_if_needed()
    apply_button.first.click()


def apply_w3global_website(url: str = DEFAULT_JOIN_URL):

    try:
        page = get_page() 

        #---------------- 1) Clickamos en 'Apply Now' primero --------------------------
        try:

            # 1.1) Navegar SOLO si no estamos ya en esa URL
            if page.url != url:
                page.goto(url, timeout=60_000, wait_until="domcontentloaded")
                try:
                    page.wait_for_load_state("networkidle", timeout=10_000)

                # muchas páginas no llegan a 'networkidle', no es fatal
                except PwTimeout:
                    pass
        except PwTimeout:
            return "⏱️ Timeout cargando la página de la oferta.", page.url
        
        # 1.2) Hacemos click en 'Apply Now'
        click_on_apply_w3global(page, botton_name= "Apply Now")

        # 3) Esperar a que reaccione la página tras el click
        page.wait_for_timeout(3000)

        #------------------ 2) Rellenamos el formulario ------------------------
        # ) Campos de texto básicos
        page.get_by_placeholder("Enter First Name").fill("Alex")
        page.get_by_placeholder("Enter Last Name").fill("Garcia")
        page.get_by_placeholder("Enter Email Id").fill("alex@example.com")
        page.locator("input#phoneNumber").fill("6267118190")       # < - Numero de usa ficticio

        # 3) European Nationality (select normal)
        page.wait_for_selector("select#countryDropdown", timeout=5000)
        page.select_option("select#countryDropdown", value="US")  # The USA (US)

        # 4) Upload Resume
        page.set_input_files("input#file", r"C:\Users\mamen\Desktop\Project\LangGraph CV Auto-Builder\data\Alberto_Blasco_Resume_GenAI.pdf")
    
        # Pausa para verlo
        page.wait_for_timeout(1000)

        # 5) Hacemos click en 'APPLY NOW'
        click_on_apply_w3global(page, botton_name= "APPLY NOW")

        # Pausa para verlo
        page.wait_for_timeout(4000)

        # 6) Volvemos a la pagina principal
        click_on_apply_w3global(page, botton_name= "Apply For More Jobs")
        

        updated_page = page.url
        #browser.close()


        # Mensaje de resumen
        msg = (
            "✅ Tool usada correctamente.\n\n"
            "- Relleno el formulario\n"
            "- Enviada solicitud\n"
            f"- nueva url: {updated_page}`\n"        # ← muy importante: la URL actual tras el click
        )

        return msg, updated_page       
            
    except PwTimeout:
        return "⏱️ Timeout durante el login con Google.", url
    except Exception as e:
        return f"❌ Error Playwright: {e}", url
    

