"""
Endpoint de prueba para diagnosticar problemas de conectividad
"""
from fastapi import APIRouter
import httpx
from typing import Dict, Any

router = APIRouter()

@router.get("/test-connectivity")
async def test_connectivity() -> Dict[str, Any]:
    """
    Prueba conectividad a diferentes sitios para diagnosticar bloqueos
    """
    async def test_url(url: str, timeout: int = 30) -> Dict[str, Any]:
        try:
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                response = await client.get(url)
                return {
                    "url": url,
                    "success": True,
                    "status_code": response.status_code,
                    "content_length": len(response.content),
                    "error": None
                }
        except Exception as e:
            return {
                "url": url,
                "success": False,
                "status_code": None,
                "content_length": 0,
                "error": str(e)
            }

    urls_to_test = [
        # Sitios que funcionan en Railway (según sistema-de-filtro)
        "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp",
        "https://apps.osce.gob.pe/perfilprov-ui/",

        # Sitio MEF sospechoso
        "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones",

        # Controles
        "https://www.google.com",
        "https://www.github.com"
    ]

    results = []
    for url in urls_to_test:
        result = await test_url(url)
        results.append(result)

    return {
        "status": "completed",
        "tests": results
    }
