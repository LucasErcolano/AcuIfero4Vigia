# Acuífero: División de Trabajo 5 Personas

Source PDF: `C:\Users\joaco\Downloads\Acuifero_Division_Trabajo_5_Personas.md.pdf`

---

Plan de División de Trabajo — Equipo de 5 personas
Acuífero 4 + Vigía — Gemma 4 Good Hackathon
Fecha de inicio: jueves 14-may-2026 Deadline: lunes 18-may-2026, 23:59 UTC (~4 días)
Modalidad: trabajo paralelo con dos sincronizaciones diarias (mañana + cierre)



Roles propuestos
 Rol                    Foco principal                          Por qué este rol existe

 A — Edge Node          Raspberry Pi + LiteRT-LM +              P1 (LiteRT) es la tarea de mayor riesgo
 Lead                   benchmarks + clip argentino             técnico y bloqueante para todo lo demás.
                                                                Necesita dueño full-time.

 B — Mobile /           Android + MediaPipe LLM Inference       Stack distinto al de A; corre en paralelo sin
 Vigía Lead             + corpus rioplatense + offline          solaparse.

 C — Backend &          FastAPI + motor de decisión + CAP       Es el "pegamento" entre A y B; trabajo
 Fusion Lead            v1.2 + function calling + capa          sustancial y propio que no cabe en los otros
                        predictiva                              roles.

 D — Storytelling       Video 3 min + writeup 1500 palabras     Video + writeup pesan 60% combinado en
 Lead                   + secciones narrativas + outreach       la rúbrica. Necesita foco.

 E — Integration &      Repo + demo E2E + ablations +           Coordina, cubre huecos, asegura que
 Polish Lead            compliance + buffer/contingencia        A+B+C se integran y el repo es navegable.




Por qué esta división vs. la tuya (2+2+1)
 Tu             Mi propuesta              Diferencia
 propuesta

 2 Acuífero     1 (A) + 1 backup (E)      E cubre Acuífero como segunda línea pero también hace otras
                                          cosas. P1 es crítico pero no necesita dos personas a tiempo
                                          completo.

 2 Vigía        1 (B)                     La app ya está funcional; falta verificación, benchmarks, y
                                          refinamiento del corpus. Un dev es suficiente.

 0 Backend      1 (C)                     El cambio más importante. CAP v1.2 + function calling +
                                          predictivo son trabajo sustancial y específico.
 Tu             Mi propuesta               Diferencia
 propuesta

 1 Video        1 (D) ampliado a           Video + writeup + outreach + secciones del writeup.
                "narrativa completa"

 0              1 (E)                      Sin esto, A+B+C entregan piezas que nadie une.
 Integración




Mapeo de tareas (P1–P14 del plan priorizado) a roles
 Tarea                                 Rol primario                        Apoyo

 P1 Migración LiteRT-LM en Pi          A                                   E

 P2 Output CAP v1.2                    C                                   D (revisa los textos en español
                                                                           del payload)

 P3 Video 3 min, 4 actos               D                                   Todos (filmación día 3)

 P4 Clip argentino real                E                                   A (lo integra al pipeline)

 P5 Benchmark card                     A (Pi) + B (móvil)                  C (latencia E2E)

 P6 Writeup 1500 palabras              D                                   C (sección técnica), A (sección
                                                                           Pi), E (compliance)

 P7 Sección anti-alucinación           D                                   A (le pasa los detalles
                                                                           OpenCV/Gemma)

 P8 Multimodal + function calling      A (multimodal en nodo) + C          B (function calling en móvil si
 Gemma 4                               (function calling en backend)       aplica)

 P9 Diferenciación vs                  D                                   E
 FarmWise/Flood
 Hub/PetaBencana

 P10 Capa predictiva ligera            C                                   —

 P11 Sección compliance argentino      E (investiga)                       D (lo redacta)

 P12 Endorsement Defensa Civil         E (escribe mensaje, hace            D (recibe video/quote si llega)
                                       outreach)

 P13 Repo limpio, docker compose,      E                                   Todos (cada uno documenta su
 README                                                                    parte)
 Tarea                                  Rol primario                       Apoyo

 P14 Ablation E2B vs E4B                E                                  A




Cronograma día por día con dependencias
Día 0 — Jueves 14-may (hoy)
Objetivo: arranque limpio, P1 ya corriendo, video script aprobado.

 Rol     Tareas del día

 A       Levantar LiteRT-LM en Pi. Bajar gemma-4-E2B-it-litert-lm de HuggingFace. Primer
          litert-lm run exitoso.

 B       Verificar que la app Android sigue usando MediaPipe LLM Inference con Gemma 4 (no 3n). Si
         quedó en 3n, swap.

 C       Diseñar esquema CAP v1.2 (qué campos pobla Gemma, cuáles el motor). Primer emisor CAP stub.

 D       Guion del video minuto a minuto. Outline del writeup con conteo de palabras por sección.

 E       Repo: estructura, README skeleton, docker compose, decidir locación del clip argentino + plan de
         filmación. Borrador del mensaje de outreach a Defensa Civil municipal.



Sync de cierre 14-may: ¿LiteRT-LM corre en Pi? Si no, mañana E entra full-time a backstop.



Día 1 — Viernes 15-may
Objetivo: nodos funcionales con métricas, CAP emitiendo, clip argentino filmado.
 Rol   Tareas del día

 A     LiteRT-LM ya estable. Empieza P5 Pi: TTFT, tok/s con y sin MTP, peak RAM. Integra multimodal
       Gemma sobre evidence frame.

 B     Benchmarks móviles (P5): NPU prefill, decode, latencia E2E. Refina corpus rioplatense; mide F1
       sobre ≥50 frases.

 C     CAP v1.2 emitiendo payloads válidos. Empieza function calling para trigger_siren ,
       emit_cap , send_lora .

 D     Escribe Sección 1 (Problema humano) + Sección 2 (Arquitectura) del writeup. Storyboard del video
       terminado.

 E     Filmar/conseguir clip argentino (P4). Envía outreach a Defensa Civil de Tigre/San
       Fernando/Vicente López/Pilar. Empieza P14 ablations en cuanto A tenga benchmarks.



Sync de cierre 15-may: ¿Tenemos clip argentino? ¿Función emit_cap_xml funciona end-to-
end? ¿Métricas Pi y móvil registradas?



Día 2 — Sábado 16-may — DÍA DE FILMACIÓN
Objetivo: video grabado, primer corte avanzado.

 Rol   Tareas del día

 A     Operar nodo Acuífero en vivo durante filmación. Mostrar latencias en pantalla.

 B     Operar app Vigía en vivo (modo avión, audio coloquial, sync al volver red).

 C     Orquestar backend durante demo: muestra tablero con fusión, CAP emitido, sirena disparada.

 D     Director/camarógrafo/editor. Plan: filmar los 4 actos en orden. Reservar 2 h para edición posterior.

 E     Actúa como "operador de Defensa Civil" en Acto 1 si nadie más puede. Captura B-roll. Backup
       técnico de cualquier rol que se trabe.



Recomendación: filmar de 10 a 16 h. Editar D + E hasta cierre del día. Resto vuelve a sus tareas
técnicas a la tarde.
Sync de cierre 16-may: ¿Cut 1 del video listo? ¿Hay quote/video del endorsement? ¿Algún
payload CAP visible en el video?



Día 3 — Domingo 17-may
Objetivo: writeup final, video editado, repo navegable, ablations cerradas.

 Rol     Tareas del día

 A       Polish del demo Pi. Ayuda a E con P14 ablations finales. Documenta su parte para el README.

 B       Polish app Android, métricas finales de corpus. Documenta su parte.

 C       Cierra P10 capa predictiva ligera si llegó. Sino, congela el scope y documenta. Pasa textos del CAP a
         D para revisión.

 D       Edita video final cut. Escribe Secciones 3, 4, 5, 6, 7 del writeup. Integra texto de compliance que le
         pasa E.

 E       P13 repo final: docker compose probado, README ejecutable, screenshots, cover image, diagrama
         de arquitectura. Hace integración E2E corriendo todo en una máquina limpia para validar el
         README. P14 tabla de ablations a D. P11 párrafos de compliance a D.



Sync de cierre 17-may: ¿El writeup ya cuenta palabras y entra en 1500? ¿El video dura ≤ 3 min?
¿Un extraño puede clonar el repo y correr la demo?



Día 4 — Lunes 18-may — DEADLINE 23:59 UTC
Objetivo: submit con 6 h de buffer.

 Tiempo         Acción

 Mañana         Todos revisan el submission completo: video subido a YouTube público, writeup en Kaggle,
                repo público.

 Mediodía       E hace el submission técnico en Kaggle, completa media gallery, confirma elegibilidad para
                Global Resilience + LiteRT.

 18:00          Cierre. Cualquier cosa que no esté lista a esta hora se descarta o se ajusta con tiempo.
 UTC

 23:59          Deadline real. NO submitting en la última hora.
 UTC




Reglas de coordinación
 1. Daily de 15 min a las 10:00 hora local + cierre de 15 min a las 21:00. No más. Lo demás es
    asíncrono.
 2. Un canal único (Slack/Discord/WhatsApp) con threads por rol. Nada de DMs para
    decisiones de proyecto.
 3. El repo es la fuente de verdad. Si no está commiteado, no existe.
 4. A y B no se bloquean entre sí; pueden trabajar 100% en paralelo. C depende de salidas
    estables de A y B desde el Día 1 — coordinar interfaces JSON temprano.
 5. D arranca el writeup el Día 0 con stubs ("Aquí van métricas del P5"). No esperar a que A y B
    terminen.
 6. E es el "responsable de que la demo funcione", no solo del repo. Si la integración rompe el
    Día 3, E entra a debuggear con quien sea.
 7. Scope freeze el Día 3 a las 18:00. Nada nuevo después; solo bug fixes y polish.



Riesgos y contingencias
Riesgo                  Plan

LiteRT-LM no compila    E entra full-time a backstop A. Plan B: usar flutter_gemma o mediapipe-
o no corre Gemma 4 en   genai en Pi vía Python bindings. Plan C: documentar el intento honestamente
Pi                      y mantener Ollama como motor, postular al premio Ollama en vez de LiteRT.

No conseguimos clip     E filma simulación física controlada (bandeja + objetos + marcas) con contexto
argentino               argentino visible. Mejor que USGS Silverado.

Endorsement no llega    Sustituir por testimonio de un ex-brigadista, familiar de vecino afectado, o
                        académico hidrólogo argentino. No vital, sí valioso si llega.

Video pasa de 3 min     D corta el Acto 1 a 30 s; el dolor humano puede comprimirse. Mantener Actos 2-
                        4 completos.

Writeup pasa de 1500    D corta primero P9 (diferenciación) y P11 (compliance), no la sección técnica ni
palabras                el problema.

Alguien se enferma o    E absorbe rol técnico (A/B/C). Si cae D, C escribe writeup técnico + A escribe
desaparece              sección del problema + E coordina video. Si cae E, A y B se autocoordinan en
                        repo.




Carga estimada por persona
Rol                            Horas estimadas en 4 días          Pico de carga

A — Edge Node                  ~35 h                              Día 0–1 (P1 LiteRT)
 Rol                           Horas estimadas en 4 días      Pico de carga

 B — Mobile                    ~25 h                          Día 1 (benchmarks + corpus)

 C — Backend & Fusion          ~30 h                          Día 1–2 (CAP + function calling)

 D — Storytelling              ~35 h                          Día 2–3 (filmación + writeup)

 E — Integration & Polish      ~30 h                          Día 2–3 (repo + integración)

Carga relativamente pareja. A y D son los más cargados; ambos son los que tienen tareas de
mayor peso para el jurado.



Si insistís en mantener 2+2+1
Versión "ajustada" de tu propuesta que también funciona, aunque sub-óptima:
       2 Acuífero: uno hace P1 LiteRT + P5 + P14; el otro hace P2 CAP + P8 function calling + P10
       predictivo (efectivamente es "Acuífero + Backend" combinados).
       2 Vigía: uno hace el lado Android + P5 móvil + corpus; el otro hace writeup + secciones
       P7/P9/P11 + outreach P12 (efectivamente "Vigía + Writeup" combinados, justificado
       porque el Android lead probablemente termina antes y migra).
       1 Video: P3 video + coordina filmación + P13 repo + P4 clip.

Funciona, pero concentra demasiado en algunas personas y deja al rol "video" sin tiempo para
repo + clip si el video se complica. Mi propuesta es más resistente a imprevistos.

