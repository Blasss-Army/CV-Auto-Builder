from ui.gradio_app import run_gradio
from orchestrator.orchestrator import Orchestrator
from retriever.retriever import Retriever
from retriever.conf import RetrieverConfig
# from app.react_agent import build_graph


if __name__ == "__main__":
    o = Orchestrator() 
    run_gradio(o)