# Acuífero: Trabajo Pendiente Priorizado v2

Source PDF: `C:\Users\joaco\Downloads\Acuifero_Trabajo_Pendiente_Priorizado_v2.md.pdf`

---

Trabajo Pendiente Priorizado para Maximizar Chances de Ganar
(v2)
Proyecto: Acuífero 4 + Vigía Hackathon: Gemma 4 Good Hackathon (Kaggle × Google
DeepMind) Deadline: 18-may-2026, 23:59 UTC — quedan ~4 días Pesos confirmados por la
rúbrica oficial:
     40% Impacto y Visión
     30% Video y Narrativa (YouTube público, máx. 3 min)
     30% Ejecución Técnica (writeup máx. 1500 palabras + repo)

Premios objetivo:
     Pista Global Resilience: USD 10.000
     Premio especial LiteRT / Google AI Edge: USD 10.000
     (Premio Ollama queda como fallback; el premio LiteRT es más alineado y menos disputado)




🔴 Prioridad Máxima (próximas 48 h)
P1. Migrar la inferencia del nodo Acuífero a LiteRT-LM en Raspberry Pi
Qué hacer: Reemplazar la dependencia de Ollama por LiteRT-LM v0.10.1+ usando la CLI o la API
Python/C++:

 litert-lm run \
   --from-huggingface-repo=litert-community/gemma-4-E2B-it-litert-lm \
   gemma-4-E2B-it.litertlm \
   --backend=gpu \
   --enable-speculative-decoding=true


Mantener Ollama solamente como modo de desarrollo documentado, no como motor de
producción. La inferencia "que cuenta" para el jurado tiene que ocurrir vía LiteRT-LM.
Por qué: Los tres análisis convergen en que sin LiteRT-LM real el premio AI Edge es
prácticamente inalcanzable. El precedente Gemma Vision (1º + premio AI Edge en Gemma 3n)
corrió sobre MediaPipe LLM Inference, que usa LiteRT bajo el capó. Ollama es excelente para
prototipar pero está fuera del mandato del premio.
Impacto: ALTO. Esfuerzo: MEDIO. Tipo: Modificar existente.



P2. Reemplazar el export "tipo SINAGIR" por output CAP v1.2 estándar (XML + JSON)
Qué hacer: Reestructurar el objeto FusedAlert para emitir Common Alerting Protocol v1.2
(ITU-T X.1303), poblando los campos obligatorios:
         identifier , sender , sent , status ("Actual"/"Test"), msgType , scope
         info.category ("Met"), info.event , info.urgency ("Immediate"/"Expected"),
         info.severity ("Extreme"/"Severe"/"Moderate"), info.certainty
     ("Observed"/"Likely")
      info.area.polygon o circle con las coordenadas del sitio
      info.description y info.instruction en español rioplatense (acá entra Gemma 4)

Mantener el wrapper SINAGIR como capa por encima, no como output principal. Mencionar
explícitamente que el payload está listo para inyección en AlertAR (sistema nacional argentino
de Cell Broadcasting aprobado en 2024).
Por qué: CAP es el estándar de la OMM, UNDRR, IFRC y la mayoría de servicios meteorológicos.
Convierte "JSON propietario para un sistema argentino" en "ciudadanía global de
interoperabilidad". Es el cambio de framing que más eleva el 40% de "Impacto y Visión" con
menos esfuerzo.
Impacto: ALTO. Esfuerzo: BAJO-MEDIO (el motor de decisión ya existe; es básicamente
renombrar y completar campos). Tipo: Modificar existente.



P3. Filmar y editar el video de 3 minutos con guion de 4 actos
Qué hacer: Estructura recomendada por los análisis y validada por proyectos ganadores
(Sentinel, Flood Ready, Gemma Vision):

 Tiempo       Acto           Contenido

 0:00–        El dolor       Operador de Defensa Civil rural argentino. Pantalla saturada de WhatsApp
 0:45                        inconexo durante alerta naranja del SMN. Internet se cae en vivo.

 0:45–        La             Nodo Acuífero en un puente argentino real. OpenCV cura frames, Gemma 4
 1:45         intervención   vía LiteRT-LM razona en Pi. Latencia en pantalla.

 1:45–        La capa        Vigía: vecino en modo avión envía audio coloquial ("el agua ya pasó la
 2:30         humana         marca"). Gemma on-device parsea y encola. Reconexión y sync.

 2:30–        Cierre         Tablero fusiona señales, emite CAP v1.2, dispara sirena/LoRa, payload listo
 3:00         auditable      para AlertAR. Métricas en overlay.



Por qué: El video pesa 30% solo, pero junto al writeup decide el otro 30% de la percepción
humana del jurado. Ningún ganador previo ganó sin un video con narrativa humana. Evitar
screencasts largos de código.
Impacto: ALTO. Esfuerzo: MEDIO-ALTO. Tipo: Agregar nuevo.
P4. Filmar UN clip de un arroyo o canal argentino real
Qué hacer: Reemplazar el clip USGS Silverado como demo principal por un clip argentino
(Luján, Reconquista, Matanza, La Plata, Resistencia, Concordia, arroyo del Gato, etc.). Si no es
viable, simulación física controlada (bandeja + marca + objetos arrastrados) con contexto
argentino visible. Mantener USGS Silverado solo como "validación adicional".
Por qué: Sin esto, el claim "español rioplatense + Defensa Civil argentina + Global Resilience" se
debilita ante el primer juez que pregunte por qué el demo es de California.
Impacto: ALTO. Esfuerzo: BAJO-MEDIO. Tipo: Modificar existente.



🟠 Prioridad Alta (48–72 h)
P5. Benchmark card cuantitativa con métricas comparables
Qué hacer: Notebook Kaggle público con tabla de métricas duras:

 Métrica                       Target referencia                     Hardware

 Time-to-First-Token (TTFT)    <2s                                   Pi 5 16GB CPU

 Decode rate                   5–8 tok/s baseline; >12 con MTP       Pi 5 GPU

 Decode rate móvil             >3000 tok/s prefill NPU               Pixel/Samsung gama alta

 Peak RAM                      < 4 GB (E2B) / < 6 GB (E4B)           Pi 5

 Latencia E2E análisis nodo    < 30 s por ventana de 60 s de video   Pi 5

 Accuracy nivel agua           R², MAE px o cm                       N clips

 F1 parsing reportes ES-AR     > 0.80                                corpus rioplatense ≥ 50 frases

 Tiempo offline soportado      ≥ 8 h con ≥ 50 reportes               Android



Los números 5–8 tok/s en Pi y >3000 tok/s NPU móvil son los benchmarks publicados por Google
AI Edge para Gemma 4; superarlos o documentarlos honestamente vale puntos en el 30%
técnico.
Por qué: Los premios técnicos (LiteRT, antes AI Edge, antes Jetson) se ganan con números, no
con "funciona". Sin métricas el writeup se lee como demo, no como ingeniería.
Impacto: ALTO. Esfuerzo: MEDIO. Tipo: Agregar nuevo.
P6. Reescribir el Kaggle Writeup respetando el límite duro de 1500 palabras
Qué hacer: Estructura sugerida (calibrada a 1500 palabras exactas):
  1. El problema humano (~200 pal) — brecha de última milla, fallo de red durante crecida.
  2. La arquitectura (~350 pal) — diagrama + flujo: cámara → OpenCV → Gemma 4 LiteRT →
     fusión → CAP v1.2 → actuador.
  3. Por qué Gemma 4 + LiteRT (~250 pal) — citar E2B/E4B, MediaPipe en Android, MTP,
     function calling, multimodal.
  4. Anti-alucinación: OpenCV como firewall determinístico (~200 pal) — alineado con
     Gemma Vision; Gemma no inventa niveles, los recibe.
  5. Resultados y métricas (~200 pal) — tabla del P5.
  6. Compliance e impacto institucional (~200 pal) — CAP v1.2, AlertAR, Disposición 2/2023,
     AAIP Guía de Transparencia 09/2024.
  7. Diferenciación y novedad (~100 pal) — frente a Flood Hub, PetaBencana, FloodNet,
     FarmWise AI.

Por qué: Pasarse del límite penaliza. Quedarse muy corto regala el 30% de ejecución técnica. Esta
estructura cubre los tres pilares de la rúbrica explícitamente.
Impacto: ALTO. Esfuerzo: MEDIO. Tipo: Modificar/Agregar.



P7. Sección explícita "OpenCV como firewall anti-alucinaciones" (Gemma Vision pattern)
Qué hacer: En el writeup y en el video, verbalizar literalmente: "Gemma no mira la imagen para
inventar el nivel del agua; recibe vectores numéricos curados por OpenCV (línea de agua
detectada, delta temporal, evidencia frame) y razona estrictamente como motor de lógica
deductiva. La misma estrategia que el ganador del premio Google AI Edge en Gemma 3n
(Gemma Vision, ML Kit OCR + Gemma)."
Por qué: Es el argumento más fuerte de seguridad ante un juez que conoce la propensión de los
LLM a alucinar en tareas críticas. Y empareja explícitamente con el patrón ya premiado por
Google. Es publicidad gratis con el jurado adecuado.
Impacto: ALTO. Esfuerzo: BAJO. Tipo: Agregar nuevo (redacción).



P8. Activar multimodalidad nativa de Gemma 4 + native function calling
Qué hacer:
     Multimodal: que Gemma 4 reciba directamente el evidence frame curado además del
     resumen textual. Ablation OpenCV-only vs Gemma-multimodal vs hybrid; reportar cuál es
     mejor y por qué (probablemente hybrid).
     Function calling: definir tools trigger_siren(level) ,
     notify_civil_defense(cap_payload) , send_lora_alert(coords, level) ,
     emit_cap_xml(event) . Gemma 4 las invoca; el motor determinístico actúa como guardrail.

Por qué: El tweet de lanzamiento de Kaggle marca literalmente "multimodal power and native
function calling" como los dos features distintivos de Gemma 4. No usarlos en el track más
alineado es regalar puntos. Y function calling es naturalmente la forma elegante de conectar
Gemma con CAP/AlertAR/sirena.
Impacto: ALTO. Esfuerzo: MEDIO. Tipo: Modificar existente.



P9. Diferenciación explícita vs FarmWise AI y demás competidores en Global Resilience
Qué hacer: Agregar un párrafo corto en el writeup que diga, sin rodeos, dónde estamos cada uno:
     FarmWise AI: Gemma 4 E2B offline para agricultores; un sensor humano, sin nodo físico,
     sin fusión, sin alerta crítica en tiempo real.
     Flood Ready PWA: malla QR P2P; sin LLM razonando sobre video, sin parsing de voz
     coloquial, sin nodo edge.
     Google Flood Hub: forecasting macro de cuenca; cloud-only, sin granularidad de puente,
     sin operación durante apagón.
     PetaBencana / Ushahidi: crowdsourcing online vía chatbot por reglas; sin LLM, sin offline
     real, sin nodo fijo.
     FloodNet NYC: sensor ultrasónico; sin capa semántica humana, sin razonamiento, sin
     español regional.
     Acuífero + Vigía: intersección de los cinco, en español rioplatense, totalmente offline, con
     CAP v1.2 estándar y trazas auditables.

Por qué: El jurado evalúa novedad relativa. Decirlo explícitamente evita que un revisor con poca
paciencia asuma que es "otro PetaBencana" o "otro Flood Hub local".
Impacto: MEDIO-ALTO. Esfuerzo: BAJO. Tipo: Agregar nuevo.



🟡 Prioridad Media (si hay margen)
P10. Capa predictiva ligera local
Qué hacer: Modelo simple (regresión sobre últimos N niveles + lluvia reciente del SMN si está
cacheada) que estime la pendiente y emita un "Riesgo proyectado a 30/60/90 min" como
segundo output paralelo al observacional. No requiere modelo nuevo: un numpy.polyfit
honesto basta.
Por qué: Los dos informes señalan que proyectos proactivos (HackAnalog, Crab Alert) suelen
ganar hackathons de alerta temprana porque "anticipar" pesa narrativamente más que
"reportar". Convierte Acuífero de "nowcasting" puro a "nowcasting + short-horizon anticipatory
action", que es el vocabulario que UNDRR/WMO premian.
Impacto: MEDIO. Esfuerzo: BAJO-MEDIO. Tipo: Agregar nuevo.



P11. Sección de cumplimiento normativo argentino
Qué hacer: Dos párrafos en el writeup mencionando:
     Disposición AAIP 2/2023 y Guía de Transparencia y Protección de Datos en IA (AAIP,
     septiembre 2024) — el procesamiento on-device cumple por diseño con la minimización
     de tratamiento y la limitación al dispositivo del usuario.
     AlertAR (Programa Nacional de Sistema de Alerta Temprana, aprobado 2024) —
     payload CAP v1.2 listo para inyección en el ecosistema oficial nacional.
     SINAGIR como receptor institucional descendente.

Por qué: Una mención específica de regulación local convierte "proyecto interesante" en
"propuesta deployment-ready bajo marco vigente". Es exactamente lo que un juez de impacto
humanitario quiere ver, y cubre el track transversal de Safety & Trust con esfuerzo mínimo.
Impacto: MEDIO. Esfuerzo: BAJO. Tipo: Agregar nuevo.



P12. Endorsement institucional informal
Qué hacer: Email, tweet, mensaje o video de 30 s de un funcionario municipal de Defensa Civil
(Tigre, Luján, San Fernando, Areco, La Plata, Resistencia, Concordia) o un bombero voluntario,
diciendo "esto sería útil para nosotros". Incluir como sidebar en el writeup y, si se consigue voz,
en el video.
Por qué: Los ganadores de Gemma 3n citan colaboraciones humanas verificables (hermano
ciego, Eva, escuelas rurales). Acuífero está en Tigre — Defensa Civil municipal de Tigre/San
Fernando/Vicente López/Pilar son contactables. Un mensaje en LinkedIn alcanza.
Impacto: ALTO si se consigue. Esfuerzo: BAJO-MEDIO. Tipo: Agregar nuevo.



P13. Repo público "clone + run" en ≤ 5 minutos
Qué hacer: README con quickstart docker compose up o make demo que levante backend +
frontend + nodo mock con video sample; instrucciones separadas para Pi real y Android real con
comando litert-lm run explícito; licencia Apache 2.0 visible; APK debuggable en releases;
diagrama de arquitectura PNG en raíz; ejemplo de payload CAP v1.2 en samples/ .
Por qué: Repo requisito formal; los jueces técnicos clonan en serio. Si no levanta, voto perdido.
Impacto: MEDIO. Esfuerzo: MEDIO. Tipo: Modificar existente.
P14. Ablation E2B vs E4B en Pi y referencia a 26B MoE como "fog server" opcional
Qué hacer: Tabla mostrando que el sistema funciona con la opción más restrictiva (E2B, 2.5 GB)
y mejora con E4B, sin requerir 26B MoE. Demuestra graceful degradation y conciencia de trade-
offs.
Por qué: Cultura "edge AI" (Qualcomm, Arm, Jetson). Los jueces de AI Edge esperan ver este
análisis.
Impacto: MEDIO. Esfuerzo: MEDIO. Tipo: Agregar nuevo.



🟢 Prioridad Baja / Evitar
P15. NO sobre-ingenierizar antes del cierre
No entrenar modelos desde cero, no fine-tuning ambicioso de Gemma 4 31B, no integrar más
sensores físicos, no agregar dashboard nuevo. Los ganadores compusieron tech existente.

P16. Simplificar la PWA si está consumiendo tiempo
Si tiene features que no aparecen en el video ni son críticos para la demo end-to-end, congelarlos.
Se evalúa la demo, no la matriz de features.



Cambios respecto a la versión anterior
 Movimiento                       Razón

 Nueva P2 (CAP v1.2) subió        El informe largo es enfático: SINAGIR propietario es subóptimo; CAP
 desde "no estaba" a Prioridad    es el estándar mundial que vuelve el proyecto deployment-ready
 Máxima                           globalmente.

 P5 (métricas) bajó de Máxima a   Sigue siendo crítica pero ahora con números objetivo explícitos (5–8
 Alta                             tok/s Pi, >3000 NPU móvil), lo que la hace más mecánica.

 Nueva P7 (firewall anti-         Patrón ganador Gemma Vision (ML Kit + Gemma) es isomórfico a
 alucinación) entró en Alta       OpenCV + Gemma. Verbalizarlo es el argumento más fuerte de
                                  safety con el menor esfuerzo.

 Nueva P9 (diferenciación         FarmWise AI ya ocupó la pista Global Resilience con Gemma 4 E2B.
 explícita)                       Asumir que el jurado va a inferir la diferencia solos es ingenuo.

 Nueva P10 (capa predictiva       Vocabulario UNDRR de "anticipatory action" pesa narrativamente.
 ligera)                          Easy win.
 Movimiento                          Razón

 Nueva P11 (compliance               Disposición 2/2023 + AAIP + AlertAR = madurez profesional con dos
 argentino)                          párrafos.

 Writeup ahora con límite duro       Confirmado por la rúbrica; estructura sugerida calibrada a ese límite.
 1500 palabras

 Video reforzado con guion 4-        Validado por Sentinel y Flood Ready, ambos finalistas/ganadores de
 actos                               eventos comparables.




Plan mínimo de 4 días para cerrar competitivo
 Día          Foco principal                                   Entregables

 D-4 (hoy,    P1 (LiteRT-LM) + P2 (CAP v1.2)                   Nodo emitiendo CAP válido desde Pi con
 14-may)                                                       Gemma 4 E2B vía LiteRT-LM.

 D-3 (15-     P4 (clip argentino) + P5 (métricas) + P8         Benchmark card con números reales;
 may)         (multimodal + function calling)                  pipeline Gemma 4 con function calling
                                                               para sirena/CAP.

 D-2 (16-     P3 (video) — rodaje y primer corte               Cut 1 del video de 3 min con los 4 actos.
 may)

 D-1 (17-     P6 (writeup 1500 pal) + P7 (firewall) + P9       Writeup final, repo navegable, video final,
 may)         (diferenciación) + P11 (compliance) + P13        P12 si llegó endorsement.
              (repo limpio)

 18-may       Submit antes de 23:59 UTC. Buffer de 6 h para
              imprevistos.




Frase narrativa unificada (para abrir video y writeup)
   "Cuando se inunda en Argentina, las alertas llegan tarde, llegan mal, o llegan cuando ya se
   cayó internet. Acuífero + Vigía es un sistema híbrido que mira el agua subir desde un puente
   con Gemma 4 corriendo en una Raspberry Pi vía LiteRT, escucha al vecino que avisa 'el agua
   ya pasó la marca' desde un celular sin señal, y emite una alerta CAP v1.2 lista para AlertAR.
   Todo on-device. Todo en español rioplatense. Todo cuando internet ya no está."

