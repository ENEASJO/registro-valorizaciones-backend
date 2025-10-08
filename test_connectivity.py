"""
Script de prueba para verificar conectividad a diferentes sitios web
desde el servidor (Railway/Render)
"""
import httpx
import asyncio
from typing import Dict, Any

async def test_url(url: str, timeout: int = 30) -> Dict[str, Any]:
    """Prueba conectividad a una URL específica"""
    try:
        async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
            response = await client.get(url)
            return {
                "url": url,
                "success": True,
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_length": len(response.content),
                "error": None
            }
    except Exception as e:
        return {
            "url": url,
            "success": False,
            "status_code": None,
            "headers": None,
            "content_length": 0,
            "error": str(e)
        }

async def main():
    """Prueba conectividad a múltiples sitios"""

    urls_to_test = [
        # Sitios que sabemos funcionan en Railway (según sistema-de-filtro)
        "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/FrameCriterioBusquedaWeb.jsp",
        "https://apps.osce.gob.pe/perfilprov-ui/",

        # Sitio MEF que sospechamos está bloqueado
        "https://ofi5.mef.gob.pe/invierte/consultapublica/consultainversiones",

        # Sitios de control
        "https://www.google.com",
        "https://www.github.com"
    ]

    print("=" * 80)
    print("PRUEBA DE CONECTIVIDAD DESDE SERVIDOR")
    print("=" * 80)
    print()

    for url in urls_to_test:
        print(f"Probando: {url}")
        result = await test_url(url)

        if result["success"]:
            print(f"  ✅ ÉXITO - Status: {result['status_code']}, Size: {result['content_length']} bytes")
        else:
            print(f"  ❌ FALLO - Error: {result['error']}")
        print()

    print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main())
