# 🌐 Integración Frontend - Arquitectura Separada

## 🏗️ NUEVA ARQUITECTURA

```
Frontend (Vercel)
    ↓
┌─────────────────────────────────────────┐
│  DUAL ENDPOINT STRATEGY                 │
├─────────────────────────────────────────┤
│  📊 SCRAPING: Cloud Run + Playwright    │
│  🗄️ CRUD: Vercel Backend + Turso       │
└─────────────────────────────────────────┘
```

## 🔧 CONFIGURACIÓN DEL FRONTEND

### 📝 Variables de Entorno (.env):

```javascript
# Scraping (Playwright) - Cloud Run
VITE_SCRAPING_API_URL=https://tu-cloud-run-url.run.app

# CRUD (Database) - Vercel Backend  
VITE_CRUD_API_URL=https://tu-backend.vercel.app

# Desarrollo local
VITE_LOCAL_SCRAPING=http://localhost:8000
VITE_LOCAL_CRUD=http://localhost:8001
```

### 🎯 API Client Configuration:

```typescript
// src/config/api.ts
const API_CONFIG = {
  // Para scraping (SUNAT/OSCE)
  SCRAPING: {
    BASE_URL: import.meta.env.PROD 
      ? import.meta.env.VITE_SCRAPING_API_URL 
      : 'http://localhost:8000',
    ENDPOINTS: {
      SUNAT: '/consulta-ruc',
      OSCE: '/consulta-osce', 
      CONSOLIDADO: '/consulta-ruc-consolidada'
    }
  },
  
  // Para CRUD (empresas, obras, valorizaciones)
  CRUD: {
    BASE_URL: import.meta.env.PROD 
      ? import.meta.env.VITE_CRUD_API_URL 
      : 'http://localhost:8001',
    ENDPOINTS: {
      EMPRESAS: '/api/empresas',
      OBRAS: '/api/obras',
      VALORIZACIONES: '/api/valorizaciones'
    }
  }
}
```

### 🔄 Service Functions:

```typescript
// src/services/scrapingService.ts
export const scrapingService = {
  async consultarSUNAT(ruc: string) {
    const response = await fetch(
      `${API_CONFIG.SCRAPING.BASE_URL}${API_CONFIG.SCRAPING.ENDPOINTS.SUNAT}/${ruc}`
    );
    return response.json();
  },

  async consultarConsolidado(ruc: string) {
    const response = await fetch(
      `${API_CONFIG.SCRAPING.BASE_URL}${API_CONFIG.SCRAPING.ENDPOINTS.CONSOLIDADO}/${ruc}`
    );
    return response.json();
  }
};

// src/services/crudService.ts  
export const crudService = {
  async listarEmpresas() {
    const response = await fetch(
      `${API_CONFIG.CRUD.BASE_URL}${API_CONFIG.CRUD.ENDPOINTS.EMPRESAS}`
    );
    return response.json();
  },

  async crearEmpresa(empresa: EmpresaCreate) {
    const response = await fetch(
      `${API_CONFIG.CRUD.BASE_URL}${API_CONFIG.CRUD.ENDPOINTS.EMPRESAS}`,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(empresa)
      }
    );
    return response.json();
  },

  async listarObras(empresaId?: number) {
    const url = empresaId 
      ? `${API_CONFIG.CRUD.BASE_URL}${API_CONFIG.CRUD.ENDPOINTS.OBRAS}?empresa_id=${empresaId}`
      : `${API_CONFIG.CRUD.BASE_URL}${API_CONFIG.CRUD.ENDPOINTS.OBRAS}`;
    
    const response = await fetch(url);
    return response.json();
  }
};
```

### 🎯 Flujo de Trabajo Típico:

```typescript
// src/hooks/useEmpresaWorkflow.ts
export const useEmpresaWorkflow = () => {
  const consultarYGuardarEmpresa = async (ruc: string) => {
    try {
      // 1. SCRAPING: Obtener datos de SUNAT/OSCE
      const datosConsolidados = await scrapingService.consultarConsolidado(ruc);
      
      if (datosConsolidados.success) {
        // 2. CRUD: Guardar en base de datos
        const empresaGuardada = await crudService.crearEmpresa({
          ruc: datosConsolidados.data.ruc,
          razon_social: datosConsolidados.data.razon_social,
          // ... más campos
        });
        
        return empresaGuardada;
      }
      
      throw new Error('Error en scraping');
    } catch (error) {
      console.error('Error en workflow:', error);
      throw error;
    }
  };
  
  return { consultarYGuardarEmpresa };
};
```

## 🚀 DESPLIEGUE DEL FRONTEND

### 1️⃣ Actualizar variables en Vercel:

```bash
# En el proyecto del frontend
vercel env add VITE_SCRAPING_API_URL production
# Valor: https://tu-cloud-run-url.run.app

vercel env add VITE_CRUD_API_URL production  
# Valor: https://tu-backend-vercel.vercel.app
```

### 2️⃣ Desplegar frontend:

```bash
cd /path/to/frontend
vercel --prod
```

## 📊 ENDPOINTS FINALES

### Cloud Run (Solo Scraping):
- `GET /consulta-ruc/{ruc}` - SUNAT
- `GET /consulta-osce/{ruc}` - OSCE  
- `GET /consulta-ruc-consolidada/{ruc}` - Ambos
- `POST /buscar` - Legacy

### Vercel Backend (Solo CRUD):
- `GET /api/empresas` - Listar empresas
- `POST /api/empresas` - Crear empresa
- `GET /api/obras` - Listar obras
- `POST /api/obras` - Crear obra
- `GET /api/valorizaciones` - Listar valorizaciones
- `POST /api/valorizaciones` - Crear valorización

## ✅ VENTAJAS DE ESTA ARQUITECTURA

1. **Separación de responsabilidades**
   - Cloud Run: Solo scraping pesado
   - Vercel: Solo CRUD ligero

2. **Escalabilidad independiente**
   - Scraping puede escalar según demanda
   - CRUD siempre disponible

3. **Costo optimizado**
   - Cloud Run solo cuando hay scraping
   - Vercel gratis para CRUD

4. **Mantenimiento simplificado**
   - Playwright aislado en Cloud Run
   - Base de datos manejada por Vercel

## 🔧 PRÓXIMOS PASOS

1. ✅ Backend Vercel configurado
2. 🔄 Actualizar frontend con dual endpoints
3. 🚀 Desplegar ambos
4. ✅ Probar flujo completo