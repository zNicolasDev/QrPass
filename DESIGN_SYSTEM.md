# QrPass Design System — "Urban Transit Precision"

Referencia estética: fusión de **Transect** (retículas cartográficas), **Headcount**
(tipografía cívica de alto impacto) y **Nightdesk** (paneles operativos limpios).

Restricción técnica: **HTML5 y CSS3 puro**. Sin Tailwind, sin Bootstrap, sin React y
sin librerías CSS externas. El JavaScript no se toca: los IDs, clases y `data-*` que
consume `app.js` son contrato estable. Este documento describe la **apariencia**; no
autoriza cambios de estructura ni de comportamiento.

---

## 0. Mapa de implementación

| Archivo | Rol |
| --- | --- |
| `frontend/styles.css` | Base estructural y componentes originales. No se reescribe. |
| `frontend/premium.css` | Capa de acabado. Se carga **después** de `styles.css` y redefine tokens y apariencia. Fuente de verdad de este documento. |
| `frontend/login.css` | Sistema aplicado al acceso (`login.html`). |
| `frontend/login.html`, `pasajero.html`, `conductor.html` | Hojas de estilo con query param de versión. |
| `frontend/cache.js` | Service worker cache-first. `CACHE_NAME` versiona el shell. |
| `frontend/app.js` | Lógica y contrato de DOM. El markup que genera `renderDashboard()` puede reestructurarse con fines visuales **solo si** se conservan las expresiones de datos y los `data-action` que consume la lógica. |

Orden de cascada en las tres páginas: `styles.css` → `premium.css` → (`login.css`).
`premium.css` define los tokens canónicos; `styles.css` conserva sus propios valores
en `:root`, pero es sobreescrito por la capa premium al cargarse después.

### Regla de cache-busting

El service worker sirve assets de forma cache-first. Tras un cambio de tokens o de
`premium.css`:

1. Subir `premium.css?v=N` en `login.html`, `pasajero.html` y `conductor.html`.
2. Subir `login.css?v=N` solo en `login.html` si se tocó ese archivo.
3. Subir `styles.css?v=N` en las tres páginas si se tocó la base.
4. Subir `CACHE_NAME = "qrpass-shell-vN"` en `cache.js`.
5. Verificar en el navegador que la hoja cargada es la versión nueva, no la cacheada.

Si solo cambió `login.css`, basta con su query param y `CACHE_NAME`; `premium.css`
conserva su versión. No se debe publicar CSS sin subir `CACHE_NAME`: el shell seguiría
sirviendo la copia anterior.

Referencia de la última revisión: `styles.css?v=30`, `premium.css?v=39`,
`conductor.css?v=25`, `login.css?v=28`, `CACHE_NAME = "qrpass-shell-v53"`.

---

## 1. Tokens

### 1.1 Color y superficies

| Token | Valor | Uso |
| --- | --- | --- |
| `--bg-canvas` | `#F6F7F4` | Fondo papel mineral cálido del `body` y del gate de login |
| `--bg-surface` | `#FFFFFF` | Tarjetas, modales, inputs, tablas |
| `--bg-surface-subtle` | `#EEF2EE` | Bloques secundarios y contenedor del token QR |
| `--brand-forest` | `#0D261B` | Sidebar, banners oscuros, esquinas QR, placas de ruta y bordes de énfasis. **No es el color de texto corrido**: para eso existe `--text-primary` |
| `--brand-forest-hover` | `#163B2B` | Segundo extremo del degradado de banners |
| `--brand-lime` | `#A3E635` | Acento eléctrico: CTA principal y estados en vivo |
| `--brand-lime-hover` | `#8FCC2B` | Hover de CTA lima y esquina de escaneo del QR |
| `--text-primary` | `#0F1F18` | Texto principal |
| `--text-secondary` | `#52635B` | Texto secundario, cabeceras de tabla, labels |
| `--text-muted` | `#66756C` | Metadatos de baja jerarquía. Es el **piso** de contraste (~4.54:1 sobre canvas): no usar para texto menor a 12px ni para información crítica |
| `--border-hairline` | `1px solid rgba(13, 38, 27, 0.09)` | **Shorthand completo** de borde |
| `--border-strong` | `1px solid rgba(13, 38, 27, 0.14)` | Inputs y botones outline |
| `--shadow-elevation-1` | `0 2px 6px -1px rgba(13, 38, 27, 0.05), 0 1px 2px rgba(13, 38, 27, 0.03)` | Reposo de tarjetas |
| `--shadow-elevation-2` | `0 12px 24px -6px rgba(13, 38, 27, 0.09)` | Solo hover |
| `--shadow-overlay` | `0 24px 60px -12px rgba(13, 38, 27, 0.22), 0 2px 8px rgba(13, 38, 27, 0.06)` | Modales y diálogos |

**Borde: shorthand vs color.** `--border-hairline` y `--border-strong` incluyen
grosor, estilo y color, por lo que se usan en la propiedad `border` completa. Cuando
solo se necesita el **color** (por ejemplo `border-bottom-color` o un borde por lado)
se usa el alias `--line` (`rgba(13, 38, 27, 0.09)`) o `--line-strong`
(`rgba(13, 38, 27, 0.14)`). No mezclar: `border-bottom: var(--line)` es inválido.

### 1.2 Tipografía y movimiento

| Token | Valor | Uso |
| --- | --- | --- |
| `--font-mono` | `"SFMono-Regular", ui-monospace, Menlo, Consolas, monospace` | Metadatos técnicos |
| `--ease` | `cubic-bezier(0.22, 1, 0.36, 1)` | Curva única del sistema |
| `--transition` | `all 0.22s cubic-bezier(0.22, 1, 0.36, 1)` | Botones, tarjetas interactivas, tiles |
| `--radius-sm` | `6px` | Botones, inputs, token QR, placas de ruta |
| `--radius-md` | `10px` | Tarjetas de monto y método de pago, logo del login |
| `--radius-lg` | `12px` | Tarjetas, banners, modales, marcos QR |

Radio máximo en contenedores: **12px**. Las píldoras existentes (badges y scrollbar)
se conservan; no se añaden radios de `16px` o más a tarjetas, botones ni paneles.

### 1.3 Alias heredados

`styles.css` consume los nombres antiguos y `login.css` aún usa `--mint`. En
`premium.css` se mantienen como alias de los canónicos para no tocar HTML ni JS:

`--ink`, `--ink-soft`, `--ink-muted`, `--canvas`, `--paper`, `--line`, `--line-strong`,
`--forest`, `--forest-2`, `--forest-3`, `--mint`, `--mint-deep`, `--mint-soft`,
`--shadow-card`, `--shadow-hover`, `--shadow-modal`.

- `--mint-soft` = `#F2F8F4`: fondo de selección y del área de escaneo.
- `--forest-3` = `#1B4132`: fondo del ítem activo del sidebar.
- `--teal`, `--amber`, `--red` y sus variantes pálidas existen para estados
  semánticos heredados; no son parte de la paleta de acento y no deben usarse para
  decoración.

### 1.4 Reglas de uso

- El lima se reserva para **una acción principal por pantalla** y **estados en vivo**.
  Nunca como decoración, fondo de sección, texto largo ni ilustración.
- Las superficies blancas se separan del canvas por contraste natural y un hairline.
  La elevación 2 solo aparece en interacción; la 1 es el reposo.
- Todo borde es hairline con tinte verde; no se usan grises neutros genéricos.
- El bosque no compite con el texto: títulos y párrafos usan `--text-primary` /
  `--text-secondary`.

---

## 2. Textura y atmósfera (anti-IA)

- **Retícula técnica (Transect):** `body` y `.login-gate` llevan cuadrícula
  cartográfica de 32 px en CSS puro:

  ```css
  background-image:
    linear-gradient(to right, rgba(13, 38, 27, 0.03) 1px, transparent 1px),
    linear-gradient(to bottom, rgba(13, 38, 27, 0.03) 1px, transparent 1px);
  background-size: 32px 32px;
  ```

- **Banners principales** (`.balance-banner`, `.driver-shift-hero`,
  `.active-shift-banner`):

  ```css
  border: 1px solid rgba(255, 255, 255, 0.08);
  border-radius: var(--radius-lg);
  background-color: var(--brand-forest);
  background-image: linear-gradient(135deg, #0D261B 0%, #163B2B 100%);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.12),
    0 10px 30px -14px rgba(13, 38, 27, 0.3);
  ```

- **Tarjeta de tránsito** (`.wallet-hero`, resumen del pasajero): misma base
  bosque con **un único** radial lima espacial, no decorativo:

  ```css
  background-image:
    radial-gradient(circle at 85% 20%, rgba(163, 230, 53, 0.14), transparent 55%),
    linear-gradient(135deg, #0D261B 0%, #163B2B 100%);
  ```

  El radial marca la esquina de la billetera y sustituye a la ilustración. No se
  reproduce en otros banners ni se combina con un segundo foco de color.

- **Profundidad por luminosidad:** la cabecera de tabla y el hover de fila usan una
  banda `rgba(13, 38, 27, 0.018)` en lugar de otra tarjeta o sombra.
- **Prohibido:** degradados multicolor, radiales lima en banners (salvo el foco
  espacial único de `.wallet-hero`), glassmorphism generalizado, sombras grandes en
  reposo, emojis decorativos.

---

## 3. Tipografía y datos numéricos (Headcount)

### 3.1 Stack y escala

- **UI:** `"DM Sans", "Inter", system-ui, sans-serif`.
- **Metadatos:** `--font-mono`.

| Nivel | Regla |
| --- | --- |
| `h1` de página | `800`, `-0.03em`, `line-height: 1.1`, `clamp(26px, 3.2vw, 34px)` |
| `h1` de login | `800`, `-0.03em`, `1.1`, `clamp(28px, 7vw, 38px)` |
| `h2` de superficie | `800`, `-0.02em` |
| Párrafo de encabezado | `13.5px`, `--text-secondary`, ancho máximo `62ch` |
| Metadatos técnicos | `11px`, `600`, `0.08em`, mayúsculas, mono |
| Badges | `10.5px`, `600`, `0.05em`, mayúsculas, mono |
| Labels de formulario | `12–13px`, `600–700`, `--text-secondary` |

**Metadatos en monoespaciada:** `.eyebrow`, `.sidebar-caption`, `.modal-kicker`,
`.stat-label`, `.trip-table th`, `.topbar-date`. Transmiten precisión técnica y
diferencian el sistema de una UI genérica.

### 3.2 Cifras

`font-variant-numeric: tabular-nums` (más `font-feature-settings: "tnum" 1`) es
obligatorio en:

- Montos y saldos: `.stat-value`, `.balance-banner h2`, `.amount-option strong`,
  `.modal-total strong`, `.history-summary strong`.
- Contadores y relojes: `.bus-qr-countdown`, `.driver-live-count`,
  `.driver-live-payment`, `#driver-cash-expected`, `#driver-cash-counted`.
- Tablas: `.trip-table td`, `.receipt-list strong`, `.route-token`.

Sin esto, los valores bailan horizontalmente al actualizarse cada segundo.

### 3.3 Placas de ruta

Señalética física de bus (`.route-token`):

```css
width: auto;
min-width: 32px;
height: 26px;
padding: 0 6px;
border: 1.5px solid var(--brand-forest);
border-radius: 6px;
background: var(--bg-canvas);
color: var(--brand-forest);
font-family: var(--font-mono);
font-size: 12px;
font-weight: 700;
font-variant-numeric: tabular-nums;
```

Nota: a `devicePixelRatio: 1` el navegador puede reportar `1px` por snapping del
`1.5px`. La declaración CSS es la fuente de verdad; en pantallas retina se ve el
grosor completo.

---

## 4. Componentes

### 4.1 Superficies

- `.surface`, `.stat-card`, `.custom-amount`, `.quick-card`: `--border-hairline`,
  `--radius-lg`, `--bg-surface`, `--shadow-elevation-1`.
- `.amount-option`: `--radius-md`, `--bg-surface`, altura mínima `92px`.
- `.driver-totals`: un solo panel con barra de proporción y tres categorías;
  sin tarjetas internas ni separadores verticales.
- `.history-summary`: franja con borde inferior, sin tarjeta ni sombra.
- `.modal`: hairline, `--radius-lg`, `--shadow-overlay`, `padding: 0`, entrada
  `modal-enter 0.16s ease-out`.

### 4.2 Banners

Degradado bosque + brillo interno (ver §2). El texto es blanco o `#F2F7F3`. La
ilustración y los iconos dentro del banner usan **blanco a baja opacidad**
(`0.14` y `0.55`), nunca lima. `.wallet-hero` no lleva ilustración: el radial lima
ocupa ese rol y el chip de estado se limita a un punto de `6px`.

### 4.3 Botones

- Base: `--radius-sm`, `700`, `transition: var(--transition)`.
- **Primario lima** (`.button-mint`, `.login-submit`,
  `[data-action="scan-passenger-camera"]`): fondo `--brand-lime`, texto
  `--brand-forest`, brillo interno `inset 0 1px 0 rgba(255,255,255,0.32)`.
- **Hover:** `translateY(-2px)` + `--shadow-elevation-2`; el lima pasa a
  `--brand-lime-hover`.
- **Active:** `scale(0.98)`, sin `filter`.
- **Outline** (`.button-outline`): `--border-strong`, fondo blanco; hover con borde
  bosque y fondo `--mint-soft`.
- **Sidebar** (`.nav-link`): hover `translateX(2px)`; activo con fondo `--forest-3`,
  texto blanco y marcador `inset 2px 0 0 var(--brand-lime)`.
- La acción de cámara del escáner es la CTA de esa pantalla: 100% de ancho,
  `min-height: 62px`, icono propio en CSS.

### 4.4 Inputs, selects y textareas

```css
border: var(--border-strong);
border-radius: var(--radius-sm);
background: var(--bg-surface);
transition: border-color 0.22s var(--ease), box-shadow 0.22s var(--ease),
  background-color 0.22s var(--ease);
```

- **Foco:** `border-color: var(--brand-forest)`, `outline: none`,
  `box-shadow: 0 0 0 3px rgba(163, 230, 53, 0.3)`.
- **Foco de teclado:** `outline: 2px solid var(--brand-forest)` con `outline-offset`
  (1px en inputs, 2px en botones), para no depender del anillo lima.
- **Placeholder:** `#96A29A`.
- `textarea { resize: none; }` global: el layout no se rompe desde el navegador.
- El login fija `border-width: 1px` en sus inputs y altura mínima `48px`; el submit,
  `50px`.

### 4.5 Selección (montos y métodos de pago)

- `.amount-option:hover/:focus/:focus-visible/:active/.is-active`: borde bosque y
  fondo `--mint-soft`.
- `.method-choice:hover .method-tile`: borde `rgba(13,38,27,0.22)`,
  `translateY(-2px)`, elevación 2.
- `.method-radio:checked + .method-tile`: borde bosque, `--mint-soft`,
  anillo `0 0 0 3px rgba(163,230,53,0.2)`.
- El estado nunca depende solo del color: cambia borde, fondo y anillo.

### 4.6 Tablas

- `th`: mono `11px` mayúsculas, `0.08em`, `--text-secondary`, banda
  `rgba(13,38,27,0.018)` y hairline inferior.
- `td`: `#46564C`, hairline superior, `tabular-nums`.
- Hover de fila: misma banda de luminosidad, transición de `0.22s`.

### 4.7 Badges

Mono `10.5px`, mayúsculas, `0.05em`, borde de 1px con tinte del propio estado:

| Clase | Borde | Fondo |
| --- | --- | --- |
| `.service-status` | `rgba(13, 38, 27, 0.1)` | `rgba(255, 255, 255, 0.86)` |
| `.status-pill` | `rgba(86, 131, 96, 0.28)` | `rgba(234, 244, 235, 0.72)` |
| `.payment-tag` | `rgba(96, 129, 109, 0.24)` | `--bg-surface-subtle` |
| `.service-tag` | `rgba(154, 116, 60, 0.26)` | heredado |

Sin sombra: el badge se apoya en el borde, no flota.

### 4.8 Visor QR

**Nunca se muestra un QR suelto sobre blanco.** Hay dos marcos:

- **`.bus-qr-frame`** (visor de cobro del conductor): padding `20px`, hairline,
  `--radius-lg`, fondo blanco, `inset 0 1px 0 #fff` + elevación 1, imagen de hasta
  `232px`. Cuatro esquinas técnicas de 22×2px: superior izquierda, superior derecha e
  inferior derecha en `--brand-forest`; **inferior izquierda en
  `--brand-lime-hover`** como marca de escaneo.
- **`.qr-frame`** (modales y vistas de detalle): hairline, `--radius-lg`, elevación 1
  y dos esquinas bosque de 16×2px (superior izquierda e inferior derecha).

El contador (`.bus-qr-countdown`) va en `--text-secondary`, `12.5px`, tabular.

### 4.9 Token JWT

El token manual del conductor es una **barra horizontal compacta**, no un textarea:

- `.qr-token-row`: flex en una fila, `gap: 8px`, fondo `#F4F7F5`, borde
  `1px solid rgba(13,38,27,0.1)`, radio `10px`, padding `6px 8px 6px 12px`.
- `.qr-token-full`: input de una línea, `flex: 1`, `nowrap`, `overflow: hidden`,
  `text-overflow: ellipsis`, sin borde ni fondo, mono `0.8rem`, color `#52635B`.
- Acciones `Copiar` y `Nuevo QR`: a la derecha, `padding: 6px 12px`,
  `font-size: 0.8rem`, `white-space: nowrap`.
- El foco de teclado sustituye el borde por un outline bosque de 2px.

### 4.10 Toasts

- Base en `styles.css`: blanco, radio `9px`, texto `#426B50`, animación `toast-in`.
- En móvil: anclados arriba (`top: 16px`), centrados, ancho máximo `420px`,
  animación `toast-in-top`.
- Error (`.toast.is-error`): texto `#9A5045`, borde `#F1D8D2`.

### 4.11 Scrollbar

10px, thumb `rgba(13,38,27,0.16)` con `background-clip: content-box`; hover `0.28`.
El track queda transparente.

### 4.12 Bento del resumen del pasajero

Sustituye el banner de bienvenida y las cuatro tarjetas iguales por una billetera de
tránsito con jerarquía asimétrica. El markup se genera en `renderDashboard()`
(`app.js`); el estilo vive en `premium.css`.

**Estructura**

- `.hero-bento-grid`: grid de dos columnas `1.35fr 1fr`, `gap: 16px`,
  `align-items: stretch`, margen inferior `21px`.
- **Columna izquierda — `.wallet-hero`**: tarjeta bosque `#0D261B` que fusiona el
  banner y el saldo. Flex vertical con `space-between` y altura mínima `292px`:
  fila superior (eyebrow `PAGO DEL PASAJE` + chip `.wallet-status`), cuerpo (label,
  saldo y nota) y fila de acciones (CTA lima + `.button-ghost`).
  - Saldo: `clamp(2.25rem, 3.5vw, 3rem)`, `800`, `-0.04em`, `tabular-nums`, blanco.
  - Sin ilustración de bus. El radial lima y el `inset 0 1px 0` aportan profundidad.
  - `.wallet-status`: chip de radio `6px`, mono `10px`, mayúsculas, punto lima.
- **Columna derecha — `.wallet-metrics`**: sub-grid vertical `auto 1fr`.
  - `.metric-card-fare`: tarjeta horizontal; copy a la izquierda (título con icono +
    detalle) y valor a la derecha (`1.5rem`, `800`, `nowrap`).
  - `.metric-pair`: dos columnas `1fr 1fr` con `gap: 16px` para viajes y método.
- `.metric-card`: superficie blanca, hairline, `--radius-lg`, elevación 1, flex
  vertical `space-between`.

**Reglas**

- Títulos de métrica: mono `0.72rem`, `600`, `0.06em`, mayúsculas; el icono se
  reduce a `16px` inline, sin recuadro de fondo.
- Valores: `1.5rem`, `800`, `-0.03em`; el método baja a `1.05rem` y permite
  `overflow-wrap: anywhere`.
- Las tarjetas de métricas no son interactivas: no llevan hover ni elevación 2.
- Entre `901px` y `1024px`, donde el sidebar aún resta ancho, el padding baja a
  `16px` y `.metric-title` hace wrap para que ninguna palabra se recorte.
- A `max-width: 900px` el grid colapsa a una columna; `.metric-pair` conserva sus
  dos columnas. A `520px` se aprieta el padding del hero y de las tarjetas.
- Contrato: se conservan `.stat-label`, `.stat-value`, `.stat-note` y los
  `data-action="pay-qr"` / `data-action="quick-top-up"`.

### 4.13 Panel del conductor (Mi turno y pagos)

El markup vive en `renderDriverDashboard()` y `renderBusQrBlock()` (`app.js`), y se
repinta parcialmente por `paintBusQr()` y `paintDriverPayments()`. Los `id` y
`data-action` son contrato funcional: no se renombran al ajustar la capa visual.

**Encabezado y banner de turno**

- Encabezado compacto: `OPERACIÓN DE TRANSPORTE` y título `Mi turno` con
  `letter-spacing: -0.03em` y `800`; sin subtítulo explicativo.
- `.active-shift-banner` es una ficha de telemetría: flex horizontal con
  `justify-content: space-between`, `align-items: center`, `gap: 16px`,
  padding `15px 18px`, fondo `#0D261B` con brillo radial lima y líneas técnicas
  verticales.
- `.shift-route-badge`: placa lima `48×48` (`#A3E635` sobre `#0D261B`), radio
  `12px`, `800`, `1.4rem`, con halo suave.
- `.shift-unit-id h2`: `Ruta N` en blanco `800`; `.shift-plate` imita una
  matrícula (`monospace`, `0.8rem`, tracking `0.08em`, fondo
  `rgba(255,255,255,0.1)`, borde `rgba(255,255,255,0.18)`, radio `5px`).
- Bloque derecho: `EN RUTA` con pulso lima animado (`@keyframes shift-pulse`),
  badge `#driver-shift-reference` (`TUR-N`) y datos `HH:mm | N abordajes`
  separados por `.shift-divider` de `1px`.
- Los `id` `#driver-route-name`, `#driver-vehicle-plate`,
  `#driver-shift-started`, `#driver-boardings-count` y
  `#driver-shift-reference` exponen ruta, placa, hora, abordajes y turno.
- A `560px` el banner hace wrap: identidad arriba y telemetría a todo el ancho;
  la placa de ruta baja a `44px`.

**QR y token**

- El subtítulo del QR es una línea: `Código de uso único · Se renueva
  automáticamente cada 60 s`; en escritorio no hace wrap.
- El token usa la barra compacta de §4.9. `#bus-qr-token` conserva su `id` y el
  tipo de control de una línea; `Copiar` y `Nuevo QR` viajan dentro de
  `#bus-qr-live` y siguen funcionando por delegación de eventos.
- Solo existe un `data-action="refresh-bus-qr"` en el DOM.

**Recaudo**

- `.driver-totals`: un solo panel con `padding: 18px 20px 16px`; el total
  (`#driver-total-all`) es la cifra protagonista (`clamp(28px, 3.4vw, 38px)`,
  `800`, `tabular-nums`).
- `.driver-share`: barra de proporción `8px`, radio `999px`, fondo `#E5ECE7`,
  `overflow: hidden`, `display: flex`. Los segmentos usan `flex-grow` inline según
  el monto: Efectivo `#0D261B`, QR / Saldo `#A3E635`, Tarjeta `#4D7C66`.
- `.driver-totals-list`: tres columnas con punto indicador de `8px`, nombre corto
  en mono `10.5px` y monto en negrita; a `380px` pasa a filas apiladas.
- Sin textos secundarios de conteo: solo nombre y monto.

**Tareas**

- `.driver-work-grid`: `1fr 1fr`, `gap: 16px`, `align-items: stretch`; colapsa a
  una columna a `max-width: 760px`.
- `Pago manual`: grid POS de dos columnas (`1fr 1fr`, `gap: 12px`). Cada
  `.driver-pay-tile` es vertical y centrado, radio `14px`, con icono circular de
  `40px` sobre `#EEF4F0`, nombre en negrita y badge lima con `+ $ 3.300`.
  `data-action="driver-payment"` y `data-method` intactos.
- `Cerrar turno`: `.driver-cash-box` (`#F4F7F5`, radio `12px`, padding
  `12px 16px`) muestra `Efectivo esperado` y `#driver-cash-expected` en grande.
  El input lleva prefijo `$` absoluto y el botón ocupa el 100% con icono check,
  borde `rgba(185,28,28,0.25)`, texto `#991B1B` y hover `#FEF2F2`.
- El punto del footer del sidebar usa lima `#A3E635`, igual que el estado activo.

**Historial del turno**

- Cabecera `Historial del turno` con resumen `N pagos · $ N` a la derecha
  (`#driver-ledger-count`).
- Cada fila muestra icono cuadrado de `32px` por medio de pago (QR, efectivo,
  tarjeta), la hora compacta (`HH:mm`) y el monto alineado a la derecha.
- Estado vacío gráfico: icono de recibo al `35%` de opacidad y
  `Sin movimientos aún`.
- Se eliminó la lista duplicada `Pagos recibidos` bajo el QR y la nota verde de
  manual; el sondeo usa `#driver-ledger-body` como ancla.

---

## 5. Layout y responsive

| Contexto | Regla |
| --- | --- |
| Sidebar | `250px`, fijo, fondo `--brand-forest` |
| Contenido | `width: min(100%, 1300px)`, padding `34px 43px 30px` |
| Topbar | blanco, padding `0 43px`; en móvil `0 20px` |
| Resumen del pasajero | Bento `1.35fr 1fr` con `gap: 16px`; colapsa a `1fr` en `max-width: 900px` |
| Panel del conductor | Recaudo en panel único con barra de proporción; POS `1fr 1fr`; tareas `1fr 1fr → 1fr` a `760px`; categorías apiladas a `380px` |
| Breakpoint principal | `max-width: 768px` |
| Contenido móvil | padding `24px 20px 28px` |
| Footer móvil | `10px 20px calc(16px + env(safe-area-inset-bottom))` |
| Login | tarjeta `min(100%, 440px)`, padding `40px 38px`; a `450px`, `28px 22px` |

### Móvil (`max-width: 768px`)

- `<main class="main-area">` con `padding-bottom: calc(100px + env(safe-area-inset-bottom))`
  para que la barra flotante nunca solape contenido ni footer.
- Barra inferior (`.mobile-tabbar`): fija, `border-radius: 10px`, fondo
  `rgba(255,255,255,0.82)`, `box-shadow: 0 10px 30px -8px rgba(13,38,27,0.18)` y
  `backdrop-filter: blur(12px) saturate(1.08)`.
- *Toasts* arriba (`top: calc(16px + env(safe-area-inset-top))`), laterales `16px`,
  centrados; no tapan controles inferiores ni el QR.
- Recaudo del conductor a ancho completo: la barra de proporción pasa debajo del
  total; las tres categorías siguen en fila y se apilan a `380px`. Las tareas se
  apilan a una columna a `760px`.
- El bento del pasajero mantiene `.metric-pair` en dos columnas incluso a `390px`;
  a `901–1024px` ajusta padding y permite wrap del título para no recortar texto.
- Sin overflow horizontal en 390, 768, 1024 ni 1440.

---

## 6. Accesibilidad y movimiento

- **Foco visible:** contorno bosque de 2px; `outline-offset` 1–2px. Nunca se elimina
  el foco sin reemplazo.
- **Contraste:** `--text-secondary` supera AA sobre canvas; `--text-muted` es el piso
  (~4.54:1) y no debe usarse por debajo de 12px.
- **Estado no cromático:** selección y error combinan borde, fondo y texto, no solo
  color.
- **`prefers-reduced-motion: reduce`:** animaciones y transiciones a `0.01ms`,
  `transform: none` en hovers de botones, tarjetas, tiles, nav y cámara.
- **`prefers-contrast: high`:** tokens a negro/blanco, bordes de 2px en botones,
  superficies y métricas; el fondo pierde la retícula.
- **`pointer: coarse`:** objetivos táctiles del login a `44px` mínimo.

### Estados base heredados

Estos estados viven en `styles.css` y aún no están tokenizados. Se documentan para
mantener coherencia; si se tocan, migrarlos a tokens:

| Estado | Clase | Apariencia actual |
| --- | --- | --- |
| Carga | `.workspace-loading` | Pantalla centrada, `14px`, `--ink-soft` |
| Error de carga | `.workspace-load-error` | Texto `#9C4E42` |
| Error de login | `.login-error` | Fondo `#FFF3F0`, borde `#F0D2CB`, texto `#9C4E42`, radio `6px` |
| Tabla vacía | `.empty-row` | Texto centrado `#8A9791` |
| Toast de error | `.toast.is-error` | Texto `#9A5045`, borde `#F1D8D2` |

---

## 7. Excepciones de lima

El acento está contenido. Estas son las **únicas** apariciones aprobadas:

1. CTA primaria: `.button-mint`, `.login-submit`, acción de cámara del escáner.
2. Pulso de turno activo: `.active-shift-pulse`.
3. Anillo de foco de inputs y de selección (`rgba(163,230,53,0.3)` / `0.2`).
4. Marcador del ítem activo del sidebar (`inset 2px 0 0`).
5. Marca del logo (`.brand-mark`).
6. Una esquina del visor QR de cobro (`--brand-lime-hover`).
7. Punto de estado de `.wallet-status` (`6px`, `--brand-lime`).
8. Foco radial de `.wallet-hero` (`rgba(163,230,53,0.14)` sobre bosque): único,
   espacial y no reutilizable en otros banners.
9. Punto del perfil en el footer del sidebar (`.profile-status`, `#A3E635`), alineado
   con el estado conectado.

Fuera de esta lista, el lima es un defecto. En particular: no se usa en
ilustraciones, iconos de saldo, radiales de banner fuera de `.wallet-hero`, fondos de
sección ni texto.

---

## 8. Checklist de aceptación

Antes de dar por cerrado un cambio visual:

- [ ] Los tres HTML cargan la versión vigente de `premium.css`; `login.html`
      también la de `login.css`; `CACHE_NAME` fue incrementado.
- [ ] `GET` de la hoja devuelve la versión nueva (no la del service worker).
- [ ] Tokens exactos: canvas `#F6F7F4`, surface `#FFFFFF`, subtle `#EEF2EE`,
      bosque `#0D261B`, hover `#163B2B`, lima `#A3E635`, texto `#0F1F18` /
      `#52635B`, hairline `rgba(13,38,27,0.09)`.
- [ ] `h1`: `800`, `-0.03em`, `1.1`.
- [ ] Montos, contadores y horas: `tabular-nums`.
- [ ] Placa de ruta: `1.5px` bosque, radio `6px`, `700`, fondo canvas, mono.
- [ ] Input en foco: borde bosque, anillo lima `0.3`, `outline: none`; foco de
      teclado con contorno bosque de 2px.
- [ ] Ningún `textarea` redimensionable.
- [ ] QR siempre enmarcado; esquinas bosque y la lima de escaneo en su lugar.
- [ ] Hover eleva 2px con `--shadow-elevation-2`; active comprime a `0.98`.
- [ ] Lima solo en las excepciones de §7.
- [ ] Resumen del pasajero: saldo dentro de `.wallet-hero`, tres métricas
      secundarias y sin `.welcome-banner` ni `.stats-grid` en el DOM.
- [ ] Bento sin overflow interno a 901, 1024 y 1440 px.
- [ ] Panel del conductor: encabezado sin subtítulo, ficha de telemetría con placa
      de ruta lima, matrícula y `TUR-N` con pulso, token en barra de una línea,
      recaudo con barra segmentada, POS de dos columnas, ficha de arqueo e
      historial con iconos. Sin `Pagos recibidos` duplicado ni nota de manual.
- [ ] Contador, copia de token, `Nuevo QR`, registro Efectivo/Tarjeta y cierre de
      turno siguen funcionando con los mismos `id` y `data-action`.
- [ ] A 390, 768, 1024 y 1440: sin overflow horizontal.
- [ ] En móvil: `main` con 100px, toasts a 16px, tabbar con blur, footer visible.
- [ ] `prefers-reduced-motion` y `prefers-contrast: high` no rompen el layout.
- [ ] Ningún ID, clase funcional ni `data-*` de `app.js` fue renombrado.

---

## 9. Deuda conocida

- Los estados de carga, error y vacío todavía usan valores literales en
  `styles.css`; conviene migrarlos a `--red`, `--red-pale` y `--text-muted`.
- `styles.css` conserva las reglas de `.welcome-banner`, `.welcome-illustration` y
  `.stats-grid`. El resumen del pasajero ya no las renderiza: son código muerto
  heredado que puede retirarse en una limpieza de la base.
- Los badges heredan `text-transform` y tamaños de `styles.css`; el ajuste fino
  vive en `premium.css`.
- `--forest-3` (`#1B4132`) es el único color de sidebar que no proviene de un token
  canónico; se mantiene como alias por compatibilidad.
- El snapping de `1.5px` a `1px` en DPR 1 es esperado, no un bug.
- Quedan literales sin tokenizar en componentes concretos: `td` (`#46564C`), borde
  punteado del token (`rgba(13,38,27,0.22)`) y placeholder (`#96A29A`).
