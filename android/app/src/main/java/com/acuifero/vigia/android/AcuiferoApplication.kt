package com.acuifero.vigia.android

import android.app.Application
import androidx.work.Constraints
import androidx.work.ExistingWorkPolicy
import androidx.work.NetworkType
import androidx.work.OneTimeWorkRequestBuilder
import androidx.work.WorkManager
import com.acuifero.vigia.android.data.GemmaOnDevice
import com.acuifero.vigia.android.data.SyncQueuedReportsWorker

class AcuiferoApplication : Application() {
    val gemma: GemmaOnDevice by lazy { GemmaOnDevice(this) }

    override fun onCreate() {
        super.onCreate()
        val request = OneTimeWorkRequestBuilder<SyncQueuedReportsWorker>()
            .setConstraints(
                Constraints.Builder()
                    .setRequiredNetworkType(NetworkType.CONNECTED)
                    .build()
            )
            .build()
        WorkManager.getInstance(this).enqueueUniqueWork(
            "sync-pending-reports",
            ExistingWorkPolicy.KEEP,
            request,
        )
    }
}
