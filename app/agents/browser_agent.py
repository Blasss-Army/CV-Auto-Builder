# app/browser_agent.py

# ReAct AI Agent | Thought -> Action -> Observe

from typing import TypedDict, Literal, List, Optional
from langgraph.graph import StateGraph, START, END
import os
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from app.web_apply.browser_env import extract_web_info
from app.web_apply.join_apply_now import click_on_apply, logging_with_google

load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)

from typing import TypedDict, Literal, List, Optional, Dict
from langgraph.graph import StateGraph, START, END
from app.web_apply.google_session import bootstrap_google_session
import os, json
from pydantic import BaseModel, Field
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.prompts import PromptTemplate



def decide_action_llm(observation: str, url: str, model: str = "gpt-4o-mini") -> dict:
    """
    Devuelve SIEMPRE un dict {"type": "click_apply_join"|"noop" , "reason": "..."}.
    Usa salida estructurada (Pydantic + JsonOutputParser) y si falla hace fallback simple.
    Requiere OPENAI_API_KEY en el entorno si quieres usar el LLM.
    """

    # 1) esquema + parser
    class Action(BaseModel):
        type: Literal["click_on_apply", "logging_with_google" "noop"] = Field(..., description="Acción a ejecutar")
        reason: str = Field(..., description="Breve explicación")

    parser = JsonOutputParser(pydantic_object=Action)
    format_instructions = parser.get_format_instructions()

    # 2) prompt
    prompt = PromptTemplate(
        template=(
            "Eres un agente que elige UNA acción.\n\n"
            "Elige exactamente una entre:\n"
            "- click_on_apply (si URL contiene 'join.com' y hay botón/aparición de 'Apply')\n"
            "- logging_with_google (si URL hay botón/aparición de 'Continue with Google' o similar)\n"
            "- noop (si no puedes actuar)\n\n"
            "{format_instructions}\n\n"
            "URL: {url}\n\n"
            "OBSERVACIÓN:\n{observation}\n"
        ),
        input_variables=["url", "observation"],
        partial_variables={"format_instructions": format_instructions},
    )

    # 3) cadena LLM -> parser
    llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0)
    chain = prompt | llm | parser

    # 4) invocar y devolver dict
    action: Action = chain.invoke({"url": url, "observation": observation})
    return action




# 1) ------------------ Definimos la clase estado -----------------------
class State(TypedDict, total=False):
    """
    Estado que maneja el BrowserAgent.
    """
    # URL de la oferta externa
    url: str

    # Objetivo del agente (ej: "apply_for_job")
    goal: str

    # Modo de operación
    mode: Literal["assist", "semi_auto", "autopilot"]

    # Última "observación" de la página (texto)
    observation: str

    # Historial de pasos/acciones que ha ido tomando
    steps: List[str]

    # Flag de finalización
    done: bool

    # Mensaje de error si algo falla
    error: Optional[str]

    loop_count: int
    # ⬇️ NUEVO: acción que el agente ha decidido ejecutar en este paso
    #    Ejemplos:
    #    {"type": "noop"}
    #    {"type": "click_apply_join"}
    next_action: dict


# 2) ------------------ Definimos el grafo -----------------------
# 2.1) ------------------  Nodo 1: Inicializar el estado del Grafo -----------------------

def init_state(state: State) -> State:
    """
    Inicializa algunos campos del estado si no vienen aún.
    """

    new_state = dict(state)

    # Objetivo por defecto
    if "goal" not in new_state or not new_state["goal"]:
        new_state["goal"] = "apply_for_job"

    # Modo por defecto
    if "mode" not in new_state or not new_state["mode"]:
        new_state["mode"] = "assist"

    # Lista de pasos
    if "steps" not in new_state or new_state["steps"] is None:
        new_state["steps"] = []

    # Marcamos done a False si no está
    if "done" not in new_state:
        new_state["done"] = False

    new_state["loop_count"] = 0          # ← empezamos en 0

    return new_state  # tiene que devolver el estado actualizado


# 2.2)  ------------------ Nodo 2:observe_page  ------------------

def observe_page(state: State) -> State:
    """
    Ahora sí: observación REAL de la página usando Playwright.

    - Usa snapshot_page(url) para:
        - abrir la página,
        - obtener título, texto y captura,
        - cerrar el navegador.
    - Guarda un resumen en state["observation"],
      y la ruta de la captura en state["screenshot_path"].
    """
    new_state = dict(state)
    steps = new_state.get("steps", [])
    
    url = new_state.get("url")
    if not url:
        new_state["error"] = "No se ha proporcionado URL al BrowserAgent."
        steps.append("observe_page: error - URL vacía.")
        new_state["steps"] = steps
        return new_state

    # 1) título + texto recortado
    try:
        snap = extract_web_info(url)
    except Exception as e:
        # Si algo peta, lo anotamos en error y no rompemos el grafo
        new_state["error"] = f"Error en snapshot_page: {e}"
        steps.append(f"observe_page: error - {e}")
        new_state["steps"] = steps
        buttons = []
        return new_state

    title = snap["title"]
    text_snippet = snap["text_snippet"]
    buttons = snap["buttons"]

    buttons_str = " | ".join(buttons[:15]) if buttons else "—"

    # Creamos una observación compacta para el agente
    observation_text = (
        f"Título de la página: {title}\n\n"
        f"Botones visibles (máx 15): {buttons_str}\n\n"
        f"Fragmento de texto visible (recortado):\n\n{text_snippet}"
    )

    new_state["observation"] = observation_text

    steps.append(f"observe_page: página observada correctamente (title='{title}'),  botones={len(buttons) if buttons else 0}).")
    new_state["steps"] = steps

    return new_state


# 2.3) ------------------ Nodo 3: decide_next_step REACT del grafo ------------------

def decide_next_step(state: State) -> State:
    """
    Decide la siguiente acción a tomar en función de la observación.

    Ahora:
      1) Intenta usar LLM (_llm_decide_action_min).
      2) Si el LLM dice 'noop' o falla, cae a la regla simplona:
         - Si URL contiene 'join.com' y observation contiene 'Apply' -> click_apply_join
         - Si no -> noop
    """

    new_state = dict(state)
    steps = list(new_state.get("steps", []))                # -> La idea es siempre la misma: trabajar con una copia y luego reasignar.
    observation = new_state.get("observation", "")
    url = new_state.get("url", "")

    # Acción por defecto: no hacer nada
    # 1) Intento con LLM (muy acotado)
    next_action = decide_action_llm(observation, url)

    # 2) Fallback/overrule simplón si el LLM no lo ve claro
    if next_action.get("type") == "noop":
        if "join.com" in url and "apply" in observation.lower():
            next_action = {
                "type": "click_on_apply",
                "reason": "Regla de respaldo: join.com + 'apply' en observación."}

    # Guardamos la acción en el estado
    new_state["next_action"] = next_action
    steps.append(f"decide_next_step: acción elegida -> {next_action['type']} "
                 f"({next_action.get('reason','')})")
    new_state["steps"] = steps

    # OJO: aquí todavía NO marcamos done=True, eso lo hará execute_action
    new_state["done"] = False

    return new_state

# 2.4) ------------------ Nodo 4: Ejecuta la accion seleccionada en 'decide_next_step' ------------------

def execute_action(state: State) -> State:
    """
    Ejecuta la acción guardada en state['next_action'].

    De momento soporta:
      - type = 'noop'                       -> no hace nada y marca done=True.
      - type = 'click_on_apply'             -> llama a click_on_apply(url)
      - type = 'logging_with_google'        -> se loggea si hay para logearse con google
      - type = 'fill_form'                  -> rellena todos los campos necesarios del informe
    """
    new_state = dict(state)
    new_state["loop_count"] = new_state.get("loop_count", 0) + 1
    steps = list(new_state.get("steps", []))
    action = new_state.get("next_action") or {"type": "noop"}

    action_type = action.get("type", "noop")
    url = new_state.get("url")

    # Caso 1: NOOP (no hacer nada)
    if action_type == "noop":
        steps.append("execute_action: acción 'noop', no hacemos nada más.")
        new_state["steps"] = steps
        new_state["done"] = True
        new_state["loop_count"] = new_state.get("loop_count", 0) + 1
        return new_state

    # Caso 2: flujo click_on_apply para join.com
    if action_type == "click_on_apply":
        if not url:
            steps.append("execute_action: error - no hay URL para join.com.")
            new_state["error"] = "No hay URL para ejecutar click_apply_join."
            new_state["steps"] = steps
            new_state["done"] = True
            return new_state

        steps.append(f"execute_action: llamando a click_apply_now_and_email(url='{url}').")
        try:
            msg, new_url = click_on_apply(url=url)
            # Guardamos info relevante
            steps.append(f"execute_action: resultado de click_on_apply -> {msg}")
            new_state["steps"] = steps

            # 🔑 AVANZAMOS LA URL DEL ESTADO
            if url != new_url:
                new_state["url"] = new_url

        except Exception as e:
            steps.append(f"execute_action: error ejecutando click_on_apply -> {e}")
            new_state["error"] = f"Error ejecutando click_on_apply: {e}"
            new_state["steps"] = steps
            new_state["done"] = True
            
            return new_state

    # Caso 3: flujo logging_with_google para join.com  
    if action_type == "logging_with_google":
        if not url:
            steps.append("execute_action: error - no hay URL para join.com.")
            new_state["error"] = "No hay URL para ejecutar click_apply_join."
            new_state["steps"] = steps
            new_state["done"] = True
            return new_state

        steps.append(f"execute_action: llamando a click_apply_now_and_email(url='{url}').")

        try:
            msg, new_url = logging_with_google(url=url)
            # Guardamos info relevante
            steps.append(f"execute_action: resultado de logging_with_google -> {msg}")
            new_state["steps"] = steps

            # 🔑 AVANZAMOS LA URL DEL ESTADO
            if url != new_url:
                new_state["url"] = new_url

        except Exception as e:
            steps.append(f"execute_action: error ejecutando logging_with_google -> {e}")
            new_state["error"] = f"Error ejecutando logging_with_google: {e}"
            new_state["steps"] = steps
            new_state["done"] = True
            return new_state



    # Si llega aquí, acción desconocida
    steps.append(f"execute_action: acción desconocida '{action_type}' \
                 , url actual: {new_state.get("url")} \
                      terminamos."
                      )

    new_state["steps"] = steps
    return new_state

# 3) ------------------  Construcción del grafo -----------------------
def build_browser_graph():
    """
    Crea y compila el grafo del BrowserAgent.
    De momento tiene un flujo muy simple:

    START -> init_state -> observe_page -> decide_next_step -> END
    """

    # Definimos el grafo
    g = StateGraph(State)

    # Añadimos nodos
    g.add_node("init_state", init_state)
    g.add_node("observe_page", observe_page)
    g.add_node("decide_next_step", decide_next_step)
    g.add_node("execute_action", execute_action)

    # Definimos el flujo
    g.add_edge(START, "init_state")
    
    # REACT | observe -> decide -> execute -> END
    #             |                        |
    #              <-----------------------         
    g.add_edge("init_state", "observe_page")
    g.add_edge("observe_page", "decide_next_step")
    g.add_edge("decide_next_step", "execute_action")
    # en build_browser_graph(), añade esta transición condicional
    g.add_conditional_edges(
    "execute_action",
    lambda s: END if (s.get("done") or s.get("loop_count", 0) >= 3) else "observe_page"
    )
    # g.add_edge("decide_next_step", END)

    # Compilamos el grafo y lo devolvemos
    return g.compile()


