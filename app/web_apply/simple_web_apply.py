# app/web_apply/simple_playwright.py

import os
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

def open_and_screenshot(url: str):
    """
    Abre la URL con Chromium, hace un screenshot y devuelve:
    - mensaje de texto para mostrar en la UI
    - ruta de la imagen (o None si ha fallado)
    """

    if not url or not url.strip():
        return "⚠️ No has puesto ninguna URL.", None

    # Carpeta donde guardamos la captura
    os.makedirs("screens", exist_ok=True)
    screenshot_path = os.path.join("screens", "playwright_demo.png")

    try:
        with sync_playwright() as p:
            # headless=False para ver la ventana del navegador
            browser = p.chromium.launch(headless=False)
            page = browser.new_page()

            # Ir a la página
            page.goto(url, timeout=60_000, wait_until="domcontentloaded")

            # Obtener título y hacer captura
            title = page.title()
            page.screenshot(path=screenshot_path, full_page=True)

            browser.close()

    except PwTimeout:
        return "⏱️ Timeout cargando la página. Prueba con otra URL o revisa tu conexión.", None
    except Exception as e:
        return f"❌ Error usando Playwright: {e}", None

    # Mensaje que mostraremos en Gradio
    msg = (
        "✅ Página abierta correctamente.\n\n"
        f"Título: **{title}**\n\n"
        f"Captura guardada en `{screenshot_path}`."
    )
    return msg, screenshot_path


