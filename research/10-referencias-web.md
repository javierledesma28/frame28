# Referencias de diseño web para el sitio de producto AI de T28

Documento de trabajo para promptear el diseño del nuevo sitio de producto dentro del ecosistema Think28 (t28.io).

**Nota sobre el stack:** la columna "Confianza" indica si el stack está confirmado por fuentes públicas (✅) o es una estimación basada en el comportamiento del sitio (⚠️). Antes de tomar decisiones técnicas, conviene validarlo con Wappalyzer o BuiltWith.

---

## Referencias base (las que originaron la búsqueda)

| Sitio | Stack | Confianza | Lo mejor |
|---|---|---|---|
| Vercel (vercel.com) | Next.js, React, tipografía Geist, Vercel Edge | ✅ | Paleta restringida, bento grids, rejilla técnica; la función es la marca |
| TypeSafe AI (typesafe.ai) | Framer + efectos WebGL de Unicorn Studio | ✅ | Estética de laboratorio retro-computacional: ASCII, Game of Life, base64 decorativo, métricas duras como héroe |

---

## Lista 1 — Sitios trascendentales (claridad, producto, sistema de diseño)

| # | Sitio | Stack | Confianza | Lo mejor en una línea |
|---|---|---|---|---|
| 1 | Linear (linear.app) | React / Next.js, Inter Display, animaciones CSS/JS propias | ⚠️ | Definió la estética "dev tool premium": oscuro, gradientes sutiles, precisión tipográfica |
| 2 | Cursor (cursor.com) | Next.js, React | ⚠️ | Muestra código real en un editor real en vez de gradientes de marketing |
| 3 | Supabase (supabase.com) | Next.js, Tailwind CSS (código abierto en su monorepo) | ✅ | La versión más disciplinada de la estética Linear en infraestructura; el hero es el producto en vivo |
| 4 | Resend (resend.com) | Next.js, Tailwind, Radix UI, Vercel | ⚠️ | Minimalismo extremo en negro con 3D sobrio; el snippet de código es el mensaje |
| 5 | Raycast (raycast.com) | Next.js, React | ⚠️ | Vende una herramienta que vive dentro de otra: el producto se ve como si ya lo usaras |
| 6 | Featherless (featherless.ai) | No verificado (probable Framer o Webflow) | ⚠️ | Concepto de origami de isotipo a ilustración; AI "ligera y precisa" frente al monolito oscuro |
| 7 | Composio (composio.dev) | No verificado (probable Next.js) | ⚠️ | Refracción con ruido, fade cinematográfico en scroll, transición wireframe → píxel → grano |
| 8 | Modal (modal.com) | SvelteKit | ⚠️ | Verde neón sobre negro, código en primer plano; "hecho por ingenieros para ingenieros" |
| 9 | Wispr Flow (wisprflow.ai) | No verificado (probable Webflow) | ⚠️ | Contrapunto editorial: fondo crema, serif elegante, animación que explica el producto sin texto |
| 10 | Anthropic (anthropic.com) | No verificado | ⚠️ | Autoridad enterprise: contención visual, lenguaje medido, wordmark serif de institución |

---

## Lista 2 — Sitios disruptivos y de efecto wow (techo técnico)

| # | Sitio | Stack | Confianza | Lo mejor en una línea |
|---|---|---|---|---|
| 11 | Lusion (lusion.co) | Renderizador WebGL propio (sin Three.js), simulación de tela, fluidos, iluminación global aproximada | ✅ | El techo técnico actual del WebGL en navegador sin sacrificar usabilidad |
| 12 | Oryzo (oryzo.ai) | Three.js, WebGL, GSAP (por Lusion) | ✅ | Render 3D de producto para una marca .ai: materializa algo intangible |
| 13 | Igloo Inc (igloo.inc) | WebGL a medida, UI renderizada en WebGL con SDF, simulación de fluidos propia | ✅ | Site of the Year de Awwwards; glitches por shader sin coste de rendimiento |
| 14 | Active Theory (activetheory.net) | Framework WebGL propio | ⚠️ | 3D de producción que funciona en móvil; formas geométricas que responden a la interacción |
| 15 | IVRESS (por Utsubo) | Three.js, renderizador WebGPU, TSL, fallback WebGL | ✅ | La tecnología que viene: WebGPU en producción |
| 16 | Stripe (stripe.com) | Shaders WebGL sobre geometría 2D (gradiente animado) | ✅ | Wow elegante y barato: luz refractada en vidrio con fragment shaders |
| 17 | Apple, páginas de producto (apple.com/iphone) | WebGL con materiales PBR en tiempo real, scroll-driven | ✅ | El 3D se vuelve invisible como tecnología: todo sirve a la historia |
| 18 | Sahara AI (saharaai.com) | No verificado (3D interactivo en hero) | ⚠️ | Wow contenido en un sitio AI: 3D interactivo + rejilla técnica + hovers con rotación |
| 19 | Shopify Editions (shopify.com/editions) | Three.js, WebGL | ✅ | Cómo lanzar muchas funcionalidades de software como una experiencia 3D |
| 20 | Bruno Simon (bruno-simon.com) | Three.js + motor de física | ✅ | La interacción como mensaje: el sitio es un juego |

---

## Detalle por sitio — qué robar de cada uno

### 1. Linear
- Hero oscuro con gradiente radial muy sutil y luz que "rebota" en los bordes de las tarjetas.
- Tipografía grande, apretada (tracking negativo), jerarquía impecable.
- Capturas de producto reales, recortadas y animadas, nunca mockups genéricos.

### 2. Cursor
- El producto real es el hero: código ejecutándose en el editor.
- Cero adornos innecesarios; la credibilidad viene de mostrar, no de prometer.

### 3. Supabase
- El hero es el playground real del producto grabado en vivo.
- Sistema de diseño muy consistente (verde de marca sobre negro), secciones modulares reutilizables.

### 4. Resend
- Negro absoluto, objetos 3D sobrios y metálicos.
- El snippet de integración es el call to action principal.

### 5. Raycast
- Muestra el producto en contexto (dentro del sistema operativo).
- Ideal como modelo si el producto de T28 es un plugin o extensión.

### 6. Featherless
- Un concepto visual (origami) aplicado a todo: logo, ilustraciones, iconografía.
- Rompe el cliché "AI = oscuro y frío".

### 7. Composio
- Fondos de refracción con ruido granulado.
- Narrativa visual en capas: wireframe → píxel → gradiente.
- Pestañas para explicar funcionalidades sin saturar.

### 8. Modal
- Color de acento único y agresivo sobre negro.
- Ejemplos de código como contenido principal; tono técnico sin concesiones.

### 9. Wispr Flow
- Paleta crema + serif = sofisticación editorial.
- Animaciones de trazo suaves y coherentes en toda la página.

### 10. Anthropic
- Contención visual extrema para transmitir confianza.
- Ideal como modelo de tono para clientes regulados (salud, banca, sector público).

### 11. Lusion
- Escena 3D abstracta que reacciona al ratón y se transforma con el scroll.
- Equilibrio entre experimento y navegabilidad.

### 12. Oryzo
- Render 3D de producto con materiales realistas.
- Referencia directa para "dar cuerpo" a un producto AI.

### 13. Igloo Inc
- UI íntegramente en WebGL (texto con SDF, glitches por shader).
- Simulación de fluidos y estética helada/futurista.

### 14. Active Theory
- Experiencia WebGL a pantalla completa, mitad arte, mitad interfaz.
- Rendimiento cuidado incluso en móvil.

### 15. IVRESS
- Renderizado WebGPU con fallback WebGL.
- Señal de "próxima generación" a nivel técnico.

### 16. Stripe
- Gradiente animado por shader que simula vidrio y luz.
- Máximo impacto con bajo coste de rendimiento: muy aplicable.

### 17. Apple
- Scroll-driven storytelling con 3D en tiempo real.
- Cada efecto justifica su existencia en la historia del producto.

### 18. Sahara AI
- Elemento 3D interactivo en el hero + rejilla de fondo.
- Animaciones de hover que dan vida a secciones estáticas.

### 19. Shopify Editions
- Lanzamiento de decenas de funcionalidades como un recorrido 3D.
- Modelo para presentar un ecosistema de productos (Hub28, Synapse28, Acimut…).

### 20. Bruno Simon
- Mundo 3D navegable con físicas.
- Inspiración para un easter egg o una demo interactiva, no para la home completa.

---

## Síntesis para el prompt de T28

**Dirección recomendada:** disciplina de Linear/Vercel en estructura + un único momento wow en el hero (estilo Stripe o Igloo) + tono de confianza tipo Anthropic para audiencia regulada.

**Palabras clave de diseño para promptear:**
- Dark mode, fondo #0a0a0a (coherente con t28.io)
- Rejilla técnica sutil de fondo, bento grid para funcionalidades
- Tipografía sans geométrica grande con tracking negativo + monoespaciada para datos y código
- Hero con shader WebGL (gradiente refractado o campo de partículas) que reacciona al ratón
- Producto real visible arriba del pliegue (captura animada o demo interactiva)
- Métricas duras como elementos visuales (estilo TypeSafe)
- Detalles retro-computacionales: ASCII, coordenadas, versión del producto, reloj en vivo
- Un único color de acento
- Micro-animaciones en hover, fade cinematográfico en scroll

**Opciones de stack según el nivel de control:**
- Rápido y visual: Framer + Unicorn Studio (lo que usa TypeSafe)
- 3D sin código: Spline embebido
- Control total: Next.js + Tailwind + React Three Fiber (Three.js) + GSAP, desplegado en Vercel o en infraestructura propia

**Prompt base sugerido:**

> Diseña la landing de un producto AI del ecosistema Think28 (t28.io). Estructura y sistema de diseño inspirados en Linear y Vercel: modo oscuro (#0a0a0a), rejilla técnica sutil, bento grid, tipografía sans grande con tracking negativo y monoespaciada para datos. El hero tiene un único efecto WebGL (gradiente refractado tipo Stripe) que reacciona al ratón, y muestra el producto real en funcionamiento. Incluye métricas de rendimiento como elementos visuales y detalles retro-computacionales al estilo TypeSafe AI. El tono transmite la confianza de Anthropic para clientes de salud, banca y sector público. Un único color de acento. Stack: Next.js, Tailwind, React Three Fiber, GSAP.
