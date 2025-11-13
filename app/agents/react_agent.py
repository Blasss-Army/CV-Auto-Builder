# react_agent.py

from typing import TypedDict, Annotated, Literal, Optional, Dict, Any, List
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.messages import HumanMessage, AIMessage
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from functools import partial
from pydantic import Field, BaseModel
from app.exports_tools.excel_export_local import export_to_excel, date_madrid_str
from app.exports_tools.export_to_drive import run_upload_to_drive, run_download_from_drive, LOCAL_XLSX
from app.prompt.prompt_v2 import build_user_prompt, SYSTEM_RESUME 

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

from retriever.retriever import Retriever 




# 1) ------------------ Definimos la clase estado -----------------------
class State(TypedDict):
    messages: Annotated[List[Any], add_messages] # historial conversacio
    
    job_offer_text: Optional[str]
    lang: Optional[Literal['es', 'en']]
    retrieved: List[Dict[str, Any]]
    context: str

    # --- NUEVO: datos de contacto
    name: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    github_url: Optional[str]
    hf_url: Optional[str]
    lk_url: Optional[str]

    # --- NUEVO : datos para excel
    rows_toExport: Optional[Dict[str, Any]]

# 1.1) ------------------  Modelo Pydantic para Extraccion de campos para el excel -----------------------

class JobOfferData(BaseModel):
  
    Fecha: str = Field(
            default_factory=date_madrid_str,
            description="Fecha de la exportacion de la oferta de trabajo"
    )
    Pais: Optional[str] = Field(
            default="Suiza",
            description="Pais de la oferta de trabajo si el usuario lo menciona"
    )
    Campo: Optional[str] = Field(
            default=None,
            description="Campo o area de la oferta de trabajo si el usuario lo menciona"
            )
    Pagina_Web: Optional[str] = Field(
            default=None,
            description="Pagina web de la oferta de trabajo si el usuario lo menciona"
            )
    Nivel: Optional[Literal['internship','entry','associate','mid-senior','director','executive']] = Field(
            default=None,
            description="Nivel de la oferta de trabajo si el usuario lo menciona"
            )
    Remoto: Optional[Literal["on-site", "remote", "hybrid"]] = Field(
            default=None,
            description="Modalidad de la oferta de trabajo si el usuario lo menciona"
            )
    Empresa: Optional[str] = Field(
            default=None,
            description="Empresa de la oferta de trabajo si el usuario lo menciona"
            )
    Link: Optional[str] = Field(
            default=None,
            description="Link de la oferta de trabajo si el usuario lo menciona"
            )
    Salario: Optional[str] = Field(
            default=None,
            description="Salario de la oferta de trabajo si el usuario lo menciona"
            )
    Aceptado: Optional[str] = Field(
            default=None,
            description="Si el usuario ha aceptado la oferta de trabajo"
            )
    def to_excel_dict(self) -> dict:
        # by_alias=True => usa "Pagina Web", "Remoto?", "Aceptado?"
        return self.model_dump(by_alias=True)          # dict
    
extractor = llm.with_structured_output(JobOfferData)

# 2) ------------------ Definimos el grafo -----------------------

# 2.1) ------------------  Nodo 1: leer oferta de Linkedin -----------------------
def read_offer(state: State):
    if "job_offer_text" in state and state["job_offer_text"]:
        print(f"Oferta recibida. {len(state['job_offer_text'])} caracteres.")
        return state
    return {
        "job_offer_text": """We are looking for a Software Engineer with experience in Python and Machine Learning to join our dynamic team. The ideal candidate will have a strong background in developing scalable applications and a passion for AI technologies."""
    }


# 2.2) ------------------  Nodo 2: recuperar contexto desde Qdrant -----------------------
def retrieve_context(state: State, retriever: Retriever):

    query = state['job_offer_text']
    relevant_docs = retriever.get_relevant_documents(query)

    retrieved = []
    for d in relevant_docs:
        retrieved.append({
            "text": d.page_content,
            "source": d.metadata.get("source", ""),
            "page": d.metadata.get("page", None),
        })
    state["retrieved"] = retrieved
    state["context"] = "\n".join([f"- {r['text']}" for r in retrieved])
    return state

# 2.3) ------------------  Nodo 3: generar respuesta -----------------------
def generate_response(state: State):
    lang = state.get("lang", "en")
    mode = state.get("mode", "cover_letter")
    job_offer = state["job_offer_text"]
    context = state["context"]

    user = build_user_prompt(
        lang= lang,
        job_offer=job_offer,
        context=context
    )
    
    result = llm.invoke([{"role": "system", "content": SYSTEM_RESUME},
                         {"role": "user", "content": user}])
    
    return {"messages": [{"role": "assistant", "content": result.content}]}


# 2.4) ------------------  Nodo 4: NODO - obtenere los datos para formar la tabla -----------------------

def extract_offer_data(state: State):
        
        job_offer = state["job_offer_text"]
        extraction = extractor.invoke([
            {"role": "system", "content": "You are an expert at extracting structured data from job offers."},
            {"role": "user", "content": f"Extract the relevant fields from the following job offer:\n\n{job_offer}"}
        ])
        state["rows_toExport"] = extraction
        return state

# 2.5) ------------------  Nodo 5: NODO - escribir los datos obtenidos en el nodo 4 en el excel especificado  -----------------------

def export_offer_data(state: State):
        data = state["rows_toExport"]
        data_dict = data.model_dump(by_alias=True)         # Pydantic model to dict

        # 1) No existe el excel, se comprueba si existe en drive
        if LOCAL_XLSX.exists() is False:
            print("El archivo Excel no existe localmente. Intentando descargar desde Google Drive...")
            done, _ = run_download_from_drive()

            if done:
                print("Descarga completada.")
  
        export_to_excel(data_dict)
        run_upload_to_drive()
        return state

# 3) ------------------  Construcción del grafo -----------------------
def build_graph(retriever: Retriever):
    # Definimos el grafo
    g = StateGraph(State)

    # Definimos los nodos
    g.add_node("read_offer", read_offer)
    g.add_node("retrieve_context", partial(retrieve_context , retriever=retriever))
    g.add_node("generate_response", generate_response)
    g.add_node("extract_offer_data", extract_offer_data)
    g.add_node("export_offer_data", export_offer_data)

    # Definimos las transiciones
    g.add_edge(START, "read_offer")
    g.add_edge("read_offer", "retrieve_context")
    g.add_edge("retrieve_context", "generate_response")
    g.add_edge("generate_response", "extract_offer_data")
    g.add_edge("extract_offer_data", "export_offer_data")
    g.add_edge("export_offer_data", END)

    # 4) ------------------  Ejecución del grafo -----------------------
    # Compilamos
    return g.compile()


