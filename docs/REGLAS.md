# REGLAS — Vinculantes para el LLM

## Idioma

- **TODO** el contenido generado (código, commits, comentarios, respuestas al usuario) debe ser en **ESPAÑOL**.
- No usar inglés a menos que el usuario lo pida explícitamente.

## Antes de hacer cambios

- **SIEMPRE presentar un plan** al usuario antes de ejecutar cualquier modificación.
- Explicar qué archivos vas a tocar, qué cambios harás, y por qué.
- Esperar la aprobación del usuario antes de proceder.

## Commits

- **NUNCA hacer commit sin preguntar al usuario primero.**
- Los mensajes de commit van en **ESPAÑOL**.
- Commits descriptivos: qué se cambió y por qué.

## Contexto y compactación

- Después de una compactación o inicio de nueva sesión, leer los 5 archivos en cascada (`GOAL.md` → `ARQUITECTURA.md` → `ESTADO.md` → `TAREAS.md` → `REGLAS.md`) antes de cualquier acción.
- No asumir información del contexto anterior después de compactación.

## Flujo de deploy

- **NUNCA editar archivos directo en EC2 sin replicar en el repo.** El CI/CD sobrescribe containers.
- El flujo correcto es: `cambio local → commit → push → CI/CD → esperar verde → validar en EC2`
- **No continuar** hasta que el workflow esté verde.
- **Lambda `upload-proxy`** se deploya MANUAL (zip + upload a AWS). No está en CI/CD.

## Prohibiciones

- **No editar archivos sin un plan aprobado.**
- **No hacer commit sin autorización explícita.**
- **No deployar sin pipeline CI/CD verde.**
- **No hardcodear secrets/tokens** — siempre usar env vars sin defaults.
- **No exponer información de error al cliente** — usar print para logging, mensaje genérico al usuario.
