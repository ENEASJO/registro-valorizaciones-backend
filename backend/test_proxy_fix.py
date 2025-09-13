#!/usr/bin/env python3
"""
Test script to verify proxy headers middleware functionality
"""

import requests
import json

def test_proxy_headers():
    """Test the proxy headers middleware"""
    
    # Test with production URL
    production_url = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/debug/headers"
    
    print("🧪 Testing proxy headers middleware...")
    print(f"📡 Requesting: {production_url}")
    
    try:
        response = requests.get(production_url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ Response received successfully")
            
            # Check key indicators
            print("\n🔍 Analysis:")
            print(f"   URL Scheme: {data.get('scheme')}")
            print(f"   Scope Scheme: {data.get('scope_scheme')}")
            print(f"   Proxy Handled: {data.get('proxy_handled')}")
            
            # Check headers
            headers = data.get('headers', {})
            forwarded_proto = headers.get('x-forwarded-proto')
            x_proxy_handled = headers.get('x-proxy-handled')
            
            print(f"   X-Forwarded-Proto: {forwarded_proto}")
            print(f"   X-Proxy-Handled: {x_proxy_handled}")
            
            # Validate the fix
            if forwarded_proto == 'https' and data.get('scheme') == 'https':
                print("✅ SUCCESS: Proxy headers are being handled correctly!")
                print("   The scheme is properly set to https")
            else:
                print("⚠️ ISSUE: Proxy headers may not be handled correctly")
                
            if x_proxy_handled == 'true':
                print("✅ SUCCESS: Proxy middleware is active")
            else:
                print("⚠️ ISSUE: Proxy middleware may not be active")
                
        else:
            print(f"❌ Error: Received status code {response.status_code}")
            print(f"   Response: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")
        
def test_empresas_endpoint():
    """Test the empresas endpoint that was causing redirects"""
    
    empresas_url = "https://registro-valorizaciones-503600768755.southamerica-west1.run.app/api/empresas/"
    
    print(f"\n🧪 Testing empresas endpoint...")
    print(f"📡 Requesting: {empresas_url}")
    
    try:
        response = requests.get(empresas_url, timeout=30)
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            print("✅ SUCCESS: Empresas endpoint is working correctly!")
            data = response.json()
            print(f"   Response type: {type(data)}")
            if isinstance(data, dict):
                print(f"   Success: {data.get('success')}")
                print(f"   Message: {data.get('message', 'No message')}")
        elif response.status_code == 307:
            print("❌ ISSUE: Still receiving 307 redirect")
            print(f"   Location: {response.headers.get('location', 'No location header')}")
        else:
            print(f"⚠️ Unexpected status code: {response.status_code}")
            print(f"   Response: {response.text[:200]}")
            
    except requests.exceptions.RequestException as e:
        print(f"❌ Request failed: {e}")

if __name__ == "__main__":
    print("🚀 Testing Cloud Run HTTPS redirect fix...")
    test_proxy_headers()
    test_empresas_endpoint()
    print("\n✅ Test completed!")