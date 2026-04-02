from datetime import datetime
from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel

# ──────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────


# -------------------------------------------------
class Role(str, Enum):
    admin = "admin"
    user = "user"
    pending = "pending"


# -------------------------------------------------
class Origen(str, Enum):
    EPAM = "EPAM"
    OBRAS = "OBRAS"
    FUNCIONAMIENTO = "FUNCIONAMIENTO"


# -------------------------------------------------
class FuenteFinanciamientoSIIF(str, Enum):
    f_10 = "10"
    f_11 = "11"
    f_12 = "12"
    f_13 = "13"
    f_14 = "14"
    f_15 = "15"


# -------------------------------------------------
class TipoComprobanteSIIF(str, Enum):
    adelanto_contratista = "PA6"
    anticipo_viatico = "PA3"
    reversion_viatico = "REV"


# -------------------------------------------------
class GrupoPartidaSIIF(int, Enum):
    """
    Enum para representar los grupos de partidas del SIIF.
    """

    sueldos = 1
    bienes_consumo = 2
    servicios = 3
    bienes_capital = 4


# ──────────────────────────────────────────────
# Users & Auth
# ──────────────────────────────────────────────


# -------------------------------------------------
class LoginUser(BaseModel):
    username: str
    password: str


# -------------------------------------------------
class UserRegistrationForm(BaseModel):
    username: str
    password: str


# -------------------------------------------------
class CreateUser(BaseModel):
    username: str
    password: str
    role: Role = Role.user


# -------------------------------------------------
class PublicStoredUser(BaseModel):
    username: str
    id: str
    role: Role


# -------------------------------------------------
class UpdateUserRole(BaseModel):
    role: Role = Role.user


# -------------------------------------------------
class ExternalCredentialIn(BaseModel):
    systemName: str
    externalUsername: str
    externalPassword: str


# ──────────────────────────────────────────────
# Reports
# ──────────────────────────────────────────────


# -------------------------------------------------
class BancoINVICOReport(BaseModel):
    ejercicio: int
    mes: str
    fecha: datetime
    cta_cte: str
    movimiento: Optional[str] = None
    es_cheque: bool
    beneficiario: Optional[str] = None
    importe: float
    concepto: Optional[str] = None
    moneda: Optional[str] = None
    libramiento: Optional[str] = None
    cod_imputacion: str
    imputacion: str


# -------------------------------------------------
class ControlRecursosReport(BaseModel):
    ejercicio: int
    mes: str
    cta_cte: str
    grupo: str
    recursos_siif: float
    depositos_banco: float


# -------------------------------------------------
class ResumenRendProvReport(BaseModel):
    origen: Origen
    ejercicio: int
    mes: str
    fecha: datetime
    beneficiario: str
    destino: str
    libramiento_sgf: str
    movimiento: str
    cta_cte: str
    importe_bruto: float
    gcias: float
    sellos: float
    iibb: float
    suss: float
    invico: float
    seguro: float
    salud: float
    mutual: float
    otras: float
    retenciones: float
    importe_neto: float


# -------------------------------------------------
class Rf602Report(BaseModel):
    ejercicio: int
    estructura: str
    fuente: FuenteFinanciamientoSIIF
    programa: str
    subprograma: str
    proyecto: str
    actividad: str
    grupo: str
    partida: str
    org: str
    credito_original: float
    credito_vigente: float
    comprometido: float
    ordenado: float
    saldo: float
    pendiente: float


# -------------------------------------------------
class Rf610Report(BaseModel):
    ejercicio: int
    estructura: str
    programa: str
    desc_programa: Optional[str] = None
    subprograma: str
    desc_subprograma: Optional[str] = None
    proyecto: str
    desc_proyecto: Optional[str] = None
    actividad: str
    desc_actividad: Optional[str] = None
    grupo: str
    desc_grupo: str
    partida: str
    desc_partida: str
    credito_original: float
    credito_vigente: float
    comprometido: float
    ordenado: float
    saldo: float


# ──────────────────────────────────────────────
# API Route Responses
# ──────────────────────────────────────────────


# -------------------------------------------------
class ErrorsDetails(BaseModel):
    loc: str
    msg: str
    error_type: str


# -------------------------------------------------
class ErrorsWithDocId(BaseModel):
    doc_id: str
    details: List[ErrorsDetails]


# -------------------------------------------------
class RouteReturnSchema(BaseModel):
    title: Optional[str] = None
    deleted: int = 0
    added: int = 0
    errors: List[ErrorsWithDocId] = []


# -------------------------------------------------
class ValidationError(BaseModel):
    loc: List[Any]
    msg: str
    type: str


# -------------------------------------------------
class HTTPValidationError(BaseModel):
    detail: Optional[List[ValidationError]] = None
