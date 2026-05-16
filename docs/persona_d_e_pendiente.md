# Persona D + E — Storytelling + Integration & Polish — Trabajo pendiente

Documento auto-contenido. No requiere contexto previo. Seguilo paso a paso.

---

## 1. Contexto del proyecto

**Proyecto:** Acuifero 4 + Vigia. Sistema dual de alerta temprana de inundaciones para Argentina, hackathon **Gemma 4 Good** (deadline lunes 18-may-2026, 23:59 UTC).

**Componentes:**
- **Acuifero (edge node, Persona A):** Raspberry Pi con cámara, Gemma 4 multimodal vía LiteRT-LM. Detecta agua/cambio visual.
- **Vigia (app Android, Persona B):** Gemma 4 + MediaPipe LLM Inference. Reporte ciudadano en español rioplatense, offline.
- **Backend FastAPI (Persona C):** fusión nodo+ciudadano, function calling con guard, CAP v1.2, predicción ligera. **COMPLETADO** (ver `docs/persona_c_backend_pendiente.md`).
- **Storytelling + Polish (TU ROL, Persona D+E combinada):** writeup, video 3 min, repo limpio, compliance, demo E2E, ablations.

**Equipo:** 4 personas. D y E las hace una sola persona (vos).

**Carga estimada D+E combinada:** ~50-60 horas en lo que queda al deadline.

---

## 2. Lo que YA está hecho (no rehacer)

Todos estos archivos ya están commiteados en branch `chore/repo-polish-compliance`:

- `docs/writeup.md` — writeup 1412 palabras, 9 secciones
- `docs/section_antihallucination.md` — sección anti-alucinación 778 palabras
- `docs/section_differentiation.md` — diferenciación vs Flood Hub/PetaBencana/PREVENIR/INA SIyAH/etc.
- `docs/compliance_argentina.md` — compliance AR (Ley 25.326, AAIP, SINAGIR, mitigaciones)
- `docs/audit_D_E.md` — auditoría inicial estado D+E vs repo
- `docs/p4_clip_candidates.md` — 6 candidatos clip real (top: AFP Bahía Blanca 2025)
- `docs/talking_head_guide.md` — guía de filmación talking-head
- `docs/hackathon-pdfs/` — PDFs del hackathon archivados
- `README.md` — Repository layout, Architecture ASCII, Stack, Quick start
- `LICENSE` — Apache 2.0
- `docker-compose.yml` + `backend/Dockerfile`
- `.gitignore` endurecido (secrets, internal tools, agent configs)
- **P12 Outreach Defensa Civil** — enviado, fuera de scope

**Video preproducción ya hecho:**
- Timeline 3:00 dividido en 8 bloques
- `docs/hackathon/video/narration.md` + `narration.wav` (locución técnica grabada)
- 7 hyperframes renderizados en `docs/hackathon/video/raw/`
- 9 UI scenes + screenshots
- EDL (edit decision list) listo

---

## 3. Tareas pendientes

Ordenadas por prioridad temporal. Empezar de arriba hacia abajo.

---

### TAREA 1 — Filmar talking-head (HOY, ~1h, sin dependencias)

**Qué:** grabar tomas a cámara de apertura (B01, ~15s) y cierre (B08, ~15s) del video.

**Cómo:** seguir `docs/talking_head_guide.md` (guía completa con guion, setup técnico, protocolo).

**Entregable:** archivos crudos en `docs/hackathon/video/raw/talking_head/`:
```
talking_head_B01_take1.mp4 (a take3)
talking_head_B08_take1.mp4 (a take3)
```

**Por qué primero:** no depende de nada. Si lo dejás para sábado se solapa con filmación principal.

---

### TAREA 2 — Descargar clip P4 (HOY, ~30 min)

**Qué:** descargar el video real de inundación que va a ir como B-roll del video.

**Cómo:**
1. Abrir `docs/p4_clip_candidates.md`.
2. Top candidato: AFP Bahía Blanca marzo 2025 (YouTube `wVYMnB88Fjc`). Score 9/10.
3. Descargar con `yt-dlp`:
   ```
   yt-dlp -f "bv*+ba/b" -o "docs/hackathon/video/raw/p4_clip/afp_bahia_blanca_2025.mp4" "https://www.youtube.com/watch?v=wVYMnB88Fjc"
   ```
4. Si falla → bajar candidato #2 (CNN Español AMBA mayo 2025) o #3 (Pexels CDMX).
5. Bajar también backup: Wikimedia Commons radar SMN Bahía Blanca (CC BY-SA, libre). URL en el doc.

**Entregable:** archivos en `docs/hackathon/video/raw/p4_clip/`.

**Crédito obligatorio:** en el video final aparece "Imágenes: AFP, marzo 2025" en pantalla o créditos. Sin esto no se puede usar.

**Restricción:** NO usar clips generados por IA. NO usar deepfakes. Si el jurado detecta clip falso simulando inundación real, resta credibilidad.

---

### TAREA 3 — Grabar screencast B05 (cuando demo E2E corra, sábado o domingo)

**Qué:** grabación de pantalla del backend en vivo durante el bloque 5 del video. Muestra fusión nodo+ciudadano, function calling validado, CAP XML emitido, sirena disparada.

**Dependencia:** demo E2E funcionando. Backend C ya está completado (CAP `/cap/emit`, function calling con guard, fusión, predictivo). Falta integrar con nodo A y app B en vivo.

**Cómo:**
1. Coordinar con A+B+C para sesión de demo. Avisar 24h antes.
2. Levantar stack completo con docker-compose + Pi corriendo + Android.
3. Disparar evento de inundación simulada (mock data o demo asset).
4. Grabar pantalla a 1080p mínimo con OBS o herramienta similar.
5. Mostrar en pantalla:
   - Dashboard backend con señales entrando
   - Decisión de fusión (logs)
   - Tool call validado por action_guard
   - CAP XML generado (endpoint `/cap/emit`)
   - Notificación de actuación (sirena/LoRa)
6. Audio limpio, sin notificaciones, sin teclado ruidoso.

**Entregable:** `docs/hackathon/video/raw/screencast_B05.mp4` (~30 segundos útiles).

---

### TAREA 4 — Filmar acto principal del video (sábado 16-may, día completo)

**Qué:** los 4 actos del video, según EDL en `docs/hackathon/video/`.

**Logística previa (viernes):**
- Confirmar locación de filmación (decisión ya tomada, ver notas internas).
- Cargar todas las baterías (cel, lavalier, Pi, Android demo).
- Imprimir guion + EDL.
- Reservar **2 horas para edición posterior** el mismo sábado.

**Equipo mínimo:**
- 1 cámara (cel + trípode).
- 1 mic lavalier o auriculares con micrófono.
- Iluminación lateral (luz natural o lámpara difusa).
- Pi Acuifero operativo (Persona A presente o entrenada).
- Android Vigía operativo (Persona B presente o entrenada).
- Vos como director/camarógrafo/editor.

**Plan del día:**
1. Setup 1h.
2. Filmar 4 actos en orden, 3 tomas por bloque mínimo.
3. A opera Pi en vivo, muestra latencias en pantalla.
4. B opera Vigía en modo avión + audio coloquial + sync.
5. C orquesta backend con dashboard visible.
6. Pausa de 2h para edición preliminar.

**Entregable:** carpeta `docs/hackathon/video/raw/main_shoot/` con todas las tomas.

---

### TAREA 5 — Ensamblar video final (domingo 17-may)

**Qué:** montar todo en editor (DaVinci Resolve recomendado, gratis; o CapCut/Premiere).

**Material a integrar:**
- Talking-head B01 + B08 (Tarea 1).
- Clip P4 (Tarea 2).
- Screencast B05 (Tarea 3).
- 7 hyperframes ya renderizados.
- 9 UI scenes + screenshots.
- Narration.wav (locución técnica ya grabada).
- Tomas filmadas sábado (Tarea 4).

**Seguir el EDL** ya escrito (ruta en `docs/hackathon/video/`). NO improvisar timeline.

**Pasos:**
1. Importar todo al proyecto.
2. Cortar según EDL.
3. Sincronizar audio con narration.wav.
4. Color pass uniforme (matchear material mixto).
5. Audio pass (denoising, normalización a -14 LUFS).
6. Texto: títulos de bloque, créditos finales (AFP, CC BY-SA Wikimedia, etc.).
7. Export H.264 1080p, ~10-20 Mbps. Duración exacta 3:00.

**Entregable:** `docs/hackathon/video/final/acuifero_vigia_3min.mp4`.

**Validación pre-submit:**
- Duración exacta 3:00 (o lo que pida el reglamento).
- Audio audible sin auriculares.
- Créditos completos (AFP, Wikimedia, equipo, hackathon).
- Subtítulos en inglés si el reglamento lo pide.

---

### TAREA 6 — Resolver TODOs del writeup (domingo, ~2h)

**Qué:** `docs/writeup.md` tiene 2 TODOs marcados con números pendientes:

1. **Latencia E2E + RAM peak Pi 8GB** (sección 4). Persona A los está midiendo. Cuando los pase, reemplazar `[TODO: confirmar métrica]` con valor real.
2. **Latencia Android hardware físico** (sección 5). Persona B o C la mide. Mismo procedimiento.

**Acción:** pinguear A y B/C el sábado a la mañana. Si no llegan los números para domingo a la noche → dejar el rango proyectado actual con disclaimer claro: "estimación basada en benchmarks públicos de MediaPipe; pendiente validación en hardware físico". No inventar números.

---

### TAREA 7 — P14 Ablation E2B vs E4B (domingo, bloqueado por A)

**Qué:** comparar Gemma 4 E2B (más chico) vs E4B (más grande) en el nodo Pi. Reportar trade-off latencia/calidad.

**Dependencia:** A tiene que tener LiteRT-LM corriendo con ambos modelos disponibles.

**Cómo:**
1. Pedir a A acceso al script o setup para correr el modelo.
2. Definir corpus de prueba: 20-30 frames de inundación (puede ser el clip P4 cortado en frames + frames sintéticos del repo).
3. Correr cada modelo sobre el corpus. Medir:
   - TTFT (time to first token)
   - Tokens/segundo
   - RAM peak
   - Calidad de respuesta (manual scoring 1-5 sobre N=20)
4. Tabla resultado en `docs/ablation_e2b_e4b.md`.
5. Recomendación final: cuál usar para producción y por qué.

**Si A no llega:** dejar la sección con disclaimer "ablation pendiente, se publicará post-deadline en repo público".

---

### TAREA 8 — Demo E2E + integración final (domingo noche)

**Qué:** asegurar que todo el sistema corre end-to-end al menos una vez de manera reproducible.

**Cómo:**
1. `docker-compose up` levanta backend.
2. Pi corre nodo Acuifero apuntando a backend.
3. Android corre app Vigía apuntando a backend.
4. Disparar evento de prueba.
5. Validar que llega CAP XML al endpoint `/cap/emit` y se ejecuta tool call por action_guard.
6. Documentar en `README.md` el procedimiento exacto de demo (jurado puede pedir reproducir).

**Backup plan:** si la demo en vivo falla, tener el screencast B05 + logs grabados como evidencia.

---

### TAREA 9 — Submit final (lunes antes de 23:59 UTC)

**Checklist pre-submit:**
- [ ] Video final exportado y subido (URL pública o adjunto según reglamento)
- [ ] Writeup en formato pedido (PDF / Markdown / link)
- [ ] Repo público con README claro
- [ ] Branch principal mergeada (mergear `chore/repo-polish-compliance` → `develop` → `main` o lo que aplique)
- [ ] LICENSE presente
- [ ] Credits en video con todas las atribuciones
- [ ] Compliance argentino documentado y linkeado en writeup
- [ ] Demo reproducible documentada
- [ ] Submit confirmado en plataforma del hackathon

---

## 4. Riesgos y mitigaciones

| Riesgo | Probabilidad | Mitigación |
|--------|-------------|------------|
| A no termina LiteRT-LM a tiempo | Media | Writeup marca como "objetivo futuro". Demo usa Ollama backup. |
| Clip P4 falla en descarga o pierde licencia | Baja | 6 candidatos disponibles. Fallback Wikimedia CC. |
| Filmación sábado se cae por clima/disponibilidad | Media | Reservar domingo mañana como buffer. |
| Latencia E2E no se mide a tiempo | Alta | Disclaimer honesto, no inventar números. |
| Demo en vivo falla durante grabación | Alta | Screencast B05 grabado con éxito previo como backup. |

---

## 5. Coordinación con otros roles

**Pings que necesitás hacer:**
- **Persona A:** métricas Pi (TTFT, tok/s, RAM peak, latencia), confirmar LiteRT-LM operativo, disponibilidad para ablation P14, presencia sábado filmación, capa OpenCV pre-LLM (si la implementan, actualizar `section_antihallucination.md`).
- **Persona B:** métricas Android hardware físico, presencia sábado filmación.
- **Persona C:** demo E2E coordinada, screencast B05 con dashboard visible, latencia E2E desde backend.

**Mergeo de branch:** `chore/repo-polish-compliance` tiene 4 commits con compliance + writeup + secciones + repo polish + talking-head guide + persona C backlog + P4 candidatos. NO toca código de componentes. Mergeable a `develop` cuando los otros lo aprueben.

---

## 6. Cronograma sugerido

| Día | Tarea principal |
|-----|----------------|
| Hoy (sábado AM) | TAREA 1 talking-head + TAREA 2 clip P4 descargado |
| Sábado | TAREA 4 filmación principal (día completo) + edición preliminar |
| Domingo | TAREA 3 screencast B05 + TAREA 5 ensamblar video + TAREA 6 TODOs writeup + TAREA 7 ablation + TAREA 8 demo E2E |
| Lunes | TAREA 9 submit + buffer para fixes de último momento |

---

## 7. Definition of done global

D+E entrega:
- Video final 3:00 exportado.
- Writeup final con TODOs resueltos o con disclaimer honesto.
- Repo limpio mergeado a main.
- Demo E2E documentada y reproducible.
- Compliance + diferenciación + anti-alucinación cubiertos.
- Submit confirmado antes de lunes 18-may-2026 23:59 UTC.
