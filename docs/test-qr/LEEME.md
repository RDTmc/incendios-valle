# Variantes de Codificacion QR para Pruebas Android

> Generado: `docs/generar_variantes_qr.py`
> Destino comun: `https://incendios-valle.pages.dev/qr/`

## Matriz de variantes

| Archivo | Formato | Texto codificado | Teoria |
|---|---|---|---|
| `qr-control.png` | **URL plana** | `https://incendios-valle.pages.dev/qr/` | Misma URL que produccion. Sirve como control para verificar si el problema persiste. |
| `qr-urlto.png` | **URLTO** | `URLTO:https://incendios-valle.pages.dev/qr/` | Formato oficial del estandar ISO/IEC 18004 para codificar una URL en un codigo QR. Algunoslectores de QR en Android interpretan `URLTO:` como una instruccion directa de "abrir en navegador". |
| `qr-mebkm.png` | **MEBKM** (Bookmark) | `MEBKM:TITLE:Incendios Valle;URL:https://...;;` | Formato Mobile ESR Bookmark. Disenado para que el lector guarde un marcador web. En teoria, obliga al software a reconocer que hay una URL involucrada. |
| `qr-html.png` | **HTML anchor** | `<a href="https://...">Reportar incendio</a>` | Codifica la URL dentro de un tag HTML. Algunos escaneres extraen el valor del atributo `href` y lo ofrecen como enlace. |

## Como probar

1. Abrir cada imagen desde el telefono o imprimir las 4 variantes
2. Escanear con varios lectores:
   - **Camara nativa de Android** (Google Camera / Samsung Camera)
   - **Google Lens**
   - **Escaener QR de terceros** (pueden tener mejor deteccion)
3. Para cada variante, anotar:
   - Que opcion ofrece? (`Abrir enlace` / `Copiar texto` / `Buscar`)
   - Se abre en el navegador o dentro del lector?

## Resultados esperados

| Variante | Resultado optimista |
|---|---|
| `qr-control` | La mayoria de escaneres modernos lo detectan como URL, pero en algunos Android falla (problema actual) |
| `qr-urlto` | Deberia forzar el reconocimiento como URL porque el estandar ISO lo define explicitamente para eso |
| `qr-mebkm` | Podria fallar porque no todos los escaneres entienden MEBKM |
| `qr-html` | Depende del escaner; algunos extraen el href, otros muestran el HTML como texto |

## Recomendacion

Si `qr-urlto.png` funciona consistentemente en todos los dispositivos Android, migramos el QR oficial a ese formato. Si no, seguimos investigando.
