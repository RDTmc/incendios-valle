# Manual de Diseno para el Afiche Municipal
## Campana: Incendios Valle del Sol — Reporte Ciudadano de Emergencia

> Version: 1.0 — Fase 0
> Emisor: Direccion de TI, Municipalidad de Valle del Sol
> Destinatario: Departamento de Diseno Grafico / Imprenta Municipal

---

## 1. Disposicion Obligatoria del Afiche

Todo afiche impreso DEBE contener **dos elementos fisicos inseparables**:

```
+-------------------------------------------------------+
|                                                       |
|   [ LOGO MUNICIPAL ]   [ ICONO FUEGO ]               |
|                                                       |
|   REPORTE DE INCENDIOS                                |
|   Escanea y reporta en 30 segundos                    |
|                                                       |
|                 +-----------+                         |
|                 | QR OFICIAL|                         |
|                 |           |                         |
|                 +-----------+                         |
|                                                       |
|   Si tu telefono lee el codigo como texto:            |
|   -> Presiona COPIAR y pegalo en Chrome/Safari       |
|   -> O escribe incendios-valle.pages.dev              |
|   -> O busca 'Incendios Valle del Sol' en Google      |
+-------------------------------------------------------+
```

---

## 2. Archivo del Codigo QR

| Atributo | Valor |
|---|---|
| Archivo | `docs/qr-pwa-incendios.png` |
| Dimensiones sugeridas | Minimo **3 cm x 3 cm** en impresion |
| Formato | PNG, 740 bytes, fondo transparente |
| URL codificada | `https://incendios-valle.pages.dev/qr/` |
| Resolucion recomendada | 300 DPI en impresion |

> **Importante:** No modificar, recolorear ni anadir bordes decorativos al QR.
> El QR debe imprimirse sobre fondo blanco con margen de seguridad de 5 mm.

---

## 3. Texto de Contingencia (Obligatorio)

Ubicacion: **Inmediatamente debajo del codigo QR**, centrado, en un recuadro de fondo amarillo suave o borde punteado.

### Texto exacto a incluir:

> **Si tu telefono lee el codigo como texto:**
> 1. Presiona **Copiar**
> 2. Abre **Google Chrome** o **Safari**
> 3. Pega la URL en la barra de direcciones
> 4. Presiona Enter
>
> O escribe manualmente: **incendios-valle.pages.dev**
>
> *Funciona en Samsung, Apple, Motorola, Xiaomi/Redmi y todos los Android.*

### Especificaciones de diseno:

- **Tamanio de fuente:** Minimo 10 pt en afiches A3, 12 pt en A2 o mayores.
- **Color de fondo del recuadro:** `#FFF9C4` (amarillo claro) o borde punteado `#F59E0B`.
- **Texto del boton Copiar:** En **negrita** para destacar la accion principal.
- **Icono opcional:** Agregar icono de dedo senalando o ✋ al inicio del bloque.

---

## 4. Estructura General del Afiche

```
+-------------------------------------------------------+
|  [Escudo Municipal]   Incendios Valle del Sol         |
|  ---------------------------------------------------  |
|  REPORTE CIUDADANO DE EMERGENCIA                      |
|  Escanea y reporta incendios en tiempo real           |
|                                                       |
|  [ QR ]                                               |
|                                                       |
|  +-----------------------------------------------+   |
|  | Si tu telefono lee el codigo como texto:      |   |
|  | 1. Presiona COPIAR                            |   |
|  | 2. Abre Chrome/Safari                         |   |
|  | 3. Pega y entra                               |   |
|  | O escribe: incendios-valle.pages.dev          |   |
|  +-----------------------------------------------+   |
|                                                       |
|  ---                                                 |
|  App gratuita. No requiere registro para emergencias.|
+-------------------------------------------------------+
```

---

## 5. Prueba de Impresion

Antes de la tirada final:

1. Imprimir **una copia de prueba** en el mismo papel y formato final.
2. Escanear el QR con **3 telefonos distintos** (uno Xiaomi/Redmi, uno Samsung, un iPhone).
3. Verificar que la URL `https://incendios-valle.pages.dev/qr/` se abre correctamente.
4. Si el QR no se lee a 30 cm de distancia, **aumentar el tamanio del QR**.

---

## 6. Paleta de Colores Oficial

| Elemento | Color | Hex |
|---|---|---|
| Fondo del afiche | Blanco | `#FFFFFF` |
| Barra superior | Rojo incendio | `#EF4444` |
| Texto principal | Negro | `#1F2937` |
| Fondo texto contingencia | Amarillo claro | `#FFF9C4` |
| Borde contingencia | Amarillo | `#F59E0B` |
| Texto secundario | Gris | `#6B7280` |

---

## 7. Contacto Tecnico

Para ajustes sobre el QR o la URL de destino, contactar a la Direccion de TI municipal antes de la impresion final. No modificar la URL del QR sin autorizacion.
