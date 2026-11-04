# Diseño de la aplicación — Rutas del Paisaje Cultural Cafetero

## 1. Qué es y quién la usa

Es una herramienta de trabajo, no una página para vender: se usa en la sustentación para mostrar
en vivo Dijkstra, QuickHull, Held-Karp y la voraz sobre la red vial real, y para enseñar las tablas
y gráficas de los experimentos. Escena física: un salón de clase con un videoproyector y un jurado
con portátil. La luz del proyector lava los colores oscuros, por eso la app es **clara** y de alto
contraste (Impeccable, `new-work.md` §4: "Dark or light is never a default: write one sentence of
physical scene").

Modo: **Operate** (Impeccable, "Modes"; `mode-operate.md`): la persona viene a hacer
una tarea. El "mundo" del Paisaje Cultural Cafetero solo presta cuatro cosas —tipografía, paleta,
densidad y un movimiento propio—; la navegación y los controles son los estándar de la web.

Cada vista responde una pregunta, y la cifra más grande de la vista es la que la responde
(Taste, `references/app-screens.md` §2.2 y §5 "The answer figure leads"):

| Vista | Pregunta | Cifra principal |
|---|---|---|
| Ruta | ¿Cuánto tardo de A a B? | tiempo de viaje en minutos |
| Envolvente | ¿Qué área cubre la red? | área en km² |
| Itinerario | ¿Cabe el día en 11 h y cuánto gana el óptimo? | jornada de cada algoritmo + "Cabe / No cabe" |
| Resultados | ¿Coincide lo medido con la teoría? | una frase de lectura bajo cada gráfica |

## 2. Paleta

Tomada del paisaje (Taste, "Check the palette against the subject": si el tema
tiene colores propios, se toman de él). Estrategia **Restrained** de Impeccable (`new-work.md` §4):
neutros teñidos de verde montaña y dos tonos que trabajan sobre los datos. Nada de degradados,
nada de violeta/índigo ni de crema con terracota (Taste, House rules "No default palette").

| Token | Hex | Papel | Contraste sobre blanco |
|---|---|---|---|
| `suelo` | `#f2f4ee` | fondo: la neblina de la cordillera | — |
| `superficie` | `#ffffff` | paneles | — |
| `hundido` | `#e8ebe2` | un paso de tono: filas elegidas, pozos | — |
| `activo` | `#dde3d5` | opción resaltada en listas | — |
| `borde` / `regla` | `#d3d9cb` / `#e5e9df` | borde de paneles / reglas de tabla | — |
| `control` | `#7d8676` | borde de campos | 3,8:1 (≥ 3:1 para controles) |
| `tinta` | `#16201a` | texto principal | 16,7:1 |
| `tinta-2` | `#46524a` | texto secundario | 8,2:1 |
| `tinta-3` | `#5a655c` | notas, ejes, etiquetas | 6,1:1 (4,6:1 sobre `activo`) |
| `primario` | `#1c3a29` | verde cordillera: el único botón lleno de cada vista | texto blanco 12,5:1 |
| `cereza` | `#a63220` | cereza de café: **el algoritmo propio / el óptimo** | 6,8:1 |
| `azul` | `#2b5c7a` | cielo de montaña: **el comparador / la voraz** | 7,2:1 |
| `guadua` / `tostado` | `#3c7334` / `#7a4b1e` | categorías finca / acopio en el mapa | — |
| `positivo` / `negativo` | `#1f6b3b` / `#96201a` (+ sus pálidos) | "Cabe en 11 h" / "No cabe" | 6,5:1 / 8,3:1; sobre su pálido 5,4:1 / 6,8:1 |

Contrastes calculados con la fórmula de luminancia relativa de WCAG 2.x (todos los textos ≥ 4,5:1;
ui-ux-pro-max, `quick-reference.md` §1 `color-contrast`; Impeccable `craft-floor.md` → Verify).

**Una regla de color en toda la app** (Taste, `app-screens.md` §6.4 "One subject keeps one hue
across the screen"; Impeccable `colorize.md` "Build roles, not a bag of swatches"):
cereza = lo propio u óptimo (la ruta de Dijkstra, QuickHull, Held-Karp, la versión con cola de
prioridad); azul = aquello con lo que se compara (versión lineal, SciPy, vecino más cercano).
El color nunca va solo: la voraz además es **discontinua**, cada leyenda dice el nombre, las
categorías del mapa tienen texto, y "No cabe" lleva palabras y no solo rojo
(ui-ux-pro-max `color-not-only`; Impeccable `colorize.md` "Information conveyed by color also needs
text, shape...").

El mapa base de OpenStreetMap se muestra desaturado (`filter: saturate(.3)`) para que el color quede
para los datos (Taste, `app-screens.md` "Colour goes on data, not chrome").

## 3. Tipografía

- **Una sola familia: Archivo** (Omnibus-Type, fundición latinoamericana), variable en peso y ancho,
  instalada con `@fontsource-variable/archivo` para funcionar sin internet. Es una grotesca con
  carácter y cifras tabulares reales, lejos de los tipos "de kit" que Impeccable lista como
  desgastados (Inter, DM Sans, Space Grotesk, IBM Plex…; `new-work.md` §4) y de "Geist o Inter sobre
  #f8f8f8" que Taste marca como cara de plantilla (`app-screens.md` §14).
- El ancho variable da la jerarquía sin segunda familia: títulos a `font-stretch: 88%`
  (semicondensados, `text-wrap: balance`), cifras a 92 %, texto a 100 %
  (Taste, `app-screens.md` §9.1 "One grotesk").
- Escala: 12 / 13 / 15 (texto) / 18 / 24 (h1 de la vista) / 30–34 (cifra principal). El h1 se queda
  en 24 px: es una herramienta, no una portada (§9.1 "App type is not display type").
- Todas las cifras con `font-variant-numeric: tabular-nums`, alineadas a la derecha en tablas y con
  formato `es-CO` mediante `Intl.NumberFormat` (1.631,5) (Taste §7.4; web-design-guidelines
  "Numbers", "Hardcoded number formats instead of Intl.*").

## 4. Espaciado, superficies y forma

- Base de 4 px; 16 px de margen en el teléfono y 24 px en escritorio
  (ui-ux-pro-max `spacing-scale`; Impeccable `layout.md` "A 4-unit base").
- Superficies planas separadas por un borde de 1 px o un paso de tono; **sin sombras** salvo en lo
  que flota (la lista desplegable del selector) (Taste §9.4 "A border or a shadow, never both").
- Radio corto y único: 6 px en paneles y controles; píldoras redondas solo para el estado
  "Cabe / No cabe" (§9.4 "Radius is bimodal").
- Las cifras se agrupan en **una franja dividida** por líneas de 1 px, no en tarjetas con iconos
  (Taste §5 "KPIs are type, not tiles"; Impeccable `craft-floor.md` → Refuse "hero-metric
  template", "same-size cards of icon plus heading").
- Sin eyebrows, sin numeración decorativa 01/02/03, sin emoji (Impeccable `craft-floor.md`
  "A kicker or eyebrow above a heading. This one is a ban"; Taste House rules).

## 5. Estructura y componentes

- **Armazón**: barra superior blanca de 56 px con la marca (un grano de café cuya ranura es una
  carretera de montaña), el nombre del producto y el alcance ("Red vial del Quindío ·
  OpenStreetMap"), y cuatro pestañas subrayadas. Sin barra lateral: son solo cuatro destinos
  (Taste §3.1 "No sidebar … for products with few destinations"; §3.2 "The product is
  named"). La vista activa vive en la dirección (`#ruta`, `#itinerario`…) para poder enlazarla
  (web-design-guidelines "URL & Deep Linking"; ui-ux-pro-max `deep-linking`).
- **Vistas de mapa** (`ConMapa`): panel de trabajo de 400 px a la izquierda y el mapa en el resto;
  en el teléfono el panel va arriba y el mapa debajo (Impeccable `layout.md` "Make responsive
  behavior structural").
- **Selector de lugar con búsqueda** (`SelectorLugar`): patrón combobox de WAI-ARIA; busca sin
  tildes por nombre, municipio o código; flechas, Enter y Escape; etiqueta visible arriba del campo
  (Taste §8.1 "Label above the field"; ui-ux-pro-max `input-labels`, `keyboard-nav`).
- **Movimiento propio de la app** (Impeccable `mode-operate.md` "Name the signature move
  concretely"; Taste §2 "one element only this product has"): la **barra de la jornada**.
  Los dos recorridos sobre un mismo eje de horas, visitas como bloques con el código del lugar,
  desplazamientos como líneas, y la franja fuera de las 11 h teñida. Responde de un vistazo "¿cabe
  el día?" y "¿dónde pierde tiempo la voraz?".
- **Mapa del itinerario**: Held-Karp gruesa y continua debajo, la voraz delgada y discontinua
  encima, para que se vean las dos donde coinciden; números de parada de Held-Karp sobre el mapa;
  casillas para ocultar cada capa.
- **Resultados**: por requerimiento, las gráficas interactivas (Recharts, leyendo los mismos CSV)
  junto a las figuras PNG del documento técnico, en una rejilla de dos columnas donde el último
  elemento impar ocupa el ancho completo para no dejar huecos (Taste §4.2 "Dead space from a
  grid that does not fit the data"). Cada gráfica: una sola rejilla horizontal tenue, sin línea de
  eje Y, escala logarítmica con marcas en potencias de 10 cuando los tiempos cruzan órdenes de
  magnitud, leyenda en la cabecera dibujada con la misma marca (línea continua/discontinua, punto)
  y una frase de lectura (§6.3, §6.4 "Every swatch is the mark it explains"; ui-ux-pro-max
  `charts.csv` "Trend Over Time → Line", "Compare Categories → Bar", "Correlation → Scatter").
  Las tablas son plegables, con encabezado fijo y números a la derecha (§7).
- **Estados**: cada bloque tiene su estado de carga ("Calculando…"), de error dentro del bloque con
  `role="alert"`, el botón deshabilitado dice por qué (validación 6–8 visible y anunciada con
  `aria-live`), y un aviso cuando el resultado mostrado ya no corresponde a la selección
  (Taste §11; Impeccable `craft-floor.md` "States"; ui-ux-pro-max `error-placement`).

## 6. Accesibilidad y superficies del navegador

- Foco visible de 2 px en verde cordillera con `:focus-visible`; enlace "Saltar al contenido".
- Todo funciona con teclado: pestañas como enlaces, selector combobox, casillas nativas.
- Selección de texto, cursor de escritura, `accent-color` de casillas y barras de desplazamiento
  teñidos con la paleta (Impeccable `craft-floor.md` → "Browser surfaces").
- `prefers-reduced-motion` respetado; las únicas transiciones son de color en hover.
- Sin desplazamiento horizontal a 375 px: las tablas anchas se desplazan dentro de su propio marco
  (Taste §12 "A table that must stay a table scrolls inside its own frame").
- Imágenes con `width`/`height` reales (la API los lee del PNG) y `loading="lazy"`
  (web-design-guidelines "Images").

## 7. Reglas de React aplicadas

De `react-best-practices` (las que aplican a una SPA con Vite):
- `bundle-dynamic-imports` / `bundle-conditional`: la vista de Resultados (Recharts) se carga con
  `React.lazy` solo cuando se abre.
- `async-parallel` / sin cascadas: los lugares se piden una vez en `App` y se pasan a las vistas.
- `rerender-derived-state-no-effect`: la validación del itinerario se calcula al renderizar, no se
  guarda en otro estado.
- `rerender-functional-setstate`: marcar/desmarcar atractivos con `setElegidos(actuales => …)`.
- `js-index-maps`: `Map` de id → lugar en el itinerario; caché de `Intl.NumberFormat`.
- `rerender-no-inline-components`: ningún componente se define dentro de otro.
- `rendering-conditional-render`: condicionales con ternario.
- `useMemo` solo donde importa: la lista de puntos para encuadrar el mapa no cambia al filtrar capas.

De `composition-patterns`:
- `patterns-children-over-render-props`: `Cifras` + `Cifra`, `Mapa` con capas como hijos,
  `ConMapa` con el panel y el mapa como piezas.
- `architecture-avoid-boolean-props` / `patterns-explicit-variants`: `Aviso tipo="error" | "nota"`
  y `trazo="continuo" | "discontinuo"` en vez de banderas booleanas.

## 8. Revisión

Revisión hecha con la app compilada (`npm run build`) y servida por `api/main.py`, recorriendo las
cuatro vistas a 1280 × 800, 1440 × 900 y 375 × 812 (teléfono), con ratón y con teclado. Se auditó
contra Impeccable (`audit.md`, `critique.md`, `polish.md`, `craft-floor.md`), Taste (reglas de
pantallas de trabajo), las Web Interface Guidelines de Vercel y la referencia rápida de ui-ux-pro-max.
Se conservó el sistema visual (paleta, tipografía, superficies); solo se corrigieron defectos.

### Hallazgos corregidos

| # | Prioridad | Vista | Hallazgo | Corrección | Guía |
|---|---|---|---|---|---|
| 1 | P1 | Todas | Al cambiar de pestaña la vista nueva se abría en la posición de desplazamiento de la anterior (en el teléfono, a mitad de la lista de atractivos o del mapa). | `App.tsx` vuelve arriba (`scrollTo(0, 0)`) en cada cambio de vista. | polish §4 "arrival paths connect" |
| 2 | P1 | Ruta | Con origen = destino se calculaba una "ruta" de 0 min y un solo punto: el mapa quedaba vacío sin explicación. | El botón se deshabilita y una frase con `aria-live` dice por qué ("elige otro destino"). | craft-floor "States"; Vercel "error messages state the fix" |
| 3 | P1 | Ruta | Al cambiar origen o destino la ruta anterior seguía en pantalla como si fuera la nueva (el itinerario ya avisaba; la ruta no). | Aviso "la ruta de abajo es la anterior", igual al del itinerario. | polish "misleading state" |
| 4 | P1 | Ruta, Itinerario | El buscador de lugares exigía el texto seguido: "bolivar arm" no encontraba "Plaza de Bolívar de Armenia" (falta el "de"). | Cada palabra escrita debe aparecer, en cualquier orden. | ui-ux-pro-max `error-feedback`; Vercel "plan for real input" |
| 5 | P2 | Ruta, Itinerario | Con el campo ya enfocado (justo después de elegir), un clic ponía el cursor en medio del nombre y lo escrito se mezclaba ("Plaza de Bolívar de Armfilandiaenia"). | El clic también selecciona el nombre si no se está escribiendo. | polish "every control … default, focus" |
| 6 | P2 | Ruta, Itinerario | Con el teclado, la opción activa del selector se salía de la lista visible, y la primera flecha abajo se saltaba la primera opción. | La opción activa se desplaza a la vista (`scrollIntoView({block: 'nearest'})`); la primera flecha solo abre la lista. | ui-ux-pro-max `keyboard-nav` |
| 7 | P2 | Ruta | Origen y destino del mapa solo se distinguían por color (negro / cereza) y por un globo que aparece al pasar el ratón, que no existe en el teléfono ni se ve en el proyector. | Etiquetas fijas "Origen: …" y "Destino: …" sobre los marcadores (`direction="auto"`, no se salen del mapa). Globos de Leaflet con la letra, la tinta y el borde de la app. | ui-ux-pro-max `color-not-only`, `hover-vs-tap` |
| 8 | P2 | Itinerario | El botón "Armar itinerario" quedaba debajo de 17 atractivos: había que bajar hasta el final del panel para usarlo (y en el teléfono, más de una pantalla). | Barra del botón pegada al borde inferior del panel (`sticky bottom-0`), con `scroll-padding` para que no tape el campo enfocado. | ui-ux-pro-max `primary-action`; WCAG 2.2 `focus-not-obscured` |
| 9 | P2 | Itinerario | El mapa está a mitad de una página que se desplaza: la rueda del ratón lo acercaba en vez de bajar, y en el teléfono el dedo quedaba atrapado moviendo el mapa. | `Mapa dentroDePagina`: sin zoom con rueda, y en pantallas táctiles el dedo mueve la página (se acerca con dos dedos). Ruta y Envolvente, donde el mapa ocupa su propio espacio, siguen igual. | Vercel "gestures"; ui-ux-pro-max `gesture-conflicts`, `scroll-behavior` |
| 10 | P2 | Itinerario | En el teléfono los rótulos del resumen se pegaban ("DesplazamientosVisitas") porque la rejilla de 3 columnas iguales no cabía. | Fila flexible con separación de 24 px que pasa a dos líneas si no cabe. | craft-floor "Run the real copy at every breakpoint" |
| 11 | P2 | Itinerario | En el teléfono los códigos de lugar se amontonaban sobre los bloques de la barra de la jornada ("CLCMOQFUN"). | El código solo se muestra desde `sm` (en el teléfono la barra es demasiado angosta); el nombre sigue en la descripción accesible del carril. | craft-floor "fix what overflows" |
| 12 | P2 | Resultados | Ejes x con marcas sin sentido: "5.305 · 11.305 · 17.305" en V + E, "5,0 · 7,0 · 9,0" para k (un entero) y "14 · 15 · 15" repetido en Held-Karp extendido. | Dominio `auto` sin decimales (marcas redondas: 0 · 7.500 · 15.000…; 4 · 6 · 8…; 13 · 14 · 15 · 16) y formato de enteros sin ",0". | Vercel "Typography" (tabular-nums, Intl.NumberFormat); Taste, pantallas de trabajo (gráficas) |
| 13 | P3 | Resultados | La gráfica "Brecha de la voraz con el óptimo" era la única sin frase de lectura. | Frase calculada del CSV: "entre 3,1 % y 10,7 % por encima del óptimo; la peor instancia, 16,9 %". | Taste: cada gráfica enuncia un hallazgo |
| 14 | P3 | Resultados | "2^k" escrito con acento circunflejo en la leyenda y en la lectura. | "2ᵏ" (superíndice real). | Vercel "Typography" |
| 15 | P3 | Itinerario | "10 h 0 min" en la suma de visitas; minutos con punto decimal ("34.9 min") en las ayudas de la barra. | "10 h"; minutos con `Intl.NumberFormat('es-CO')` ("34,9 min"). | Vercel "hardcoded number formats" |
| 16 | P3 | Ruta, Itinerario | El botón principal deshabilitado se veía distinto en cada vista (opacidad 60 % en Ruta, gris en Itinerario) y no tenía estado presionado. | Clases únicas `.boton-primario` / `.boton-secundario` en `index.css`: mismo deshabilitado y estado `active` en las dos vistas. | ui-ux-pro-max `state-clarity`, `press-feedback` |
| 17 | P3 | Todas (teléfono) | La barra superior fija ocupaba 105 px de 812 en el teléfono. | Fila de la marca de 48 px y sin la línea del alcance bajo `sm` (97 px). | ui-ux-pro-max `content-priority` |

### Revisado y sin cambios

- Contraste: todos los pares texto/fondo de la paleta siguen ≥ 4,5:1 (tabla de la §2).
- Foco visible en enlaces, campos, casillas y botones; "Saltar al contenido" funciona.
- Sin desplazamiento horizontal a 375 px en ninguna vista; las tablas anchas se desplazan dentro de su marco.
- Consola del navegador sin errores en las cuatro vistas.
- Rendimiento del mapa: menos de 100 marcadores por vista y polilíneas de unos cientos de puntos;
  el renderizador SVG de Leaflet basta, no hace falta Canvas ni agrupar marcadores.

### Pendiente fuera de `web/`

- Las figuras PNG del documento (`resultados/figuras/*.png`, de los scripts de experimentos) usan
  los colores por defecto de Matplotlib (azul y naranja), al revés de la regla de color de la app
  (cereza = propio, azul = comparador). Cambiarlo corresponde a quien genera esas figuras.
