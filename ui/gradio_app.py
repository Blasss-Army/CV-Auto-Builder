# gradio_app.py

import gradio as gr
from orchestrator.orchestrator import Orchestrator
from app.linkedin_search import build_linkedin_jobs_url
from app.web_apply.simple_web_apply import open_and_screenshot 

def run_gradio(orchestrator: Orchestrator):

    def google_status():
        ok, msg = orchestrator.ensure_google_session(auto=False)
        return msg  # "✅ Sesión Google OK" o "⚠️ No hay sesión..."

    def google_bootstrap():
        # Abre la ventana de Google con perfil persistente; el usuario inicia sesión y cierra
        ok, msg = orchestrator.ensure_google_session(auto=True, wait_ms=180000)
        # tras cerrar la ventana, devolvemos el estado actual
        ok2, msg2 = orchestrator.ensure_google_session(auto=False)
        return msg if ok else msg2


    def run_graph(job_text, language):
        
        output = orchestrator.run(job_text=job_text, language=language)
        return output['messages'][-1].content
    
    def run_browser_agent(url: str | None = None):
        # URL por defecto si no te pasan nada (pestaña demo)
        url = url or "https://join.com/companies/neurosoft-bio2/15111253-ai-and-software-internship?pid=e65242534431eadcb0c9"

        res = orchestrator.run_browser_agent(url=url, mode="assist")

        if res.get("error") == "missing_google_session":
            msg = "⚠️ Falta sesión de Google. Pulsa 'Iniciar sesión Google (una vez)' y vuelve a ejecutar."
        else:
            msg = res["steps"][-1] if res.get("steps") else "Hecho."

        # SIEMPRE devolvemos: (texto, json)
        return msg, res
    
    '''def run_browser_agent():
        sol = orchestrator.run_browser_agent(url= "https://join.com/companies/neurosoft-bio2/15111253-ai-and-software-internship?pid=e65242534431eadcb0c9")
        return sol
    '''
    
    def make_link(keywords, location, work_types, experience, posted, EasyApply=False, actively_hiring=True, sort_newest=True):
        url = build_linkedin_jobs_url(
            keywords=keywords or "",
            location=location or "",
            work_types=work_types or [],
            experience=experience or [],
            posted=posted or None,
            easy_apply=EasyApply,
            actively_hiring=actively_hiring,
            sort_newest=sort_newest
        )
        return f"[Abrir búsqueda en LinkedIn]({url})\n\n> Se abrirá en tu navegador."
    

    def demo_playwright(url: str):
        """
        Wrapper pequeñito para usar open_and_screenshot desde Gradio.
        """
        text, path = open_and_screenshot(url)
        return text, path
    
        
    with gr.Blocks(title="LangGraph CV Auto-Builder (Demo mínima)") as demo:
        gr.Markdown("# LangGraph CV Auto-Builder — Demo mínima\n\nEste es el esqueleto. A continuación añadiremos RAG y agentes.")
        progress = gr.Progress(track_tqdm=True)



        with gr.Tab("Get LinkedIn URL"):
            gr.Markdown("## 1) Genera una búsqueda en LinkedIn (se abre en tu navegador)")
            kw = gr.Textbox(label="Palabras clave", placeholder="Generative AI, LLM, RAG")
            loc = gr.Textbox(label="Ubicación", placeholder="Switzerland, Zurich")
            wt  = gr.CheckboxGroup(choices=["remote", "hybrid", "on-site"], label="Modalidad")
            ex  = gr.CheckboxGroup(choices=["internship","entry","associate","mid-senior","director", "executive"], label="Seniority")
            po  = gr.Radio(choices=["24h","week","month"], value="week", label="Antigüedad")
            easy_apply = gr.Checkbox(label="Solo ofertas con 'Easy Apply'", value=False)
            btn_link = gr.Button("Crear enlace de búsqueda")
            link_md  = gr.Markdown()
            btn_link.click(fn=make_link, inputs=[kw, loc, wt, ex, po, easy_apply], outputs=link_md)



        with gr.Tab("Generar CV"):
            gr.Markdown("Aquí pegaremos la oferta y generaremos el CV en el idioma elegido.")
            job_text = gr.Textbox(label="Job Offer Text", lines=10, placeholder="Paste the job offer text here...")
            lang  = gr.Radio(choices=["es","en"], value="en", label="Idioma")
            with gr.Row():
                boton_generate_cv = gr.Button("Send", scale=1)
                boton_clear = gr.Button("Clear", scale=1)
            salida_generate_cv = gr.Markdown()

            boton_generate_cv.click(fn = run_graph,inputs = [job_text,lang],outputs = salida_generate_cv )
            boton_clear.click(fn=lambda: ("",""), inputs=[], outputs=[job_text, salida_generate_cv])


        with gr.Tab("Playwright demo"):
            gr.Markdown("## Probar Playwright con una URL sencilla")

            url_demo = gr.Textbox(
                label="URL",
                placeholder="https://example.com"
            )

            btn_demo = gr.Button("Abrir con Playwright y hacer captura")

            msg_out = gr.Markdown(label="Resultado")
            img_out = gr.Image(label="Screenshot de la página")

            btn_demo.click(
                fn=demo_playwright,
                inputs=[url_demo],
                outputs=[msg_out, img_out],
            )
            
        with gr.Tab("Browser Graph"):
            gr.Markdown("## Probar Nuevo Grafo")
            btn_graph_demo = gr.Button("Ejecutar grafo")
            graph_last_md = gr.Markdown(label="Último paso")
            output_json = gr.JSON(label="Estado completo")
    

            btn_graph_demo.click(
                fn=run_browser_agent,
                inputs=[],
                outputs=[graph_last_md,output_json],
            )

        with gr.Tab("LangGraph CV Auto-Builder"):
            gr.Markdown("# LangGraph CV Auto-Builder")

            with gr.Row():
                google_md = gr.Markdown()
                btn_bootstrap = gr.Button("Iniciar sesión Google (una vez)")
                btn_refresh   = gr.Button("Revisar estado")

            url_in = gr.Textbox(label="URL externa (JOIN/…)")
            btn_run = gr.Button("Ejecutar BrowserAgent")
            out_md  = gr.Markdown()
            out_json = gr.JSON()

            demo.load(fn=google_status, inputs=None, outputs=google_md)
            btn_refresh.click(fn=google_status, inputs=None, outputs=google_md)
            btn_bootstrap.click(fn=google_bootstrap, inputs=None, outputs=google_md)

            btn_run.click(
                fn=run_browser_agent,      # misma función
                inputs=url_in,             # aquí sí le pasas URL
                outputs=[out_md, out_json] # mismas 2 salidas
            )



        

    demo.queue(max_size=32).launch()        #   demo.launch()