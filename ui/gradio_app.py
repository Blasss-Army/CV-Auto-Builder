# gradio_app.py

import gradio as gr
from orchestrator.orchestrator import Orchestrator
from app.linkedin_search import build_linkedin_jobs_url

def run_gradio(orchestrator: Orchestrator):


    def run_graph(job_text, language):
        
        output = orchestrator.run(job_text=job_text, language=language)
        return output['messages'][-1].content
    
    
    def make_link(keywords, location, work_types, experience, posted):
        url = build_linkedin_jobs_url(
            keywords=keywords or "",
            location=location or "",
            work_types=work_types or [],
            experience=experience or [],
            posted=posted or None
        )
        return f"[Abrir búsqueda en LinkedIn]({url})\n\n> Se abrirá en tu navegador."
    
        
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
            btn_link = gr.Button("Crear enlace de búsqueda")
            link_md  = gr.Markdown()
            btn_link.click(fn=make_link, inputs=[kw, loc, wt, ex, po], outputs=link_md)



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

            



        

    demo.queue(max_size=32).launch()        #   demo.launch()