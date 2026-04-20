package com.acuifero.vigia.android.data

import android.content.Context
import android.util.Log
import java.io.File
import kotlin.system.measureTimeMillis

/**
 * On-device Gemma wrapper backed by MediaPipe LLM Inference (gemma4-e2b `.task`).
 *
 * Loaded reflectively so the module compiles even when the `tasks-genai`
 * dependency is not on the classpath (CI / dev machines without Google Maven
 * mirror access). When the real dep is present *and* a model file exists at
 * [modelFile], [structure] runs fully on-device with no network calls.
 *
 * Contract guarantees (P7 requirement):
 * - Cold-start time logged on first call.
 * - [structure] returns null if the model is unavailable; callers must
 *   surface an explicit error to the user (no silent backend fallback).
 * - Model path is `app-internal files dir / gemma4-e2b.task`.
 */
class GemmaOnDevice(private val context: Context) {
    private var inferenceEngine: Any? = null
    private var lastColdStartMs: Long = -1

    val modelFile: File get() = File(context.filesDir, "gemma4-e2b.task")

    fun isAvailable(): Boolean = modelFile.exists()

    fun ensureLoaded(): Boolean {
        if (inferenceEngine != null) return true
        if (!modelFile.exists()) {
            Log.w(TAG, "Gemma .task asset missing at ${modelFile.absolutePath}")
            return false
        }
        return try {
            lastColdStartMs = measureTimeMillis {
                val optionsClass = Class.forName("com.google.mediapipe.tasks.genai.llminference.LlmInference\$LlmInferenceOptions")
                val builder = optionsClass.getMethod("builder").invoke(null)
                builder.javaClass.getMethod("setModelPath", String::class.java)
                    .invoke(builder, modelFile.absolutePath)
                builder.javaClass.getMethod("setMaxTokens", Int::class.javaPrimitiveType)
                    .invoke(builder, 256)
                val options = builder.javaClass.getMethod("build").invoke(builder)
                val llmClass = Class.forName("com.google.mediapipe.tasks.genai.llminference.LlmInference")
                inferenceEngine = llmClass.getMethod("createFromOptions", Context::class.java, optionsClass)
                    .invoke(null, context, options)
            }
            Log.i(TAG, "Gemma loaded in ${lastColdStartMs}ms from ${modelFile.absolutePath}")
            true
        } catch (t: Throwable) {
            Log.e(TAG, "Gemma load failed (is com.google.mediapipe:tasks-genai on the classpath?)", t)
            inferenceEngine = null
            false
        }
    }

    /** Returns raw model output or null on failure. */
    fun generate(prompt: String): String? {
        if (!ensureLoaded()) return null
        val engine = inferenceEngine ?: return null
        return try {
            val method = engine.javaClass.getMethod("generateResponse", String::class.java)
            method.invoke(engine, prompt) as? String
        } catch (t: Throwable) {
            Log.e(TAG, "Gemma generateResponse failed", t)
            null
        }
    }

    /**
     * Structured volunteer-report parser. Mirrors the backend few-shot prompt
     * but lives entirely on-device. Returns the raw JSON string; the caller
     * decodes with Gson into a [ParsedObservation]-shaped object.
     */
    fun structureReport(transcript: String): String? {
        if (transcript.isBlank()) return null
        val prompt = buildFewShotPrompt(transcript)
        val raw = generate(prompt) ?: return null
        val start = raw.indexOf('{')
        val end = raw.lastIndexOf('}')
        if (start == -1 || end == -1 || end < start) return null
        return raw.substring(start, end + 1)
    }

    fun lastColdStartMs(): Long = lastColdStartMs

    companion object {
        private const val TAG = "GemmaOnDevice"

        private fun buildFewShotPrompt(transcript: String): String = """
            Sos un parser de reportes de voluntarios en espanol rioplatense.
            Devolve SOLO un JSON con claves: water_level_category, trend,
            road_status, bridge_status, homes_affected, urgency, summary, confidence.

            Ejemplo: {"water_level_category":"critical","trend":"rising","road_status":"blocked","bridge_status":"unknown","homes_affected":false,"urgency":"critical","summary":"paso la marca","confidence":0.9}
            Ejemplo: {"water_level_category":"low","trend":"stable","road_status":"open","bridge_status":"open","homes_affected":false,"urgency":"low","summary":"tranquilo","confidence":0.9}

            Transcript: $transcript
            JSON:
        """.trimIndent()
    }
}
