# app/web_apply/browser_env.py

import os
from typing import Dict
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout


def snapshot_page(url: str) -> Dict[str, str]:
    """
    Abre la URL con Chromium, captura información básica y devuelve:
      - title: título de la pestaña
      - text_snippet: un trozo de texto visible de la página

    Si algo falla, lanza una excepción o devuelve info mínima.
    """

    if not url or not url.strip():
        raise ValueError("URL vacía en snapshot_page")


    with sync_playwright() as p:
        # headless=False si quieres ver la ventana; True para “modo invisible”
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        try:
            page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=60_000)
        except PwTimeout:
            browser.close()
            raise RuntimeError("Timeout cargando la página en snapshot_page")

        # Título
        title = page.title()

        # Texto visible (recortamos para no pasarnos de tokens)
        try:
            body_text = page.inner_text("body")
        except Exception:
            body_text = ""

        # Nos quedamos con los primeros N caracteres
        max_chars = 1500
        text_snippet = body_text[:max_chars]

        browser.close()

    return {
        "title": title,
        "text_snippet": text_snippet,
    }



from typing import List
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

def extract_web_info(url: str, max_buttons: int = 30) -> List[str]:
    """
    Abre la URL y devuelve una lista de textos de botones visibles.
    Incluye:
      - <button> (rol accesible)
      - <input type="submit">
      - <a> con apariencia de botón
    """
    if not url or not url.strip():
        raise ValueError("URL vacía en extract_web_info")

    buttons: List[str] = []

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)  # pon True si quieres oculto
        page = browser.new_page()
        try:
            page.goto(url, timeout=60_000, wait_until="domcontentloaded")
            page.wait_for_load_state("networkidle", timeout=60_000)
        except PwTimeout:
            browser.close()
            raise RuntimeError("Timeout cargando la página en snapshot_page")

        # Extraemos el titulo -------------------------------------------
        # Título
        title = page.title()

        # Texto visible (recortamos para no pasarnos de tokens)
        try:
            body_text = page.inner_text("body")
        except Exception:
            body_text = ""

        # Nos quedamos con los primeros N caracteres
        max_chars = 1500
        text_snippet = body_text[:max_chars]


        # a) <button> (rol)    -------------------------------------------
        btns = page.get_by_role("button")
        n = min(btns.count(), max_buttons)
        for i in range(n):
            try:
                t = btns.nth(i).inner_text().strip()
                if t:
                    buttons.append(t)
            except Exception:
                pass

        # b) <input type="submit">   -------------------------------------------
        submits = page.locator("input[type=submit]")
        n2 = min(submits.count(), 10)
        for i in range(n2):
            try:
                v = (submits.nth(i).get_attribute("value") or "").strip()
                if v:
                    buttons.append(v)
            except Exception:
                pass

        # c) enlaces con pinta de botón    -------------------------------------------
        anchors = page.locator("a[role=button], a.button, a.btn, [class*=btn i], [class*=button i]")
        n3 = min(anchors.count(), 20)
        for i in range(n3):
            try:
                t = anchors.nth(i).inner_text().strip()
                if t:
                    buttons.append(t)
            except Exception:
                pass

        browser.close()

    # deduplicar conservando orden y cortar textos largos
    seen = set()
    dedup: List[str] = []
    for b in buttons:
        b = b[:80].strip()
        if b and b not in seen:
            seen.add(b)
            dedup.append(b)

    return {
        "title": title,
        "text_snippet": text_snippet,
        "buttons": dedup,
    }
    