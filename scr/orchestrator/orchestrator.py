from agents.link_agent import build_graph
from agents.react_agent import build_browser_graph
from retriever.retriever import Retriever
from retriever.conf import RetrieverConfig
from web_apply.google_session import  bootstrap_google_session ,check_google_session



class  Orchestrator:
    def __init__(self, config: RetrieverConfig | None = None):
        
        self.config = config or RetrieverConfig()
        self.retriever = Retriever(self.config)
        self.graph = build_graph(self.retriever)

        # ✅ Solo CHECK aquí (no bootstrap)
        self.google_ready: bool = check_google_session()
        
        self.browser_graph = build_browser_graph()        # 🔹 Nuevo grafo de navegador (BrowserAgent)

     # Opción: método para lanzar bootstrap cuando tú quieras (desde la UI)
    def ensure_google_session(self, auto: bool = False, wait_ms: int = 180000) -> tuple[bool, str]:
        if self.google_ready:
            return True, "✅ Sesión de Google OK"
        if not auto:
            return False, "⚠️ No hay sesión de Google. Ejecuta el bootstrap manualmente."
        # Solo si lo pides explícitamente
        bootstrap_google_session(max_wait_s=wait_ms)
        self.google_ready = check_google_session()
        return (self.google_ready,
                "✅ Sesión creada" if self.google_ready else "❌ No se pudo confirmar la sesión tras el bootstrap.")

    def run(self,
            language: str = "en",
            job_text: str = "Buscamos ingeniero de IA con experiencia en modelos generativos y Python.",
            retrieved: list[dict] = [],
            context: str = ""
            ):
        initial_state = {
            "lang": language,
            "job_offer_text": job_text,
            "retrieved": retrieved,
            "context": context,
        }
        return self.graph.invoke(initial_state) 
    

    def run_browser_agent(
            self,
            url: str ,
            mode: str = "assist",
            goal: str = "apply_for_job",
        ):
            """
            Ejecuta el BrowserAgent con:
            - url: página externa donde queremos actuar (join.com, etc.)
            - mode: 'assist' | 'semi_auto' | 'autopilot' (de momento solo usamos el string, sin lógica compleja)
            - goal: objetivo del agente (por defecto 'apply_for_job')

            Devuelve el estado final del grafo de navegador (BrowserState).
            """

            initial_state = {
                "url": url,
                "mode": mode,
                "goal": goal,
            }

            return self.browser_graph.invoke(initial_state)


