package com.acuifero.vigia.android.data

import android.content.Context
import org.junit.After
import org.junit.Assert.assertEquals
import org.junit.Assert.assertFalse
import org.junit.Assert.assertNull
import org.junit.Before
import org.junit.Test
import org.mockito.kotlin.doReturn
import org.mockito.kotlin.mock
import java.io.File
import java.nio.file.Files

/**
 * Unit tests for [GemmaOnDevice]. The wrapper uses reflection to talk to
 * MediaPipe at runtime, so without a real model file at filesDir/gemma4-e2b.task
 * every entry point must short-circuit safely.
 */
class GemmaOnDeviceTest {
    private lateinit var tempDir: File
    private lateinit var context: Context

    @Before
    fun setUp() {
        tempDir = Files.createTempDirectory("gemma-test").toFile()
        context = mock {
            on { filesDir } doReturn tempDir
        }
    }

    @After
    fun tearDown() {
        tempDir.deleteRecursively()
    }

    @Test
    fun `isAvailable returns false when model file missing`() {
        val gemma = GemmaOnDevice(context)
        assertFalse(gemma.isAvailable())
    }

    @Test
    fun `structureReport returns null when model file missing`() {
        val gemma = GemmaOnDevice(context)
        assertNull(gemma.structureReport("hola, el agua subio"))
    }

    @Test
    fun `generate returns null without crashing when model file missing`() {
        val gemma = GemmaOnDevice(context)
        assertNull(gemma.generate("hi"))
    }

    @Test
    fun `modelFile resolves under filesDir`() {
        val gemma = GemmaOnDevice(context)
        assertEquals(File(tempDir, "gemma4-e2b.task").absolutePath, gemma.modelFile.absolutePath)
    }
}
