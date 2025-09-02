# 📋 Estándares de Desarrollo - Registro de Valorizaciones

## 🎯 Propósito
Este documento establece estándares para prevenir problemas de archivos duplicados y mantener consistencia en el código.

## 🚫 PROBLEMAS IDENTIFICADOS Y SOLUCIONADOS

### Problema Principal: Archivos Duplicados
- **Síntoma**: Cambios en código no se reflejan en la aplicación
- **Causa**: Archivos `.js` y `.tsx` duplicados, la app usaba el obsoleto
- **Solución**: Eliminación masiva de duplicados + .gitignore optimizado

## ✅ ESTÁNDARES OBLIGATORIOS

### 1. Extensiones de Archivos
```
✅ USAR:
- .tsx para componentes React con TypeScript
- .ts para servicios, utils, tipos con TypeScript  
- .js SOLO para archivos de configuración (vite.config.js, tailwind.config.js)

❌ NUNCA:
- .js para componentes (usar .tsx)
- .js para servicios (usar .ts)
- Archivos duplicados con diferentes extensiones
```

### 2. Estructura de Carpetas
```
src/
├── components/          # Componentes globales (.tsx)
├── modules/            
│   └── [modulo]/
│       ├── components/  # Componentes específicos (.tsx)  
│       ├── services/    # Servicios (.ts)
│       └── types/       # Tipos TypeScript (.ts)
├── services/           # Servicios globales (.ts)
├── types/             # Tipos globales (.ts)  
└── utils/             # Utilidades (.ts)
```

### 3. Nomenclatura de Archivos
```
✅ CORRECTO:
- PascalCase para componentes: FormularioEmpresa.tsx
- camelCase para servicios: consultaRucService.ts
- kebab-case para utils: date-helpers.ts

❌ INCORRECTO:  
- formulario-empresa.tsx
- ConsultaRucService.ts
- DateHelpers.ts
```

### 4. Imports
```typescript
// ✅ CORRECTO - Con extensión explícita
import FormularioEmpresa from './FormularioEmpresa';
import { consultaRuc } from '../services/consultaRucService';

// ❌ INCORRECTO - Sin extensión puede causar ambigüedad
import FormularioEmpresa from './FormularioEmpresa.js';
```

### 5. Configuración TypeScript
```json
{
  "strict": true,
  "forceConsistentCasingInFileNames": true,
  "noImplicitAny": true,
  "isolatedModules": true
}
```

## 🛡️ PREVENCIÓN AUTOMÁTICA

### .gitignore Optimizado
```gitignore
# Prevenir archivos duplicados
**/components/*.js
**/services/*.js  
**/config/api.js

# Permitir solo configuraciones necesarias
!**/index.js
!**/*.config.js
```

## 🔍 CHECKLIST PRE-COMMIT

### Antes de cada commit:
- [ ] No hay archivos `.js` en `/components/`
- [ ] No hay archivos `.js` en `/services/`
- [ ] Todos los imports tienen extensiones correctas
- [ ] TypeScript compila sin errores: `npm run build`
- [ ] No hay archivos temporales: `.backup`, `.tmp`, `.old`

## 🚀 COMANDOS ÚTILES

### Verificar Duplicados
```bash
# Buscar archivos .js en components
find . -name "*.js" -path "*/components/*" ! -name "index.js"

# Buscar archivos .js en services  
find . -name "*.js" -path "*/services/*"
```

### Limpieza de Emergencia
```bash
# CUIDADO: Solo usar en caso de emergencia
find . -name "*.js" -path "*/components/*" ! -name "index.js" -delete
```

## 🎯 BENEFICIOS DE ESTOS ESTÁNDARES

1. **Consistencia**: Todos usan las mismas extensiones
2. **Predictibilidad**: Siempre sabes qué archivo se ejecuta
3. **Debugging fácil**: No más confusión por archivos duplicados
4. **Builds rápidos**: Menos archivos duplicados para procesar
5. **Escalabilidad**: Estructura clara para nuevos desarrolladores

## ⚠️ ALERTAS

### Señales de Problema:
- Cambios en código no se ven en la app
- Build exitoso pero funcionalidades no funcionan
- Imports que funcionan en desarrollo pero fallan en producción

### Acción Inmediata:
1. Verificar archivos duplicados
2. Comprobar .gitignore
3. Revisar configuración TypeScript
4. Ejecutar `npm run build` para verificar

---

**📞 Contacto**: Si encuentras problemas, revisa este documento primero.

**🔄 Última actualización**: Septiembre 2024 - Post limpieza masiva