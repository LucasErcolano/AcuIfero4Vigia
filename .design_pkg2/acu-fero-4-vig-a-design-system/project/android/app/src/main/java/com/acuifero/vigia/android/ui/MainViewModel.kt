package com.acuifero.vigia.android.ui

import android.content.Context
import androidx.lifecycle.ViewModel
import androidx.lifecycle.ViewModelProvider
import androidx.lifecycle.viewModelScope
import com.acuifero.vigia.android.data.AcuiferoRepository
import com.acuifero.vigia.android.data.AlertSummary
import com.acuifero.vigia.android.data.CalibrationPayload
import com.acuifero.vigia.android.data.CalibrationResponse
import com.acuifero.vigia.android.data.ExternalSnapshot
import com.acuifero.vigia.android.data.NodeAnalysisResponse
import com.acuifero.vigia.android.data.PendingReportEntity
import com.acuifero.vigia.android.data.ReportEnvelope
import com.acuifero.vigia.android.data.RuntimeStatus
import com.acuifero.vigia.android.data.SiteDetail
import com.acuifero.vigia.android.data.SiteSummary
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.SharingStarted
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.flow.stateIn
import kotlinx.coroutines.launch

data class DashboardState(
    val runtime: RuntimeStatus? = null,
    val sites: List<SiteSummary> = emptyList(),
    val alerts: List<AlertSummary> = emptyList(),
    val isLoading: Boolean = false,
    val error: String? = null,
)

data class SiteScreenState(
    val site: SiteDetail? = null,
    val calibration: CalibrationResponse? = null,
    val snapshot: ExternalSnapshot? = null,
    val analysis: NodeAnalysisResponse? = null,
    val reportResult: ReportEnvelope? = null,
    val isLoading: Boolean = false,
    val isSubmitting: Boolean = false,
    val message: String? = null,
    val error: String? = null,
)

class MainViewModel(
    private val repository: AcuiferoRepository,
) : ViewModel() {
    private val _dashboard = MutableStateFlow(DashboardState(isLoading = true))
    val dashboard: StateFlow<DashboardState> = _dashboard.asStateFlow()

    private val _siteState = MutableStateFlow(SiteScreenState())
    val siteState: StateFlow<SiteScreenState> = _siteState.asStateFlow()

    private val _serverUrl = MutableStateFlow(repository.currentBaseUrl())
    val serverUrl: StateFlow<String> = _serverUrl.asStateFlow()

    val pendingReports = repository.observePendingReports()
        .stateIn(viewModelScope, SharingStarted.WhileSubscribed(5_000), emptyList())

    init {
        refreshDashboard()
    }

    fun refreshDashboard() {
        viewModelScope.launch {
            _dashboard.value = _dashboard.value.copy(isLoading = true, error = null)
            runCatching { repository.fetchDashboard() }
                .onSuccess { (runtime, sites, alerts) ->
                    _dashboard.value = DashboardState(
                        runtime = runtime,
                        sites = sites,
                        alerts = alerts,
                        isLoading = false,
                    )
                }
                .onFailure { error ->
                    _dashboard.value = _dashboard.value.copy(isLoading = false, error = error.message)
                }
        }
    }

    fun loadSite(siteId: String) {
        viewModelScope.launch {
            _siteState.value = SiteScreenState(isLoading = true)
            runCatching {
                Triple(
                    repository.fetchSite(siteId),
                    repository.fetchCalibration(siteId),
                    repository.fetchSnapshot(siteId),
                )
            }.onSuccess { (site, calibration, snapshot) ->
                _siteState.value = SiteScreenState(
                    site = site,
                    calibration = calibration,
                    snapshot = snapshot,
                    isLoading = false,
                )
            }.onFailure { error ->
                _siteState.value = SiteScreenState(isLoading = false, error = error.message)
            }
        }
    }

    fun refreshSnapshot(siteId: String) {
        viewModelScope.launch {
            _siteState.value = _siteState.value.copy(isLoading = true, error = null)
            runCatching { repository.refreshSnapshot(siteId) }
                .onSuccess { snapshot -> _siteState.value = _siteState.value.copy(snapshot = snapshot, isLoading = false) }
                .onFailure { error -> _siteState.value = _siteState.value.copy(isLoading = false, error = error.message) }
        }
    }

    fun analyzeSample(siteId: String) {
        viewModelScope.launch {
            _siteState.value = _siteState.value.copy(isLoading = true, error = null)
            runCatching { repository.analyzeSample(siteId) }
                .onSuccess { result -> _siteState.value = _siteState.value.copy(analysis = result, isLoading = false) }
                .onFailure { error -> _siteState.value = _siteState.value.copy(isLoading = false, error = error.message) }
        }
    }

    fun submitReport(siteId: String, reporterName: String, reporterRole: String, transcriptText: String, forceOffline: Boolean) {
        viewModelScope.launch {
            _siteState.value = _siteState.value.copy(isSubmitting = true, message = null, error = null)
            runCatching {
                repository.submitOrQueueReport(siteId, reporterName, reporterRole, transcriptText, forceOffline)
            }.onSuccess { envelope ->
                _siteState.value = _siteState.value.copy(
                    isSubmitting = false,
                    reportResult = envelope,
                    message = if (envelope == null) "Reporte guardado offline." else "Reporte enviado al backend.",
                )
                refreshDashboard()
            }.onFailure { error ->
                _siteState.value = _siteState.value.copy(isSubmitting = false, error = error.message)
            }
        }
    }

    fun saveCalibration(siteId: String, payload: CalibrationPayload, onDone: () -> Unit) {
        viewModelScope.launch {
            _siteState.value = _siteState.value.copy(isSubmitting = true, message = null, error = null)
            runCatching { repository.saveCalibration(siteId, payload) }
                .onSuccess { calibration ->
                    _siteState.value = _siteState.value.copy(
                        calibration = calibration,
                        isSubmitting = false,
                        message = "Calibracion guardada.",
                    )
                    onDone()
                }
                .onFailure { error -> _siteState.value = _siteState.value.copy(isSubmitting = false, error = error.message) }
        }
    }

    fun flushPendingReports() {
        viewModelScope.launch {
            _dashboard.value = _dashboard.value.copy(isLoading = true, error = null)
            runCatching { repository.flushPendingReports() }
                .onSuccess {
                    _siteState.value = _siteState.value.copy(message = "Cola sincronizada.")
                    refreshDashboard()
                }
                .onFailure { error ->
                    _dashboard.value = _dashboard.value.copy(isLoading = false, error = error.message)
                }
        }
    }

    fun updateServerUrl(url: String) {
        repository.updateBaseUrl(url)
        _serverUrl.value = repository.currentBaseUrl()
        refreshDashboard()
    }

    fun setBackendConnectivity(isOnline: Boolean) {
        viewModelScope.launch {
            runCatching { repository.setConnectivity(isOnline) }
                .onSuccess { refreshDashboard() }
                .onFailure { _dashboard.value = _dashboard.value.copy(error = it.message) }
        }
    }
}

class MainViewModelFactory(context: Context) : ViewModelProvider.Factory {
    private val repository = AcuiferoRepository.get(context)

    override fun <T : ViewModel> create(modelClass: Class<T>): T {
        return MainViewModel(repository) as T
    }
}
