# Incendios PWA — Frontend

Aplicación web progresiva (PWA) para la gestión táctica de incendios forestales/urbanos. Dashboard público, reportes ciudadanos, panel admin.

## Tecnologías

- React 18 + TypeScript
- Vite 5
- Tailwind CSS 3
- Mapbox GL JS / Leaflet
- Zustand (estado global)
- Vitest + Testing Library (tests)
- react-router-dom v6

## Requisitos

- Node.js 22+
- npm

## Instalación

```bash
cd frontend
npm install
```

## Ejecución (desarrollo)

```bash
npm run dev
```

Abre en `http://localhost:5173`.

## Build producción

```bash
npm run build
```

El build se genera en `frontend/dist/`.

## Tests

```bash
# Todos los tests (una ejecución)
npm test

# Modo watch
npm run test:watch

# Con cobertura
npm run test:coverage
```

El reporte de cobertura se genera en `frontend/coverage/`.

## Estructura

```
frontend/
├── src/
│   ├── pages/        # Componentes de página
│   ├── components/   # Componentes reutilizables
│   ├── util/         # Utilidades (API, toast, device)
│   ├── __tests__/    # Tests unitarios
│   ├── App.tsx       # Layout + routing
│   └── main.tsx      # Entry point
├── public/           # Assets estáticos
├── package.json
└── vite.config.ts
```
