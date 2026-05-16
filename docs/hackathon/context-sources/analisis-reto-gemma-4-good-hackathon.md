# Análisis del reto Gemma 4 Good Hackathon

Source PDF: `C:\Users\joaco\Downloads\Análisis del reto Gemma 4 Good Hackathon.pdf`

---

Análisis del reto Gemma 4 Good Hackathon
El Gemma 4 Good Hackathon es una competencia enfocada en soluciones de IA de impacto real,
especialmente en ambientes con baja conectividad, privacidad y accesibilidad limitadas 1 . En
concreto, el track “Global Resilience” apunta a sistemas que ayuden en crisis y desastres (e.g.
herramientas de emergencia offline, adaptación climática, AI en entornos remotos) 2 . El hackathon
enfatiza que la solución use Gemma 4 localmente (edge AI), multi-modalidades (texto, imágenes, voz),
y sea offline primero con explicaciones transparentes. Además, los criterios de evaluación clave son
impacto/visión, narrativa convincente (video/storytelling) y profundidad técnica 3 4 . En
resumen, se premian prototipos con un problema real, una solución creíble y demostrada, y un uso
significativo de Gemma 4 en un dispositivo local 5 6 .



Análisis de ganadores de hackathons similares
Proyectos ganadores previos en hackathons relacionados ofrecen ejemplos útiles:


     • En el Gemma 3n Impact Challenge (2025), muchos equipos usaron Gemma local con
       dispositivos físicos. Por ejemplo, “Sixth Sense for Security Guards” combinó un detector de
       movimiento YOLO con Gemma 3n para interpretar video de vigilancia en tiempo real 7 . De
       modo similar, “Gemma Vision” montó una cámara en el pecho de una persona con discapacidad
       visual y usó Gemma 3n on-device (vía MediaPipe) para describir imágenes y actuar por
       comandos de voz 8 . El proyecto “LENTERA” demostró un hotspot WiFi local que ejecutaba
       Gemma 3n offline, permitiendo a usuarios conectarse a un micro-servidor educativo sin internet
         9 . Estos ejemplos muestran la efectividad de la inferencia local multimodal (imagen + texto +

       voz) y la importancia de la operación offline.


     • En hackathons de desastres globales (e.g. AWS Disaster Response, hackathons de ciudades
       inteligentes), los ganadores suelen integrar múltiples fuentes de datos y análisis predictivo.
       Por ejemplo, un equipo de hackathon combinó sensores de nivel de agua y drones para predecir
       inundaciones y enviar alertas locales 10 . Otro equipo ganó un premio por una solución
       predictiva que rastreaba especies invasoras antes de que se establecieran, destacando que los
       sistemas proactivos de alerta (no solo recolección de reportes) son más efectivos 11 .


Estos casos muestran que las soluciones más fuertes son las que funcionan end-to-end, abordan un
flujo de trabajo concreto y un usuario claro (e.g. “oficial de Defensa Civil”), usan Gemma de forma
central (no solo como chat genérico), y tienen resultados demostrables evidenciables 4 6 .



Comparación del prototipo con el reto y
ejemplos previos
El prototipo “Acuífero 4 + Vigía” apunta claramente al track Resiliencia Global: es un sistema de alerta
temprana de inundaciones offline, fusionando señales locales (video de cámara fija + reportes de
ciudadanos) con Gemma 4 corriendo en el borde. Esto cumple el énfasis offline y multi-modal del
hackathon 1 2 . El proyecto incluye características destacadas: razonamiento local con Gemma en




                                                    1
español, evidencia auditable de decisiones, estructura de alerta integrable con protocolos argentinos
(SINAGIR). Además, contempla salidas físicas (sirena, radio, LoRa) en caso de alerta alta.


En términos de alineación con ganadores previos: el uso de un nodo de cámara fija + OpenCV es
análogo a proyectos como “Sixth Sense” 7 , que usó visión por computadora combinada con Gemma.
El envoltorio con reporte ciudadano offline es un componente adicional novedoso; los ejemplos previos
no integraron esa fuente de información humana de forma estructurada. También coincide con la
necesidad de éxito técnico del hackathon: se ha implementado todo el pipeline (backend, frontend, app
Android, gemma on-device, cache offline, etc.), lo cual demuestra ejecución real.


Diferencias/Limitaciones: Aunque el prototipo parece innovador en la integración, hay que destacar
que otros hackganadores ya han mostrado usos similares de Gemma en dispositivos edge 8 9 . Por
ejemplo, “LENTERA” validó el despliegue offline con hotspot local 9 , un aspecto que nuestro sistema
también plantea. Sin embargo, el proyecto aún podría fortalecerse en la demostración efectiva del
despliegue real en hardware limitado (ej. Raspberry Pi), ya que el hackathon valora explícitamente
esa parte 12 . También conviene asegurarse de que el uso de Gemma sea plenamente significativo: en
otros proyectos ganadores Gemma servía para tareas claves (p.ej. generación de instrucciones en “Vite
Vere Offline”), por lo que debemos resaltar en qué consiste exactamente el razonamiento de Gemma en
nuestra propuesta y cómo se usa su salida (más allá de un chatbot genérico) 6 .



Tareas pendientes (priorizadas)
Para maximizar las chances de ganar, sugerimos enfocarse en lo siguiente:


     • Implementar despliegue en hardware real (edge AI). El hackathon premia la demostración de
       inferencia local en dispositivos limitados 12 . Se recomienda probar el nodo fijo y la app Android
       en un Raspberry Pi o similar (con GPU mínimo o CPU) y medir latencias. Esto incluye mostrar
       cómo Gemma 4 corre localmente (usando Ollama/MediaPipe) con los recursos del dispositivo.


     • Destacar las capacidades multimodales y funciones de Gemma. Aprovechar más
       funcionalidades de Gemma on-device (p.ej. function calling o localización de conocimiento). Por
       ejemplo, al procesar un reporte ciudadano, usar Gemma para extraer entidades/hallazgos clave,
       no solo clasificación básica. Se podría incorporar una base de datos local (climatología, umbrales
       de ríos) y que Gemma la consulte, reforzando la explicación de la alerta. Esto muestra “uso
       significativo de Gemma” y alinea con ideas de tracks como Safety & Trust (flujos de inferencia
       confiables) 13 .


     • Integrar componente predictivo/proactivo. Considerar sumar un modelo de previsión (p.ej.
       basado en lluvias recientes o históricos) que anticipe el riesgo. Como sugieren ejemplos
       ganadores, las soluciones proactivas destacan (predecir la marea de crecida al estilo HackAnalog
        10 o invasiones biológicas 11 ). Incluso un modelo simple local (ej. regresión sobre niveles

       recientes) podría reforzar la utilidad y novedad del sistema.


     • Mejorar la narrativa y demostración (video/UX). Preparar un video de demo claro y breve (30–
       60s) que muestre el problema real y el beneficio. Presentar a un usuario concreto (p.ej. “el
       operador municipal” u “oficial de Defensa Civil”) usando la app: cómo recibe un reporte, vemos el
       vídeo curado, el Gemma genera el análisis y aparece la alerta (sirena/LED) con la justificación.
       Las reglas indican valorar una historia fácil de entender en segundos 6 . Pulir la interfaz
       (dashboard PWA y app móvil) para que sea intuitiva y bilingüe (usar español).




                                                   2
         • Calibrar y explicar decisiones (confianza y trazabilidad). Ante falsos positivos/narraciones
           extrañas de Gemma, añadir explicaciones o niveles de confianza. Por ejemplo, incluir en la alerta
           el “frame de evidencia” seleccionado y el texto de razón generada por Gemma (ya se hace),
           mostrando al operador por qué se activó la alarma 9 13 . Esto apoya la trazabilidad y la
           confianza (track Safety & Trust). Se puede añadir un breve resumen de la puntuación del riesgo
           por cada fuente (cámara vs reporte ciudadano).


         • Completar requerimientos formales de la competencia. Asegurarse de tener un repositorio
           público bien documentado, un write-up claro en Kaggle (o blog), un video pitch, capturas/
           pantallas (“media gallery”), etc., tal como exigen las bases 14 . Incluir un “cover image” atractivo.
           Documentar claramente la parte de Gemma (qué prompt/fine-tuning se usó, cómo se integra la
           reasoning de Gemma). El equipo de Meta-data lo valora: no es solo un notebook, sino un
           prototipo de producto con documentación.


         • Fortalecer la integración ciudadana y local. Mejorar la experiencia de reporte voluntario: por
           ejemplo, incorporar reconocimiento de voz offline (Android Speech-To-Text) para audios, o
           permitir cargar fotos con anotaciones. Se puede implementar comunicación LoRa o hotspot local
           para conectar sensores o dispositivos de vecinos, al estilo “LENTERA” 9 . Esto subraya la
           independencia de internet y la soberanía de datos.


En resumen, el enfoque debe ser demostrar ingeniería real + valor tangible: mostrar que el sistema
funciona end-to-end en condiciones difíciles (sin conectividad) y resuelve un flujo específico de
emergencia. Cada tarea anterior apunta a hacer más claro y robusto el prototipo, aumentando su
impacto en el concurso.


Referencias: descripción del hackathon y ejemplos de proyectos ganadores                  1   2   6   7      9   11 .




 1   2     3   4   5   6   12   13   14   The Gemma 4 Good Hackathon. by — Kaggle Team | by Sudha Rani
Maddala | Apr, 2026 | Medium
https://sudhamsr.medium.com/the-gemma-4-good-hackathon-aef927f17ef1

 7   8     9   These developers are changing lives with Gemma 3n
https://blog.google/innovation-and-ai/technology/developers-tools/developers-changing-lives-with-gemma-3n/

10   Early warning system wins Analog Devices flooding hackathon - TechCentral.ie
https://www.techcentral.ie/early-warning-system-wins-analog-devices-flooding-hackathon/

11 Items - Crab Alert: Hackathon team builds award-winning early warning system for invasive species -
School of Electronic Engineering and Computer Science
https://www.qmul.ac.uk/eecs/news-and-events/news/items/crab-alert-hackathon-team-builds-award-winning-early-warning-
system-for-invasive-species.html




                                                           3

