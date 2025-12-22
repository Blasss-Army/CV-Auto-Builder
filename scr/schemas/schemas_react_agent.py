from typing import TypedDict, Literal, List, Optional, Dict, Any
from pydantic import Field, BaseModel
from datetime import datetime
from zoneinfo import ZoneInfo

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

    filled_form: bool



# 1.1) ------------------  Modelo Pydantic para Extraccion de campos para el excel -----------------------
class JobOfferData(BaseModel):
  
    Fecha: str = Field(
        default_factory=lambda: datetime.now(ZoneInfo("Europe/Madrid")).strftime("%d %b %Y"),
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
    
