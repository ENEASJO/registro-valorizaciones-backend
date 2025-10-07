"""Modelos para datos de MEF Invierte"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class MEFInvierteInput(BaseModel):
    """Modelo para la entrada de búsqueda en MEF Invierte"""
    cui: str = Field(..., description="Código Único de Inversión", min_length=7, max_length=10)
    class Config:
        json_schema_extra = {"example": {"cui": "2595080"}}

class DatosResultado(BaseModel):
    codigo_idea: str = Field(..., description="Código de idea")
    cui: str
    estado: str
    nombre: str
    tipo_formato: str
    situacion: str
    costo_viable: str
    costo_actualizado: str

class DatosGeneralesEjecucion(BaseModel):
    cui: str
    monto_inversion: str
    monto_actualizado: str

class Modificacion(BaseModel):
    fecha: str
    monto_actualizado: str
    comentarios: str
    usuario: str
    tipo_documento: str
    es_historico: str

class DatosEjecucionLista(BaseModel):
    datos_generales: DatosGeneralesEjecucion
    modificaciones: List[Modificacion]

class Encabezado(BaseModel):
    titulo: str
    fecha_registro: str
    etapa: str
    estado: str

class DatosGenerales(BaseModel):
    cui: str
    nombre: str

class ResponsabilidadFuncional(BaseModel):
    funcion_aprobacion: str = Field(default="")
    funcion_ejecucion: str = Field(default="")
    division_funcional_aprobacion: str = Field(default="")
    division_funcional_ejecucion: str = Field(default="")
    grupo_funcional_aprobacion: str = Field(default="")
    grupo_funcional_ejecucion: str = Field(default="")
    sector_responsable_aprobacion: str = Field(default="")
    sector_responsable_ejecucion: str = Field(default="")

class PMI(BaseModel):
    servicio_publico: str = Field(default="")
    indicador_brechas: str = Field(default="")
    unidad_medida: str = Field(default="")
    espacio_geografico: str = Field(default="")
    contribucion_cierre: str = Field(default="")

class Institucionalidad(BaseModel):
    opmi_aprobacion: str = Field(default="")
    opmi_ejecucion: str = Field(default="")
    uf_aprobacion: str = Field(default="")
    uf_ejecucion: str = Field(default="")
    uei_aprobacion: str = Field(default="")
    uei_ejecucion: str = Field(default="")
    uep: str = Field(default="")

class SeccionAFormulacion(BaseModel):
    responsabilidad_funcional: ResponsabilidadFuncional
    pmi: PMI
    institucionalidad: Institucionalidad

class ProgramacionEjecucion(BaseModel):
    subtotal: str = Field(default="")
    gastos_generales_covid: str = Field(default="")
    inventario_fisico_covid: str = Field(default="")
    expediente_tecnico: str = Field(default="")
    supervision: str = Field(default="")
    liquidacion: str = Field(default="")
    costo_inversion_actualizado: str = Field(default="")

class SeccionBEjecucion(BaseModel):
    programacion_ejecucion: ProgramacionEjecucion
    modificaciones: List = Field(default_factory=list)

class CostosFinales(BaseModel):
    costo_inversion_actualizado: str = Field(default="")
    costo_control_concurrente: str = Field(default="")
    costo_controversias: str = Field(default="")
    monto_carta_fianza: str = Field(default="")
    costo_total_actualizado: str = Field(default="")

class Formato08C(BaseModel):
    encabezado: Encabezado
    datos_generales: DatosGenerales
    seccion_a_formulacion: SeccionAFormulacion
    seccion_b_ejecucion: SeccionBEjecucion
    costos_finales: CostosFinales

class ProyectoMEFInvierte(BaseModel):
    cui: str
    datos_resultado: DatosResultado
    datos_ejecucion_lista: DatosEjecucionLista
    formato_08c: Formato08C
    fuente: str = Field(default="MEF Invierte")
    fecha_consulta: Optional[datetime] = Field(default_factory=datetime.now)

class ErrorResponseMEF(BaseModel):
    error: bool = True
    message: str
    details: Optional[str] = None
    cui: Optional[str] = None
    fuente: str = "MEF Invierte"