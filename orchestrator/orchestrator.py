from app.react_agent import build_graph
from retriever.retriever import Retriever
from retriever.conf import RetrieverConfig

class  Orchestrator:
    def __init__(self, config: RetrieverConfig | None = None):
        
        self.config = config or RetrieverConfig()
        self.retriever = Retriever(self.config)
        self.graph = build_graph(self.retriever)

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



