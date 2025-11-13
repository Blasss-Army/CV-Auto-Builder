from playwright.sync_api import sync_playwright

def main():
    # 1) Lanzar Playwright
    with sync_playwright() as p:
        # 2) Abrir navegador (headless=False para ver la ventana)
        browser = p.chromium.launch(headless=False)

        # 3) Crear una nueva pestaña
        page = browser.new_page()

        # 4) Ir a una página muy simple
        page.goto("https://www.youtube.com/watch?v=5gO0xpY_Y3E&list=RD5gO0xpY_Y3E&start_radio=1&t=48s", wait_until="domcontentloaded")

        # 5) Imprimir el título en la consola
        print("Título de la página:", page.title())

        # 6) Tomar una captura de pantalla
        page.screenshot(path="example.png", full_page=True)
        print("Captura guardada en example.png")

        # 7) Cerrar navegador
        browser.close()

if __name__ == "__main__":
    main()