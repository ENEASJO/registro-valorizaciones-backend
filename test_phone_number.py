#!/usr/bin/env python3
"""
Test script to investigate phone number field issue
"""
import requests
import json
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def test_phone_number_issue():
    """Test phone number field mapping"""

    base_url = "http://localhost:8000"

    # Test data with phone number
    test_data = {
        "ruc": "20123456789",
        "razon_social": "EMPRESA TEST TELEFONO S.A.C.",
        "email": "test@telefono.com",
        "celular": "987654321",  # This should be the phone number
        "direccion": "AV. TEST 123",
        "representantes": [
            {
                "nombre": "TEST REPRESENTANTE",
                "cargo": "GERENTE",
                "numero_documento": "12345678",
                "tipo_documento": "DNI",
                "fuente": "MANUAL",
                "es_principal": True,
                "activo": True
            }
        ],
        "representante_principal_id": 0,
        "estado": "ACTIVO",
        "tipo_empresa": "SAC",
        "categoria_contratista": "EJECUTORA"
    }

    headers = {
        "Content-Type": "application/json"
    }

    try:
        # Step 1: Create empresa with phone number
        logger.info("🔍 Step 1: Creating empresa with phone number...")
        logger.info(f"📤 Sending data: {json.dumps(test_data, indent=2, ensure_ascii=False)}")

        response = requests.post(
            f"{base_url}/empresas/",
            json=test_data,
            headers=headers
        )

        logger.info(f"📥 Status Code: {response.status_code}")

        if response.status_code == 201:
            result = response.json()
            logger.info("✅ Empresa created successfully!")
            logger.info(f"📋 Response: {json.dumps(result, indent=2, ensure_ascii=False)}")

            # Extract empresa ID for next step
            empresa_id = result.get('data', {}).get('id')

            if empresa_id:
                # Step 2: Get empresa by ID to check detail view
                logger.info(f"\n🔍 Step 2: Getting empresa details (ID: {empresa_id})...")

                detail_response = requests.get(f"{base_url}/empresas/{empresa_id}")
                logger.info(f"📥 Detail Status Code: {detail_response.status_code}")

                if detail_response.status_code == 200:
                    detail_result = detail_response.json()
                    logger.info("✅ Empresa details retrieved!")
                    logger.info(f"📋 Detail Response: {json.dumps(detail_result, indent=2, ensure_ascii=False)}")

                    # Analyze phone number fields
                    data = detail_result.get('data', {})
                    telefono = data.get('telefono')
                    celular = data.get('celular')

                    logger.info(f"\n📞 Phone Number Analysis:")
                    logger.info(f"   - telefono field: {telefono}")
                    logger.info(f"   - celular field: {celular}")
                    logger.info(f"   - email field: {data.get('email')}")

                    if telefono is None and celular is None:
                        logger.error("❌ ISSUE: Both phone fields are null!")
                        logger.error("❌ This confirms the phone number is not being saved/returned properly")
                    elif telefono:
                        logger.info("✅ telefono field has data")
                    elif celular:
                        logger.info("✅ celular field has data")

                else:
                    logger.error(f"❌ Error getting empresa details: {detail_response.text}")
            else:
                logger.error("❌ No empresa ID in response")
        else:
            logger.error(f"❌ Error creating empresa: {response.text}")

    except requests.exceptions.ConnectionError:
        logger.error("❌ Connection error - make sure the server is running on localhost:8000")
    except Exception as e:
        logger.error(f"❌ Unexpected error: {e}")

if __name__ == "__main__":
    test_phone_number_issue()