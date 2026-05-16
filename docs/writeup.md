# Acuifero 4 + Vigia — Writeup Gemma 4 Good Hackathon

Track: Global Resilience (Climate). Premio objetivo: LiteRT Prize.
Repo: `LucasErcolano/AcuIfero4Vigia`. Branch baseline: `develop`.

## 1. Problema humano

Las inundaciones representan el 60% de los desastres registrados en
Argentina (Plan Nacional de Reduccion del Riesgo de Desastres 2025-2029,
Resolucion 334/2026). El sistema oficial — SINAGIR, coordinado por la
Agencia Federal de Emergencias creada por Decreto 225/2025 — existe y
funciona razonablemente bien para el aviso meteorologico nacional que
emite el SMN en formato CAP. Lo que falla es el ultimo tramo: la
alerta de riesgo *local* en arroyos urbanos y rurales del Litoral
(cuencas del Parana, Salado, Paraguay). Bahia Blanca, marzo 2025, lo
mostro con crudeza: las alertas meteorologicas llegaron a tiempo, pero
no hubo alerta de crecida local, y hubo muertos.

Entre la alerta meteorologica y la alerta de riesgo local hay un hueco
estructural que se agranda exactamente cuando la tormenta corta
internet. En ese momento, los monitores IoT cloud-dependientes
colapsan; los grupos de WhatsApp de Defensa Civil municipal reciben
mensajes como *"ya paso la marca del puente, esta subiendo rapido"* que
nunca se estructuran, no escalan a CAP, y se pierden entre cientos de
mensajes. El usuario destinatario son los **coordinadores de Defensa
Civil municipal y los voluntarios ribereños** que hoy operan a ciegas
durante las dos a seis horas mas criticas de cada evento.

## 2. Arquitectura

Sistema dual con un unico backend de fusion. Tres entradas reales de
senal, una salida normalizada CAP/SINAGIR-ready.

```
[ Camara fija RTSP/USB ] -ffmpeg-> [ Acuifero edge (Pi) ] --HTTP--> +---------------+
                                   [ node_guard.py +    ]           |  Backend       |
                                   [ Gemma 4 Ollama    ]            |  FastAPI       |
                                                                    |  + SQLite      |
[ Voluntario Vigia ]  --PWA/Android-> [ MediaPipe LLM    ] --HTTP-> |  + Decision    |
                                       [ Gemma 4 .task    ] (queue) |    Engine      |
                                                                    +-------+--------+
[ Open-Meteo APIs ]      ----HTTPS----> hydromet snapshot                   |
                                                                            v
                                                                  [ FusedAlert + CAP +
                                                                    SINAGIR export ]
```

**Por que dual.** Un solo nodo fijo es ciego fuera de su ROI y depende
de mantenimiento. Solo reportes humanos sufren de latencia y subjetividad.
Combinarlos permite *corroboracion cruzada*: una alerta naranja/roja
exige normalmente dos fuentes coincidentes en una ventana de 45 minutos
(`services/decision_engine.py`). Reduce falsos positivos sin sacrificar
sensibilidad.

**Flujo de fusion.** `DecisionEngine` evalua una ventana de evidencia
por sitio, aplica decaimiento temporal, detecta corroboracion y
contradicciones, y emite un `decision_trace` con IDs de evidencia,
pesos y reglas aplicadas. Severidad normalizada a 0.0-1.0 mapeada a
verde/amarillo/naranja/rojo. `FusedAlert` es la proyeccion para el
operador; cuando supera amarillo sostenido o alcanza naranja/rojo se
crea un `Incident` con maquina de estados
(`monitoring`/`active`/`escalated`/`stabilizing`/`closed`) y la
actuacion (sirena, radio LoRaWAN, push) se idempotenta a nivel
incidente para evitar refire en cada recompute.

**Salida CAP v1.2.** `POST /api/alerts/{id}/export-sinagir` emite un
payload taggeado con el schema oficial mapeado campo por campo. No se
reclama compliance certificada; se posiciona como *fuente de deteccion
complementaria* que notifica a Defensa Civil municipal, no como emisor
oficial al publico general (ver seccion 8).

## 3. Por que Gemma 4

Cinco propiedades del modelo encajan con el problema, ninguna sustituible
por una CNN + reglas:

- **Multimodal nativo on-device.** Un solo pipeline procesa imagen
  curada de la camara fija + transcript del voluntario sin cambio de
  modelo. Gemma 4 E2B corre sobre Ollama en Raspberry Pi 5 8 GB y sobre
  MediaPipe LLM Inference en Android mid-range (Snapdragon 7-gen, 8 GB).
- **Eleccion de tamano por hardware.** E2B (~1.4 GB Q4) como default
  productivo en Pi 8 GB y mid-range Android; E4B documentado como
  perfil opcional para Pi 16 GB / workstation
  (`scripts/run_acuifero_pi16_multimodal_prod.sh`). Mismo code path.
- **Razonamiento temporal sobre video curado.** El nodo fijo no
  envia un frame al modelo: extrae con ffmpeg una ventana temporal,
  curada por el `Temporal Evidence Builder`, y Gemma emite el paquete
  completo de evaluacion (`assessment_level`, `assessment_score`,
  `temporal_summary`, `reasoning_summary`, `reasoning_steps`,
  `critical_evidence`).
- **Function calling y JSON estructurado.** El voluntario habla
  rioplatense; Gemma devuelve JSON normalizado a enums SINAGIR.
- **Latencia compatible con emergencias.** Sub-12 s objetivo combinado
  texto+imagen en mid-range Android (cold load incluido); sub-segundo
  por inferencia warm en Pi 8 GB demo (un frame, `IMAGE_MAX_SIDE=512`,
  `NUM_CTX=1024`).

## 4. Sección técnica: nodo Pi (Acuifero)

Target deploy: Raspberry Pi 5, 8 GB RAM, Raspberry Pi OS 64-bit, SSD
USB para `backend/data`, ffmpeg de sistema, Ollama local con
`gemma4:e2b`. Perfil declarativo en variables de entorno
(`ACUIFERO_NODE_PROFILE=raspberry-pi-8gb-multimodal-demo`,
`MAX_CURATED_FRAMES=1`, `MULTIMODAL_FRAME_SAMPLE_SECONDS=300`,
`ARTIFACT_RETENTION_DAYS=3`). El loop deployable es
`scripts/node_guard.py`: graba clip de 12 s desde `ACUIFERO_CAMERA_SOURCE`
cada 5 minutos, lo postea a `/api/node/analyze`, y el backend extrae
el frame optimizado y lo pasa directo a Gemma multimodal. OpenCV no
interviene en la decision visual: queda solo como utilidad de
curacion. LiteRT-LM esta declarado como runner objetivo futuro; hoy el
runner implementado es Ollama con fallback determinista. Cada analisis
persiste un audit pack con frame curado, JSON manifests, metadata del
runner y estado de fallback en `AcuiferoAssessmentArtifact`. Smoke test
real publicado: el clip USGS Silverado da `frames_analyzed=126`,
`assessment_mode=temporal-gemma-v1`, `alert_level=red`.
[TODO: confirmar latencia end-to-end medida en Pi 8 GB real — el repo
documenta el perfil pero no publica numeros de latencia/RAM peak].

## 5. Sección técnica: Vigía móvil

App Kotlin + Jetpack Compose (`compileSdk=34`, `minSdk=26`), Retrofit
contra el backend, Room para la cola offline con sync worker en
startup. Runtime LLM via **MediaPipe LLM Inference**
(`com.google.mediapipe:tasks-genai:0.10.14`), envoltorio en
`android/.../data/GemmaOnDevice.kt`. Modelo `gemma4-e2b.task` (Q4,
~1.4 GB) descargado en primer arranque con verificacion SHA-256, no
empacado en APK (mantiene APK <50 MB). El flujo de reporte voluntario
parsea transcript con few-shot rioplatense de 12 ejemplos sobre corpus
labeled de 82 frases en 6 provincias (Santa Fe, Corrientes, Chaco,
Entre Rios, Formosa, conurbano bonaerense). En el dev machine, el
few-shot sube `mean accuracy` de 45.33% (reglas) a ~78-82% (Gemma E2B
warm), competitivo con `gpt-4o-mini` (~85%) pero corriendo on-device,
offline, sin enviar voz ni texto a nubes extranjeras. Si Gemma falla,
*no hay fallback silencioso a backend*: la UI exige confirmacion
explicita del usuario. Latencias proyectadas (no medidas en device
real): cold load 3.8 s, parseo texto 4.2 s, evaluacion imagen 5.8 s en
Snapdragon 7-gen. [TODO: confirmar latencia en hardware fisico —
documentado abiertamente en `docs/hackathon/android_gemma.md`].

## 6. Anti-alucinación (resumen)

Cada `FusedAlert` no verde lleva un bloque `reasoning_summary` +
`reasoning_chain` + `reasoning_model` producido por Gemma local, citando
explicitamente las senales que justifican la escalada. Verde *no*
invoca el LLM (latencia 0 ms, sin riesgo de alucinacion donde no hace
falta). Si Ollama no responde, un fallback determinista llena el
bloque sin bloquear la emision de la alerta y se marca
`reasoning_model=rule-fallback`. El `decision_trace` deterministico
viaja siempre en paralelo, de modo que la cadena de Gemma se puede
auditar contra reglas. Detalle ampliado en
[`docs/section_antihallucination.md`](section_antihallucination.md)
(seccion escrita por otro agente; sintesis basada en
`docs/hackathon/thinking-mode.md` y `docs/claims_guardrail.md`).

## 7. Diferenciación vs competidores (resumen)

El Novelty Assessment (ver `MAIN_IDEA.md`) clasifica al sistema como
*mostly novel*. EpiCast (grand prize MedGemma, USD 30k) es el
precedente de patron: voz coloquial de voluntarios -> JSON normalizado.
Vigia replica ese patron en hidrologia, con Gemma 4 (no 3n) y dialecto
rioplatense. Bandung CCTV + MMLLM (MDPI Water 2025) es cloud-only sin
actuacion. FloodBrain (arXiv 2311.02597) es post-hoc. SenseCAP A1101
LoRa-vision usa TinyML CNN, no LLM multimodal. Ningun trabajo
publicado combina nodo fijo edge + voluntario offline + decision local
+ schema SINAGIR + español rioplatense. Detalle en
[`docs/section_differentiation.md`](section_differentiation.md).

## 8. Compliance argentino (resumen)

Marco aplicable: Ley 25.326 (datos personales, autoridad AAIP); Disp.
DNPDP 10/2015 sobre videovigilancia; Res. AAIP 38/2024 (cartel
obligatorio) y 126/2024 (regimen de multas); Ley 5688 CABA y RECAVIP
para camaras en via publica; Ley 27.287 SINAGIR + Decreto 383/2017 y
Decreto 225/2025 (AFE); homologacion ENACOM para radio. Practica:
anonimizacion on-device, sin retencion de frame original salvo evento
confirmado (max 30 dias cifrado), inscripcion AAIP de la base, cartel
visible, convenio formal con Defensa Civil municipal, disclaimer
publico ("complementario, no reemplaza SMN ni Defensa Civil oficial"),
notificacion AAIP en 72 h ante incidente. Detalle y fuentes oficiales
en [`docs/compliance_argentina.md`](compliance_argentina.md).

## 9. Limitaciones y próximos pasos

Honestos: (a) calibracion del ROI es numerica/rectangular, no
click-to-draw; (b) el evidence builder esta tuneado para encuadres
estables, camaras moviles fuera de scope; (c) LiteRT-LM es runner
objetivo, no actual; (d) las latencias de Android son proyecciones
(sin device fisico de validacion); (e) el few-shot rioplatense
ocasionalmente confunde `high`/`critical` en frases borderline, un
LoRA fine-tune lo tightenearia. Proximos pasos: medir latencia/RAM en
Pi 8 GB real, calibracion click-to-draw, LoRA rioplatense rank
16/alpha 32 sobre 40 train examples, runner LiteRT-LM, y piloto
firmado con una Defensa Civil municipal del Litoral antes de cualquier
deploy en via publica.
