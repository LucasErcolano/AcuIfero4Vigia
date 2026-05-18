# Plan de trabajo: sistema central de integracion

## Proposito del documento

Este documento es un briefing operativo para un agente que llega al proyecto sin contexto previo. Su objetivo es dirigir el trabajo restante del sistema central: la capa que recibe senales del nodo fijo Acuifero, reportes del nodo ciudadano Vigia, contexto hidrometeorologico, y produce alertas fusionadas, trazables y accionables.

La meta no es mejorar por separado Acuifero ni Vigia. La meta es convertir sus salidas en un centro de decision defendible para Defensa Civil municipal.

## Resumen del proyecto

Acuifero 4 + Vigia es un sistema hibrido de alerta temprana de inundaciones pensado para operar aun cuando la conectividad cae durante una tormenta.

El sistema tiene tres grandes bloques:

1. Acuifero: nodo fijo con camara, OpenCV y Gemma local. Observa una escena estable, estima nivel/tendencia del agua y genera `NodeObservation`.
2. Vigia: app/PWA o cliente movil para voluntarios. Captura texto, voz, foto y datos de campo; estructura la observacion en `VolunteerReport` y `ParsedObservation`.
3. Sistema central de integracion: backend FastAPI + SQLite que fusiona evidencia, genera `FusedAlert`, exporta payload SINAGIR-ready, sincroniza edge/central y dispara actuadores.

El avance actual esta mas maduro en las entradas Acuifero/Vigia que en la capa central. La capa central ya existe y funciona para demo, pero sigue siendo un MVP: toma la ultima senal de cada fuente, aplica scoring simple, genera una alerta y dispara actuadores simulados.

## Alcance exacto del sistema central

Incluido:

- Ingesta normalizada de observaciones de nodo fijo, reportes ciudadanos y snapshots hidrometeorologicos.
- Fusion temporal y espacial por sitio.
- Motor de decision con reglas auditables, ponderacion por evidencia y razonamiento local con Gemma cuando corresponda.
- Ciclo de vida de incidentes: apertura, escalamiento, mantenimiento, degradacion y cierre.
- Export SINAGIR-ready y trazabilidad de decisiones.
- Actuadores locales y remotos desacoplados: sirena, radio/LoRa, notificacion app.
- Sync edge -> central con idempotencia, reintentos y estado observable.
- Superficie de operador: endpoints y datos listos para dashboard.
- Tests de integracion end-to-end.

Fuera de alcance salvo que bloquee la integracion:

- Mejoras profundas de vision por computadora en Acuifero.
- UX completa de la app Vigia.
- LiteRT/on-device real del cliente Android.
- Claims de compliance oficial con SINAGIR. Usar siempre "SINAGIR-ready" o "SINAME-ready" hasta verificar contra APIs o documentacion oficial.

## Estado actual que debe asumir el agente

Rama base esperada: `develop`.

Cambios ya integrados:

- `feat/acuifero-node-init`
- `feat/vigia-bootstrap`

Branch a ignorar:

- `feat/video-demo`

Puntos actuales relevantes:

- `backend/src/acuifero_vigia/services/decision_engine.py`
  - `recompute_site_alert()` toma la ultima `NodeObservation`, el ultimo `VolunteerReport` con `ParsedObservation` y el ultimo `HydrometSnapshot`.
  - Usa `max(score)` como base y suma un bonus de corroboracion simple.
  - Crea un `FusedAlert`.
  - Si la alerta es `orange` o `red`, intenta disparar actuadores.

- `backend/src/acuifero_vigia/api/routers/alerts.py`
  - Lista alertas.
  - Expone detalle con trazas parseadas.
  - Recalcula alertas por sitio.
  - Exporta payload `sinagir-ready-v1`.

- `backend/src/acuifero_vigia/services/actuators.py`
  - Define tool calling via Ollama/Gemma.
  - Incluye actuadores stub/log para sirena, radio y app.
  - Por diseno no debe romper el pipeline si falla.

- `backend/src/acuifero_vigia/api/routers/sync.py`
  - Copia entidades pendientes desde `edge.db` a `central.db`.
  - Falta idempotencia fuerte, reintentos detallados, conflictos, lotes y observabilidad.

- `backend/src/acuifero_vigia/models/domain.py`
  - Contiene los modelos persistidos principales: `Site`, `NodeObservation`, `VolunteerReport`, `ParsedObservation`, `HydrometSnapshot`, `FusedAlert`, `SyncQueueItem`, `AcuiferoAssessmentArtifact`.

## Primeros comandos de orientacion

Ejecutar desde la raiz del repo:

```powershell
git status --short --branch
rg --files docs backend/src/acuifero_vigia backend/tests frontend/src
Get-Content -Raw docs/architecture.md
Get-Content -Raw backend/src/acuifero_vigia/services/decision_engine.py
Get-Content -Raw backend/src/acuifero_vigia/models/domain.py
```

No incluir `tools/` si aparece como no trackeado. Contiene tooling/assets externos y no forma parte de este plan salvo instruccion explicita.

## Principios de direccion

1. Priorizar el centro de comando, no las entradas.
   Acuifero y Vigia ya producen senales utiles. El diferencial restante esta en probar que el sistema central las convierte en decisiones confiables.

2. Mantener una sola arquitectura.
   No presentar dos productos. Todo debe converger en: dos fuentes principales, un schema, una alerta fusionada, una accion.

3. Hacer trazable cada escalamiento.
   Una alerta `orange` o `red` debe poder explicar que fuentes participaron, que reglas dispararon, que evidencia se uso y que actuadores se invocaron.

4. Disenar para operar offline.
   El sistema central debe tolerar que edge y central se separen, acumulen eventos y luego sincronicen sin duplicar ni perder informacion critica.

5. Evitar claims institucionales no verificados.
   Exportar `SINAGIR-ready` es correcto. Decir "compliant" o "integrado oficialmente" no lo es.

## Modelo objetivo

El sistema central debe evolucionar de "recalculo de ultima senal" a "gestion de incidente".

Modelo conceptual recomendado:

```text
Site
  -> EvidenceEvent[]
       -> node_observation
       -> volunteer_observation
       -> hydromet_snapshot
       -> manual_operator_note
  -> Incident
       -> current_level
       -> lifecycle_state
       -> opened_at / updated_at / closed_at
       -> evidence_window
       -> decision_versions[]
       -> actuation_records[]
  -> FusedAlert
       -> public/operator-facing projection
```

No hace falta implementar todos los nombres exactamente asi. La direccion importante es separar:

- evidencia recibida,
- decision calculada,
- incidente operacional,
- acciones ejecutadas.

## Trabajo pendiente por prioridad

### P0 - Fijar contratos y criterios de severidad

Objetivo: que todas las fuentes hablen un lenguaje comun antes de fusionarlas.

Tareas:

- Definir un contrato interno para eventos de evidencia por sitio.
- Normalizar severidades en una escala comun `0.0 - 1.0`.
- Documentar que significa `green`, `yellow`, `orange`, `red`.
- Definir umbrales minimos por fuente:
  - Nodo fijo cruza linea critica.
  - Reporte humano menciona marca superada, subida rapida, viviendas afectadas, corte de ruta o puente comprometido.
  - Hydromet indica lluvia/caudal compatible con escalamiento.
- Agregar tests unitarios para `level_from_score()` y reglas de severidad.

Archivos probables:

- `backend/src/acuifero_vigia/services/decision_engine.py`
- `backend/src/acuifero_vigia/schemas/api.py`
- `backend/src/acuifero_vigia/models/domain.py`
- `backend/tests/`

Criterio de aceptacion:

- Dado el mismo conjunto de senales, el motor produce siempre el mismo nivel y una traza legible.
- Los umbrales estan documentados y testeados.

### P1 - Implementar fusion temporal real

Objetivo: dejar de usar solamente la ultima senal y evaluar una ventana temporal coherente.

Tareas:

- Definir ventana por defecto, por ejemplo ultimos 30-60 minutos por sitio.
- Consultar multiples `NodeObservation`, `ParsedObservation` e `HydrometSnapshot`.
- Aplicar decaimiento temporal: evidencia reciente pesa mas que evidencia vieja.
- Detectar corroboracion entre fuentes dentro de la ventana.
- Detectar contradicciones:
  - Nodo marca bajo riesgo, voluntarios reportan riesgo alto.
  - Hydromet no acompana, pero hay evidencia local fuerte.
- Guardar en `decision_trace` los eventos usados, no solo scores agregados.

Archivos probables:

- `backend/src/acuifero_vigia/services/decision_engine.py`
- `backend/src/acuifero_vigia/models/domain.py`
- `backend/tests/test_decision_engine.py` o equivalente.

Criterio de aceptacion:

- Dos senales medias de fuentes distintas dentro de la ventana escalan mas que una sola senal media.
- Una senal vieja no mantiene una alerta alta indefinidamente.
- La traza explica ventana, fuentes, pesos y reglas.

### P2 - Crear ciclo de vida de incidente

Objetivo: que el sistema no genere alertas aisladas sin continuidad operacional.

Tareas:

- Agregar modelo `Incident` o equivalente.
- Relacionar `FusedAlert` con incidente activo.
- Definir estados:
  - `monitoring`
  - `active`
  - `escalated`
  - `stabilizing`
  - `closed`
- Definir reglas de apertura:
  - primer `yellow` sostenido,
  - cualquier `orange` o `red`,
  - reporte humano critico.
- Definir reglas de cierre:
  - periodo sin senales de riesgo,
  - confirmacion manual,
  - descenso sostenido.
- Evitar crear un incidente nuevo en cada recompute.

Archivos probables:

- `backend/src/acuifero_vigia/models/domain.py`
- `backend/src/acuifero_vigia/services/decision_engine.py`
- `backend/src/acuifero_vigia/api/routers/alerts.py`
- `backend/tests/`

Criterio de aceptacion:

- Recomputes sucesivos actualizan el mismo incidente mientras el evento sigue activo.
- La API puede mostrar estado actual, historial de escalamiento y cierre.

### P3 - Versionar decisiones y evidencia

Objetivo: que cada decision sea auditable y reproducible.

Tareas:

- Crear una entidad de snapshot/version de decision o enriquecer `FusedAlert`.
- Persistir:
  - IDs de evidencia usada.
  - ventana temporal.
  - pesos aplicados.
  - reglas disparadas.
  - modelo LLM usado, si hubo.
  - resumen razonado.
  - actuadores solicitados y resultado.
- Evitar almacenar solo strings opacos cuando convenga JSON estructurado.
- Mantener compatibilidad con endpoints existentes.

Archivos probables:

- `backend/src/acuifero_vigia/models/domain.py`
- `backend/src/acuifero_vigia/services/reasoning.py`
- `backend/src/acuifero_vigia/services/decision_engine.py`
- `backend/src/acuifero_vigia/api/routers/alerts.py`

Criterio de aceptacion:

- Un operador puede abrir una alerta y ver por que se genero.
- Un test puede reconstruir la decision desde evidencia fixture.

### P4 - Endurecer actuadores

Objetivo: pasar de stubs de demo a una capa conectable, verificable y segura.

Tareas:

- Agregar modelo `ActuationRecord`.
- Registrar cada intento:
  - tipo de actuador,
  - payload,
  - estado,
  - error si fallo,
  - timestamp,
  - alerta/incidente asociado.
- Implementar idempotencia por alerta/incidente para no disparar dos veces la misma sirena.
- Separar decision de accion:
  - el motor recomienda acciones,
  - el dispatcher ejecuta,
  - el resultado queda persistido.
- Mantener los stubs actuales para test y demo.
- Preparar interfaces para GPIO/LoRa/push sin requerir hardware en CI.

Archivos probables:

- `backend/src/acuifero_vigia/services/actuators.py`
- `backend/src/acuifero_vigia/models/domain.py`
- `backend/src/acuifero_vigia/services/decision_engine.py`
- `backend/tests/`

Criterio de aceptacion:

- Una alerta roja registra que actuadores se intentaron y cuales fueron exitosos.
- Recalcular la misma alerta no duplica acciones criticas.
- Si falla un actuador, la alerta sigue creada y el error queda visible.

### P5 - Mejorar sync edge -> central

Objetivo: que la desconexion y reconexion sean parte real del producto, no solo una demo feliz.

Tareas:

- Agregar identificadores estables por entidad sincronizable.
- Hacer `SyncQueueItem` idempotente.
- Guardar intentos, ultimo error y timestamps de sync.
- Procesar por lotes con respuesta parcial.
- Definir politica de conflicto:
  - append-only para evidencia,
  - merge/update para estado de incidente,
  - no sobrescribir decisiones centrales mas nuevas con edge viejo.
- Agregar endpoint de estado de sync.
- Testear duplicados y reconexion.

Archivos probables:

- `backend/src/acuifero_vigia/api/routers/sync.py`
- `backend/src/acuifero_vigia/models/domain.py`
- `backend/src/acuifero_vigia/api/deps.py`
- `backend/tests/test_sync.py`

Criterio de aceptacion:

- Enviar dos veces el mismo item no duplica evidencia ni alertas.
- Un fallo parcial deja items pendientes con error claro.
- La API informa cuantos items estan pendientes, sincronizados y fallidos.

### P6 - Completar API de operador

Objetivo: exponer datos listos para una consola central simple.

Tareas:

- Endpoint de resumen por sitio:
  - nivel actual,
  - incidente activo,
  - ultima evidencia por fuente,
  - estado de sync,
  - ultima accion ejecutada.
- Endpoint de timeline de incidente.
- Endpoint para acknowledgement manual.
- Endpoint para cierre manual con motivo.
- Endpoint para exportar alerta/incidente en formato institucional.

Archivos probables:

- `backend/src/acuifero_vigia/api/routers/alerts.py`
- nuevo router opcional `backend/src/acuifero_vigia/api/routers/incidents.py`
- `backend/src/acuifero_vigia/schemas/api.py`

Criterio de aceptacion:

- El frontend puede dibujar un dashboard central sin reinterpretar reglas.
- La API diferencia evidencia cruda, decision y estado operacional.

### P7 - Tests end-to-end de historia completa

Objetivo: probar el flujo que se va a mostrar y defender.

Escenario minimo:

1. Crear sitio con calibracion.
2. Ingresar reporte Vigia offline con texto critico.
3. Ingresar `NodeObservation` de Acuifero con cruce de linea critica.
4. Ingresar `HydrometSnapshot` compatible.
5. Recomputar alerta.
6. Verificar `FusedAlert` roja o naranja.
7. Verificar traza, reasoning y actuadores.
8. Encolar sync.
9. Ejecutar `/sync/flush`.
10. Verificar que central contiene evidencia y alerta sin duplicados.

Archivos probables:

- `backend/tests/test_central_integration_flow.py`
- fixtures existentes de backend.

Criterio de aceptacion:

- El test corre sin servicios externos.
- Si Gemma/Ollama no esta disponible, el fallback deterministico mantiene el flujo.

### P8 - Documentacion de demo y decisiones

Objetivo: que el jurado o un revisor entienda por que la integracion es novedosa y operable.

Tareas:

- Actualizar `docs/architecture.md` con el modelo final.
- Crear o completar mapping SINAGIR-ready si falta.
- Documentar escenarios:
  - solo Acuifero,
  - solo Vigia,
  - Acuifero + Vigia corroborados,
  - conectividad caida y posterior sync.
- Documentar limites conocidos:
  - no compliance oficial,
  - actuadores reales reemplazables,
  - scoring inicial calibrable.

Archivos probables:

- `docs/architecture.md`
- `docs/demo-script.md`
- `docs/hackathon/sinagir-mapping.md` o equivalente.

Criterio de aceptacion:

- Un agente nuevo puede correr la demo y explicar cada decision.

## Orden recomendado de ejecucion

Implementar en este orden:

1. P0 - Contratos y criterios de severidad.
2. P1 - Fusion temporal real.
3. P7 - Test end-to-end minimo, aunque al principio falle.
4. P2 - Ciclo de vida de incidente.
5. P3 - Versionado de decisiones y evidencia.
6. P4 - Actuadores persistidos e idempotentes.
7. P5 - Sync robusto.
8. P6 - API de operador.
9. P8 - Documentacion final y demo.

Razon: primero se estabiliza el significado de una decision, despues se prueba el flujo completo, y recien despues se agregan estado operacional, actuacion y sync robusto.

## Reglas de implementacion

- Mantener cambios chicos y testeables.
- No reescribir Acuifero/Vigia salvo que haya un contrato roto.
- No meter dependencias nuevas si el stack actual alcanza.
- Preservar fallback deterministico cuando Gemma/Ollama no este disponible.
- No hacer que actuadores rompan el pipeline de alertas.
- Preferir JSON estructurado para trazas nuevas.
- Mantener endpoints existentes compatibles salvo que se actualicen tests y frontend.
- No commitear assets generados, modelos ni contenido de `tools/`.

## Validacion minima antes de cerrar cada bloque

Backend:

```powershell
cd backend
.\.venv\Scripts\python.exe -m pytest
```

Frontend, si se tocan superficies web:

```powershell
cd frontend
npm test
npm run lint
```

Android, si se toca el cliente movil:

```powershell
cd android
.\gradlew.bat :app:testDebugUnitTest
```

Nota: si Android falla por `JAVA_HOME` o falta de `java`, reportarlo como bloqueo de entorno, no como fallo de codigo.

## Definicion de terminado para el sistema central

El sistema central puede considerarse listo para hackathon cuando cumple esto:

- Recibe y persiste evidencia de Acuifero, Vigia e hydromet.
- Fusiona multiples eventos dentro de una ventana temporal.
- Genera una alerta con nivel, score, resumen y traza estructurada.
- Mantiene un incidente activo en lugar de alertas sueltas.
- Explica la decision con reglas y, si esta disponible, razonamiento local.
- Dispara o registra actuadores de forma idempotente.
- Sincroniza edge -> central sin duplicar registros.
- Expone endpoints suficientes para dashboard y export institucional.
- Tiene un test end-to-end que cubre la historia principal sin depender de red externa.

## Mensaje de direccion para el agente ejecutor

Si tenes que elegir una sola cosa para avanzar: fortalece `decision_engine.py` hasta que pueda defender una alerta frente a un operador humano.

No optimices aun la camara ni la app ciudadana. El mayor riesgo del proyecto es que Acuifero y Vigia parezcan dos demos pegadas. El trabajo del sistema central es demostrar que son dos entradas de una misma decision operacional.
