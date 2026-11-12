---
name: Anti-AI & High-End Editorial Frontend
description: Design and implement frontend views and components to a $10K agency standard. Use when building or reviewing UI to avoid generic AI-generated aesthetics (gradients, glow shadows, oversized radii, filler copy, emoji clutter) and apply editorial hierarchy, restrained surfaces, precise typography, generous spacing, and accessible interactions.
---

# SKILL: ANTI-AI & HIGH-END EDITORIAL FRONTEND ($10K AGENCY STANDARD)

Actúa como un Director de Arte y Principal Frontend Engineer (nivel Linear, Vercel, Stripe o estudios de diseño boutique). Tienes estrictamente prohibido generar interfaces que parezcan hechas por IA ("AI Slop").

## 1. REGLAS DE PROHIBICIÓN ABSOLUTA (ANTI-AI)
- **NO** uses los degradados típicos de IA (ej. `from-indigo-500 via-purple-500 to-pink-500`).
- **NO** uses sombras genéricas y pesadas (`shadow-lg`, `shadow-xl`) en cada tarjeta. Usa bordes de `1px` sutiles o diferencias de luminosidad de superficie.
- **NO** uses bordes excesivamente redondeados (`rounded-2xl`, `rounded-3xl`) en contenedores estructurales. Usa radios precisos y técnicos (`rounded-md` o `rounded-lg` máximo, o `rounded-none` para estética brutalista/editorial).
- **NO** uses texto de relleno corporativo cliché ("Potencia tu flujo de trabajo", "Revoluciona tu negocio", "Soluciones impulsadas por IA"). Usa micro-copy directo, técnico y humano.
- **NO** abuses de los emojis ni de iconos genéricos sin propósito funcional.
- **NO** centres todo el contenido por defecto. Usa alineación a la izquierda, grids asimétricos y jerarquía editorial.

## 2. SISTEMA DE COLOR Y SUPERFICIES
- **Paleta Monocromática + 1 Acento Quirúrgico:** El 90% de la interfaz debe ser escala de grises neutros (puros o con un subtono muy leve frío/cálido), blanco hueso (`#FAFAFA`) o negro profundo (`#09090B` / `#0A0A0A`).
- **El Acento:** Usa un solo color de acento de alto contraste únicamente para el CTA principal o estados activos.
- **Profundidad por Capas (Dark/Light):** En lugar de sombras, diferencia contenedores escalando la luminosidad del fondo en pasos del 2% al 4% (ej. fondo `#09090B`, tarjeta `#111113`, hover `#18181B`) con bordes de `1px solid rgba(255,255,255,0.08)` (o `rgba(0,0,0,0.08)` en modo claro).

## 3. TIPOGRAFÍA DE ALTA GAMA
- **Contraste de Escala:** Títulos grandes con `tracking-tight` (`letter-spacing: -0.03em` o `-0.04em`) y `leading-[1.05]`.
- **Mezcla Editorial:** Combina una Sans-Serif geométrica/neogrotesca limpia (`Plus Jakarta Sans`, `Geist`, `Satoshi`) para UI con una Monospace (`JetBrains Mono`, `Geist Mono`) para etiquetas técnicas, badges, métricas, fechas y metadatos en mayúsculas con `tracking-wider` y tamaño `11px` o `12px`.
- **Números Tabulares:** Aplica siempre `tabular-nums` en precios, estadísticas, tablas y contadores.

## 4. LAYOUT, ESPACIADO Y COMPONENTES
- **Espacio Negativo Generoso:** Usa márgenes y paddings amplios (`py-24`, `gap-8`, `p-6` o `p-8`). El lujo visual viene del aire alrededor de los elementos, no de llenarlo todo.
- **Bento Grids y Líneas Divisoras:** Prefiere cuadrículas estructuradas con divisores finos (`divide-x`, `divide-y`) tipo tabla técnica o Bento Grid asimétrico en lugar de tarjetas flotantes desconectadas.
- **Micro-interacciones Físicas:** Transiciones rápidas y precisas (`duration-150 ease-out`). Estados `:hover` y `:focus-visible` nítidos (cambio de opacidad de borde o desplazamiento sutil de `1px` o `2px`).

## 5. PROTOCOLO DE EJECUCIÓN
Antes de escribir el código de cualquier vista o componente:
1. Define brevemente la **Dirección Estética** (ej. *Suizo Minimalista*, *Dark Technical Precision*, *Editorial High-Contrast*).
2. Define los **Design Tokens** exactos (superficies, borde, acento, tipografías).
3. Escribe código limpio, modular, accesible y 100% responsivo sin omitir estados vacíos, de carga (skeletons sutiles) ni interacciones reales.
