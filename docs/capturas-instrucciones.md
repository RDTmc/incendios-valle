# Capturas de Pantalla para el Informe de Pruebas

A continuación se indican las capturas necesarias para el informe PDF (R3), cómo generarlas y qué deben mostrar.

---

## 1. Portada del informe de cobertura (Backend)

**Comando:**
```bash
cd ec2/api && python -m pytest --cov --cov-report=html
```

**Captura:** Abrir `ec2/api/htmlcov/index.html` en el navegador.
**Qué mostrar:** La tabla principal con el listado de módulos, columnas `Stmts`, `Miss`, `Cover`. Debe verse el 88% overall.

---

## 2. Portada del informe de cobertura (Frontend)

**Comando:**
```bash
cd frontend && npm run test:coverage
```

**Captura:** Abrir `frontend/coverage/index.html` en el navegador.
**Qué mostrar:** Tabla de cobertura con todos los archivos y el 82% overall.

---

## 3. Tests backend ejecutados (pytest)

**Comando:**
```bash
cd ec2/api && python -m pytest -v --tb=short
```

**Captura:** Terminal con la salida completa. Scroll para mostrar los últimos tests + resumen `167 passed in X.XXs`.
**Qué mostrar:** La línea final verde de aprobación.

---

## 4. Tests frontend ejecutados (vitest)

**Comando:**
```bash
cd frontend && npm test
```

**Captura:** Terminal con `Test Files 21 passed`, `Tests 172 passed`.
**Qué mostrar:** El resumen final.

---

## 5. Tests Lambda ejecutados

**Comando:**
```bash
python -m pytest lambda/ -v
```

**Captura:** Terminal con `10 passed`.
**Qué mostrar:** Listado de los 10 tests Lambda.

---

## 6. Ejemplos de tests (6 backend + 6 frontend)

Para cada uno de los 12 ejemplos del informe (`docs/informe-pruebas.md`), tomar una captura que muestre:

| # | Test | Cómo capturar |
|---|------|---------------|
| B1 | Login + 2FA OTP | `python -m pytest tests/test_auth.py -v -k "2fa"` |
| B2 | Circuit Breaker | `python -m pytest tests/test_circuit_breaker.py -v` |
| B3 | BFF Dashboard | `python -m pytest tests/test_bff.py -v` |
| B4 | Upload Lambda | `python -m pytest lambda/upload_proxy/ -v` |
| B5 | Password Reset | `python -m pytest tests/test_password_reset.py -v` |
| B6 | Admin Estado | `python -m pytest tests/test_reports.py -v -k "admin"` |
| F1 | Login OTP input | `cd frontend && npx vitest run src/__tests__/Login.test.tsx` |
| F2 | Mapbox markers | `cd frontend && npx vitest run src/__tests__/MapboxStrategy.test.tsx` |
| F3 | Reporte submit | `cd frontend && npx vitest run src/__tests__/Reporte.test.tsx` |
| F4 | AdminPage tab | `cd frontend && npx vitest run src/__tests__/AdminPage.test.tsx` |
| F5 | ForgotPassword | `cd frontend && npx vitest run src/__tests__/ForgotPassword.test.tsx` |
| F6 | OfflineBanner | `cd frontend && npx vitest run src/__tests__/OfflineBanner.test.tsx` |

**Qué mostrar en cada captura:** El comando ejecutado + la línea verde `✓` o `PASSED`.

---

## 7. Pantalla de Swagger UI (opcional)

Si el endpoint está accesible:
- Abrir `https://api.keogh.lat/api/docs` en el navegador
- Capturar la interfaz Swagger mostrando los endpoints agrupados por tags (auth, reports, public, admin, alerts)

**Alternativa:** Abrir `docs/api-spec/openapi.json` en un editor de texto y capturar parte del JSON mostrando la estructura.

---

## 8. Resumen de herramientas

Captura de pantalla mostrando:
- `pytest --version` → versión de pytest
- `node --version` y `npm --version` → versiones de Node/npm
- `vitest --version` → versión de vitest

---

## Notas para las capturas

- Tomar capturas en **alta resolución** (no recortar demasiado)
- Preferir **formato PNG** para mejor calidad
- Incluir en cada captura: el **comando ejecutado** (parte superior de la terminal) y el **resultado** (parte inferior)
- Si la terminal tiene colores, mejor — muestra claramente los ✅ verdes
- Para el informe final PDF, insertar cada captura junto con el snippet de código correspondiente
