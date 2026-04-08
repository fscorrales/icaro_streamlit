__all__ = ["Endpoints"]

from enum import Enum


# -------------------------------------------------
class Endpoints(str, Enum):
    SIIF = "/siif"
    SIIF_RVICON03 = "/siif/rvicon03"
    SIIF_RI102 = "/siif/ri102"
    SIIF_RCI02 = "/siif/rci02"
    SIIF_RFP_P605B = "/siif/rfpP605b"
    SIIF_RF602 = "/siif/rf602"
    SIIF_RF610 = "/siif/rf610"
    SIIF_RCG01_UEJP = "/siif/rcg01Uejp"
    SIIF_RPA03G = "/siif/gtoRpa03g"
    SIIF_RFONDO07TP = "/siif/rfondo07tp"
    SIIF_RFONDOS04 = "/siif/rfondos04"
    USERS = "/users"
    CONTROL_RECURSOS = "/control/controlRecursos"
    SGF_RESUMEN_REND_PROV = "/sgf/resumenRendProv"
    SSCC_BANCO_INVICO = "/sscc/bancoINVICO"
    CTAS_CTES = "/sscc/ctasCtes"
    ICARO_CARGA = "/icaro/carga"
    ICARO_RETENCIONES = "/icaro/retenciones"
    ICARO_OBRAS = "/icaro/obras"
    ICARO_ESTRUCTURAS = "/icaro/estructuras"
    ICARO_PROVEEDORES = "/icaro/proveedores"
    ICARO_CERTIFICADOS = "/icaro/certificados"
    ICARO_RESUMEN_REND_OBRAS = "/icaro/resumenRendObras"
