#!/usr/bin/env python3
"""
Probar consulta RUC y guardado en Turso
"""
import sys
from pathlib import Path

# Add the app directory to the Python path
current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

from app.services.empresa_service_turso_enhanced import EmpresaServiceTurso

def test_ruc_save():
    """Probar guardar datos de empresa en Turso"""
    
    # Datos simulados de consulta RUC
    ruc = "20600074114"
    datos_consulta = {
        "success": True,
        "data": {
            "ruc": ruc,
            "razon_social": "CONSTRUCTORA E INGENIERIA V & Z S.A.C.",
            "contacto": {
                "direccion": "AV. INDUSTRIAL 123, LIMA",
                "telefono": "01-2345678",
                "email": "contacto@constructoravz.com"
            },
            "miembros": [
                {
                    "nombre": "JUAN PEREZ GARCIA",
                    "numero_documento": "12345678"
                }
            ]
        }
    }
    
    print(f"🏢 Probando guardar empresa RUC: {ruc}")
    
    # Crear servicio
    service = EmpresaServiceTurso()
    
    # Guardar empresa
    empresa_id = service.save_empresa_from_consulta(ruc, datos_consulta)
    
    if empresa_id:
        print(f"✅ Empresa guardada con ID: {empresa_id}")
        
        # Verificar que se guardó
        empresa = service.get_empresa_by_ruc(ruc)
        if empresa:
            print(f"✅ Empresa recuperada:")
            print(f"   RUC: {empresa.get('ruc')}")
            print(f"   Razón Social: {empresa.get('razon_social')}")
            print(f"   Dirección: {empresa.get('direccion')}")
            print(f"   Representante: {empresa.get('representante_legal')}")
        else:
            print("❌ No se pudo recuperar la empresa")
            
        # Mostrar estadísticas
        stats = service.get_stats()
        print(f"📊 Estadísticas: {stats}")
        
    else:
        print("❌ Error guardando empresa")
    
    service.close()
    return empresa_id is not None

if __name__ == "__main__":
    success = test_ruc_save()
    if success:
        print("🎉 ¡Integración Turso funcionando!")
    else:
        print("❌ Falló la integración")