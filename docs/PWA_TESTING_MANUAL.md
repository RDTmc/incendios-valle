# 🔍 GUÍA DE VALIDACIÓN MANUAL - PWA INCENDIOS

## Estado: MODO TESTEO MANUAL (Sin Backend)

---

## 📋 CHECKLIST DE VALIDACIÓN

### PARTE 1: Login

| # | Prueba | Esperado | Estado |
|---|--------|----------|--------|
| 1.1 | Abrir app → muestra Login | Formulario de login visible | ⬜ |
| 1.2 | Campos: email + password | Ambos campos visibles | ⬜ |
| 1.3 | Botón "Iniciar Sesión" | Botón activo | ⬜ |
| 1.4 | Click login sin datos | Muestra error validación | ⬜ |
| 1.5 | Click login con datos | Navega a Reporte | ⬜ |
| 1.6 | Link "¿Olvidaste tu contraseña?" | Link visible | ⬜ |

### PARTE 2: Reporte (Formulario)

| # | Prueba | Esperado | Estado |
|---|--------|----------|--------|
| 2.1 | Vista Reporte cargada | Título "Reportar Incendio" | ⬜ |
| 2.2 | Botones tipo: Forestal/Urbano | Ambos visibles y clickeables | ⬜ |
| 2.3 | Botón "Obtener Ubicación" | Botón visible | ⬜ |
| 2.4 | Click obtener ubicación | Pide permiso GPS | ⬜ |
| 2.5 | Si acepta permiso | Muestra coordenadas | ⬜ |
| 2.6 | Input cámara | Campo para subir foto | ⬜ |
| 2.7 | Click input cámara | Abre cámara del celular | ⬜ |
| 2.8 | Campo descripción | Textarea visible | ⬜ |
| 2.9 | Botón "Enviar Reporte" | Botón activo | ⬜ |
| 2.10 | Click enviar | Navega a Confirmación | ⬜ |

### PARTE 3: Confirmación

| # | Prueba | Esperado | Estado |
|---|--------|----------|--------|
| 3.1 | Vista confirmación cargada | ✓ check verde | ⬜ |
| 3.2 | Muestra ID reporte | Formato: RPT-XXXXXXXXX | ⬜ |
| 3.3 | Muestra coordenadas | Lat/Lng visible | ⬜ |
| 3.4 | Botón "Nuevo Reporte" | Navega a Reporte | ⬜ |
| 3.5 | Botón "Ver Mapa de Focos" | Navega a Mapa | ⬜ |

### PARTE 4: Mapa Focos

| # | Prueba | Esperado | Estado |
|---|--------|----------|--------|
| 4.1 | Header "Mapa de Focos" | Título visible | ⬜ |
| 4.2 | Muestra contador de focos | "3 focos en tiempo real" | ⬜ |
| 4.3 | Área del mapa | Zona para mapa visible | ⬜ |
| 4.4 | Leyenda de colores | 3 colores (rojo/naranja/amarillo) | ⬜ |
| 4.5 | Lista de focos | 3 items visibles | ⬜ |
| 4.6 | Cada foco muestra: ID, coordenadas, estado | Información completa | ⬜ |

### PARTE 5: Historial

| # | Prueba | Esperado | Estado |
|---|--------|----------|--------|
| 5.1 | Header "Mis Reportes" | Título visible | ⬜ |
| 5.2 | Lista de reportes | 3 reportes visibles | ⬜ |
| 5.3 | Cada reporte muestra: ID, tipo, estado, fecha | Información completa | ⬜ |
| 5.4 | Estados con colores | Verde/Azul/Amarillo | ⬜ |
| 5.5 | Botón "Ver detalles" | Link visible | ⬜ |

---

## 🧪 PRUEBAS DE PERFORMANCE

| Prueba | Métrica | Target |
|--------|---------|--------|
| Tiempo de carga | < 3 segundos | ⬜ |
| Sin errores Console | 0 errores críticos | ⬜ |
| Responsive | Se adapta a pantalla móvil | ⬜ |

---

## 📱 PRUEBA EN DISPOSITIVO MÓVIL

Para probar en tu celular:

```bash
# Tu PC debe estar en la misma red
# Ejecutar:
npm run dev -- --host

# Esto mostrará la IP de tu PC
# Abrir en celular: http://TU-IP:5173
```

---

## 🎯 RESULTADO ESPERADO

| Sección | Pasos OK | Total | % |
|---------|-----------|-------|---|
| Login | _ / 6 | 6 | 0% |
| Reporte | _ / 10 | 10 | 0% |
| Confirmación | _ / 5 | 5 | 0% |
| Mapa | _ / 6 | 6 | 0% |
| Historial | _ / 5 | 5 | 0% |
| **TOTAL** | **0** | **32** | **0%** |

---

## ⚠️ ERRORES CONOCIDOS (Sin Backend)

Estos errores son NORMALES sin backend:

1. **Login**: Aunque funcione, no valida contra servidor real
2. **Reporte**: Envía datos a nowhere (no hay Lambda)
3. **Mapa**: Muestra datos mock (no de DynamoDB real)
4. **Historial**: Muestra datos hardcodeados

---

## ✅ CRITERIO PARA AVANZAR

Para pasar a Cloudflare Pages, necesitamos:
- [x] 5 vistas creadas
- [x] Navegación funcional
- [ ] Todas las pruebas de UI aprobadas
- [ ] Sin errores críticos en consola

**Una vez aprobado → Deploy a Cloudflare Pages**

---

*Documento para validación manual*
*Fecha: $(date)*