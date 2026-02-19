# Android Oculus Prime App — Roadmap & Architecture

> **Last updated**: Feb 17, 2026 14:45 UTC

> **Date**: February 17, 2026  
> **Status**: Planning Baseline  
> **Scope**: Android Edge Client for Oculus Prime — IoT interoperability test case

---

## 1. Mission

Costruire un'applicazione Android di riferimento per il modulo Oculus Prime che dimostri la capacità di Vitruvyan di integrarsi con fonti esterne (IoT, sensori mobili, acquisizione multimediale) tramite architettura client-server offline-first.

Obiettivo primario: usare Android come **test harness remoto** per inviare diversi tipi di artifact verso Vitruvyan e verificare end-to-end la robustezza della pipeline.

Questo test serve a validare in anticipo che, spostando in futuro Oculus Prime (o moduli analoghi) su device remoti (IoT, mini-PC, VPS, smartphone), il sistema centrale sia in grado di acquisire, persistire e processare correttamente i flussi esterni.

---

## 2. Analisi Architettura Esistente

L'architettura attuale è **già progettata per questo scenario** ed è composta da:

### 2.1 Oculus Prime Edge Gateway (`services/api_edge_oculus_prime/`)

**Caratteristiche**:
- **Gateway unico edge**: endpoint media-specifici esposti direttamente dal servizio Oculus Prime
- **Upload multipart**: file + metadata + correlation ID
- **Pipeline visibility**: endpoint operativi per health, pipeline status, eventi recenti
- **Transport contract**: upload diretto verso endpoint `/api/oculus-prime/{type}`

**Componenti chiave**:
```python
# services/api_edge_oculus_prime/api/routes.py
@router.post("/api/oculus-prime/image")
async def ingest_image(
    file: UploadFile = File(...),
    sampling_policy_ref: str | None = Form(None),
    correlation_id: str | None = Form(None),
):
    ...
```

**Operational endpoints**:
- `GET /health` — health servizio + connettività DB
- `GET /api/oculus-prime/pipeline` — stato pipeline ingestione
- `GET /api/oculus-prime/events` — eventi recenti Oculus Prime

### 2.2 Core Oculus Prime API (`services/api_edge_oculus_prime/`)

**Caratteristiche**:
- **7 media types**: document, image, audio, video, CAD, landscape, geo
- **Agents specializzati**: in `infrastructure/edge/oculus_prime/core/agents/`
- **Evidence Packs**: immutabili, append-only PostgreSQL
- **Event emission**: Redis Streams (`oculus_prime.evidence.created`)
- **Pre-epistemic**: NO NER, NO embeddings (upstream processing)

**Endpoint pattern**:
- `POST /api/oculus-prime/document`
- `POST /api/oculus-prime/image`
- `POST /api/oculus-prime/audio`
- `POST /api/oculus-prime/video`
- `POST /api/oculus-prime/cad`
- `POST /api/oculus-prime/landscape`
- `POST /api/oculus-prime/geo`

### 2.3 Infrastructure Layer (`infrastructure/edge/oculus_prime/core/`)

**Compliance**: 94% ACCORDO-FONDATIVO-INTAKE-V1.1

**Componenti**:
- **Guardrails**: validazione payload, integrity hash (SHA-256)
- **Event emitter**: idempotency keys, retry logic, audit log
- **Schema SQL**: append-only, consumer groups compliance
- **Agents**: document, image, audio, video, CAD, landscape, geo intake

**Event flow**:
```
External Source → Upload → Agent Processing → Evidence Pack (PostgreSQL)
                                            ↓
                              Redis Streams (oculus_prime.evidence.created)
                                            ↓
                    Sacred Orders (Codex → Pattern Weavers → Memory Orders)
```

---

## 3. Proposta Architettura Android App

### 3.1 Modello Client-Server Ibrido

```
┌─────────────────────────────────────────────────────────────────┐
│  ANDROID APP (Edge Client)                                      │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  UI Layer (Jetpack Compose)                               │  │
│  │  - Camera capture, audio record, GPS tracking             │  │
│  │  - Gallery upload, document picker                        │  │
│  │  - Real-time preview + status sync                        │  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                         │
│  ┌─────────────────────▼─────────────────────────────────────┐  │
│  │  Vitruvyan Android SDK (Kotlin)                           │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  OculusPrimeClient                                  │  │  │
│  │  │  - Multipart request builder                         │  │  │
│  │  │  - Media type detection + validation                │  │  │
│  │  │  - Correlation ID tracking                          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  LocalOutboxManager (SQLite Android)                │  │  │
│  │  │  - Queue pending uploads (offline buffering)        │  │  │
│  │  │  - Retry policy (exponential backoff)               │  │  │
│  │  │  - Status tracking (pending/sent/failed)            │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  │  ┌─────────────────────────────────────────────────────┐  │  │
│  │  │  TransportLayer (Retrofit/OkHttp)                   │  │  │
│  │  │  - HTTP multipart upload                            │  │  │
│  │  │  - Bearer token auth (CORE_EDGE_API_TOKEN)          │  │  │
│  │  │  - Connection health check                          │  │  │
│  │  └─────────────────────────────────────────────────────┘  │  │
│  └────────────────────────────────────────────────────────────┘  │
└───────────────────────┬─────────────────────────────────────────┘
                        │ POST /api/oculus-prime/{type}
                        │ (HTTP multipart + metadata)
                        ▼
┌─────────────────────────────────────────────────────────────────┐
│  VITRUVYAN CORE (Server)                                         │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │  Oculus Prime API (services/api_edge_oculus_prime)       │  │
│  │  - Media-specific agent processing                       │  │
│  │  - PostgreSQL Evidence Pack persistence                  │  │
│  │  - Redis Streams emission (oculus_prime.evidence.created)│  │
│  └─────────────────────┬─────────────────────────────────────┘  │
│                        │                                         │
│  ┌─────────────────────▼─────────────────────────────────────┐  │
│  │  Sacred Orders Processing                                │  │
│  │  Codex → Pattern Weavers → Memory Orders → Vault Keepers │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **UI** | Jetpack Compose (Material 3) | Modern declarative UI, type-safe |
| **Networking** | Retrofit + OkHttp | Industry standard, coroutines support |
| **Database** | Room (SQLite wrapper) | Type-safe DAO, migration support |
| **Async** | Kotlin Coroutines | Structured concurrency, cancellation |
| **Background Sync** | WorkManager | Guaranteed execution, battery-aware |
| **Camera** | CameraX | Modern camera API, multi-device support |
| **Location** | FusedLocationProviderClient | Battery-efficient GPS |
| **DI** | Hilt (Dagger) | Android-optimized dependency injection |

---

## 4. Implementazione Tecnica

### 4.1 Android SDK Core (`vitruvyan-android-sdk/`)

#### Modulo 1: `sdk-core/` (networking + contracts)

```kotlin
/**
 * Main client for Oculus Prime API interaction.
 * Handles HTTP multipart upload with Bearer token authentication.
 */
class OculusPrimeClient(
    private val baseUrl: String,
    private val apiToken: String?,
    private val timeout: Duration = 30.seconds
) {
    private val retrofit: Retrofit by lazy {
        Retrofit.Builder()
            .baseUrl(baseUrl)
            .client(buildOkHttpClient())
            .addConverterFactory(GsonConverterFactory.create())
            .build()
    }
    
    private val api: OculusPrimeApi by lazy {
        retrofit.create(OculusPrimeApi::class.java)
    }
    
    /**
     * Upload image file with metadata.
     * Calls POST /api/oculus-prime/image.
     */
    suspend fun uploadImage(
        file: File,
        metadata: Map<String, String> = emptyMap(),
        correlationId: String? = null
    ): Result<UploadResponse> = withContext(Dispatchers.IO) {
        try {
            val envelope = buildEnvelope(
                sourceType = SourceType.IMAGE,
                file = file,
                metadata = metadata,
                correlationId = correlationId
            )
            val response = api.uploadImage(envelope)
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    suspend fun uploadDocument(file: File, ...): Result<UploadResponse>
    suspend fun uploadAudio(file: File, ...): Result<UploadResponse>
    suspend fun uploadVideo(file: File, ...): Result<UploadResponse>
    suspend fun uploadGeo(file: File, ...): Result<UploadResponse>
    
    /**
     * Check Oculus Prime health status.
     */
    suspend fun checkHealth(): Result<HealthStatus> = withContext(Dispatchers.IO) {
        try {
            val response = api.getHealth()
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    /**
     * Get Oculus Prime pipeline status.
     */
    suspend fun getPipelineStatus(): Result<PipelineStatus> = withContext(Dispatchers.IO) {
        try {
            val response = api.getPipelineStatus()
            Result.success(response)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }
    
    private fun buildOkHttpClient(): OkHttpClient {
        return OkHttpClient.Builder()
            .connectTimeout(timeout)
            .readTimeout(timeout)
            .writeTimeout(timeout)
            .addInterceptor { chain ->
                val request = chain.request().newBuilder()
                apiToken?.let { token ->
                    request.addHeader("Authorization", "Bearer $token")
                }
                chain.proceed(request.build())
            }
            .build()
    }
}

/**
 * Generic upload envelope used by the Android SDK before multipart serialization.
 */
data class OculusPrimeUploadEnvelope(
    val source_type: SourceType,
    val source_uri: String,
    val metadata: Map<String, Any>,
    val correlation_id: String?,
    val created_utc: String
)

enum class SourceType {
    DOCUMENT,
    IMAGE,
    AUDIO,
    VIDEO,
    CAD,
    LANDSCAPE,
    GEO;
    
    override fun toString(): String = name.lowercase()
}

data class UploadResponse(
    val status: String,
    val message: String,
    val evidence_ids: List<String>
)

data class HealthStatus(
    val service: String,
    val version: String,
    val status: String,
    val timestamp: String,
    val postgresql: String
)

data class PipelineStatus(
    val total_events: Int,
    val ingestion_rate: Double,
    val recent_errors: Int
)
```

#### Modulo 2: `sdk-offline/` (SQLite outbox + sync)

```kotlin
/**
 * Manages local outbox for offline-first upload queue.
 * SQLite-backed with Room ORM.
 */
class LocalOutboxManager(
    private val database: OutboxDatabase
) {
    private val dao = database.outboxDao()
    
    /**
     * Enqueue upload for later transmission.
     * Returns outbox ID for tracking.
     */
    suspend fun enqueue(
        envelope: OculusPrimeUploadEnvelope,
        filePath: String
    ): Long = withContext(Dispatchers.IO) {
        val upload = PendingUpload(
            envelopeJson = Gson().toJson(envelope),
            localFilePath = filePath,
            status = UploadStatus.PENDING,
            attempts = 0,
            createdAt = System.currentTimeMillis(),
            lastAttemptAt = null,
            errorMessage = null
        )
        dao.insert(upload)
    }
    
    /**
     * Get all pending uploads for sync.
     */
    suspend fun getPendingUploads(): List<PendingUpload> = withContext(Dispatchers.IO) {
        dao.getPendingUploads()
    }
    
    /**
     * Synchronize pending uploads with exponential backoff retry.
     * Reports progress via callback.
     */
    suspend fun syncPending(
        client: OculusPrimeClient,
        onProgress: (current: Int, total: Int) -> Unit
    ): SyncResult = withContext(Dispatchers.IO) {
        val pending = getPendingUploads()
        var sent = 0
        var failed = 0
        
        pending.forEachIndexed { index, upload ->
            onProgress(index + 1, pending.size)
            
            val file = File(upload.localFilePath)
            if (!file.exists()) {
                markFailed(upload.id, "File not found")
                failed++
                return@forEachIndexed
            }
            
            val envelope = Gson().fromJson(upload.envelopeJson, OculusPrimeUploadEnvelope::class.java)
            val result = when (envelope.source_type) {
                SourceType.IMAGE -> client.uploadImage(file, envelope.metadata, envelope.correlation_id)
                SourceType.DOCUMENT -> client.uploadDocument(file, envelope.metadata, envelope.correlation_id)
                SourceType.AUDIO -> client.uploadAudio(file, envelope.metadata, envelope.correlation_id)
                SourceType.VIDEO -> client.uploadVideo(file, envelope.metadata, envelope.correlation_id)
                SourceType.GEO -> client.uploadGeo(file, envelope.metadata, envelope.correlation_id)
                else -> Result.failure(Exception("Unsupported source type"))
            }
            
            result.fold(
                onSuccess = {
                    markSent(upload.id)
                    sent++
                },
                onFailure = { error ->
                    markFailed(upload.id, error.message ?: "Unknown error")
                    failed++
                }
            )
        }
        
        SyncResult(total = pending.size, sent = sent, failed = failed)
    }
    
    /**
     * Mark upload as successfully sent.
     */
    suspend fun markSent(outboxId: Long) = withContext(Dispatchers.IO) {
        dao.updateStatus(outboxId, UploadStatus.SENT)
    }
    
    /**
     * Mark upload as failed with error message.
     */
    suspend fun markFailed(outboxId: Long, reason: String) = withContext(Dispatchers.IO) {
        dao.incrementAttempts(outboxId)
        dao.updateError(outboxId, reason)
        dao.updateStatus(outboxId, UploadStatus.FAILED)
    }
    
    /**
     * Delete uploaded files to free storage.
     */
    suspend fun cleanupSent() = withContext(Dispatchers.IO) {
        dao.deleteSent()
    }
}

@Entity(tableName = "outbox_uploads")
data class PendingUpload(
    @PrimaryKey(autoGenerate = true) val id: Long = 0,
    val envelopeJson: String,
    val localFilePath: String,
    val status: UploadStatus,
    val attempts: Int,
    val createdAt: Long,
    val lastAttemptAt: Long?,
    val errorMessage: String?
)

enum class UploadStatus {
    PENDING,
    SENT,
    FAILED
}

data class SyncResult(
    val total: Int,
    val sent: Int,
    val failed: Int
)
```

#### Modulo 3: `sdk-sensors/` (IoT acquisition helpers)

```kotlin
/**
 * Helper for camera photo/video capture.
 */
class CameraIntakeHelper(
    private val context: Context,
    private val lifecycleOwner: LifecycleOwner
) {
    private var imageCapture: ImageCapture? = null
    private var videoCapture: VideoCapture<Recorder>? = null
    
    /**
     * Capture photo and save to file.
     */
    fun capturePhoto(
        outputFile: File,
        onCaptured: (File) -> Unit,
        onError: (Exception) -> Unit
    ) {
        val outputOptions = ImageCapture.OutputFileOptions.Builder(outputFile).build()
        
        imageCapture?.takePicture(
            outputOptions,
            ContextCompat.getMainExecutor(context),
            object : ImageCapture.OnImageSavedCallback {
                override fun onImageSaved(output: ImageCapture.OutputFileResults) {
                    onCaptured(outputFile)
                }
                
                override fun onError(exception: ImageCaptureException) {
                    onError(exception)
                }
            }
        )
    }
    
    /**
     * Start video recording.
     */
    fun startVideoRecording(
        outputFile: File,
        onStopped: (File) -> Unit
    ): Recording?
    
    /**
     * Stop ongoing video recording.
     */
    fun stopVideoRecording()
}

/**
 * Audio recorder wrapper.
 */
class AudioRecorder(private val context: Context) {
    private var recorder: MediaRecorder? = null
    
    fun startRecording(outputFile: File) {
        recorder = MediaRecorder().apply {
            setAudioSource(MediaRecorder.AudioSource.MIC)
            setOutputFormat(MediaRecorder.OutputFormat.AAC_ADTS)
            setAudioEncoder(MediaRecorder.AudioEncoder.AAC)
            setOutputFile(outputFile.absolutePath)
            prepare()
            start()
        }
    }
    
    fun stopRecording(): File {
        recorder?.apply {
            stop()
            release()
        }
        recorder = null
        return File("...") // Return output file
    }
}

/**
 * GPS location tracker.
 */
class GeoLocationTracker(private val context: Context) {
    private val fusedLocationClient: FusedLocationProviderClient =
        LocationServices.getFusedLocationProviderClient(context)
    
    /**
     * Get current location (single request).
     */
    suspend fun getCurrentLocation(): Location? = suspendCoroutine { continuation ->
        if (ActivityCompat.checkSelfPermission(
                context,
                Manifest.permission.ACCESS_FINE_LOCATION
            ) != PackageManager.PERMISSION_GRANTED
        ) {
            continuation.resume(null)
            return@suspendCoroutine
        }
        
        fusedLocationClient.lastLocation.addOnSuccessListener { location ->
            continuation.resume(location)
        }.addOnFailureListener {
            continuation.resume(null)
        }
    }
    
    /**
     * Start periodic location tracking.
     */
    fun startTracking(
        intervalMs: Long,
        onUpdate: (Location) -> Unit
    ): LocationCallback {
        val locationRequest = LocationRequest.create().apply {
            interval = intervalMs
            fastestInterval = intervalMs / 2
            priority = LocationRequest.PRIORITY_HIGH_ACCURACY
        }
        
        val callback = object : LocationCallback() {
            override fun onLocationResult(result: LocationResult) {
                result.lastLocation?.let(onUpdate)
            }
        }
        
        // Request location updates
        fusedLocationClient.requestLocationUpdates(locationRequest, callback, null)
        
        return callback
    }
    
    fun stopTracking(callback: LocationCallback) {
        fusedLocationClient.removeLocationUpdates(callback)
    }
}
```

### 4.2 Reference Android App (`examples/android/oculus-prime-demo/`)

#### Features Principali

| Feature | Description | Implementation |
|---------|-------------|----------------|
| **Camera Capture** | Take photo → upload with GPS metadata | CameraX + Location API |
| **Video Recording** | Record video → chunked upload | CameraX video mode |
| **Audio Recording** | Record audio → upload with timestamp | MediaRecorder wrapper |
| **Document Picker** | Select PDF/DOCX → upload | Intent.ACTION_OPEN_DOCUMENT |
| **Gallery Upload** | Batch upload images | Intent.ACTION_GET_CONTENT (multiple) |
| **Offline Mode** | Queue uploads → auto-sync on reconnect | Room + WorkManager |
| **Real-time Status** | Pending count, sync progress | StateFlow + Compose |
| **IoT Simulation** | Periodic GPS tracking + auto-upload | WorkManager periodic task |

#### App Architecture (MVVM + Clean Architecture)

```
app/
├── data/
│   ├── repository/
│   │   ├── OculusPrimeRepository.kt     # Coordinates SDK + local storage
│   │   └── LocationRepository.kt
│   ├── local/
│   │   └── OutboxDatabase.kt            # Room database
│   └── remote/
│       └── VitruvyanSdkProvider.kt      # SDK singleton
├── domain/
│   ├── model/
│   │   ├── MediaItem.kt
│   │   └── UploadStatus.kt
│   └── usecase/
│       ├── CapturePhotoUseCase.kt
│       ├── UploadMediaUseCase.kt
│       └── SyncPendingUploadsUseCase.kt
├── presentation/
│   ├── home/
│   │   ├── HomeScreen.kt                # Main dashboard UI
│   │   └── HomeViewModel.kt
│   ├── camera/
│   │   ├── CameraScreen.kt
│   │   └── CameraViewModel.kt
│   ├── upload/
│   │   ├── UploadScreen.kt
│   │   └── UploadViewModel.kt
│   └── navigation/
│       └── NavGraph.kt
└── workers/
    ├── SyncWorker.kt                     # Background sync with WorkManager
    └── LocationTrackingWorker.kt
```

---

## 5. Considerazioni Sicurezza

### 5.1 Device Identity

```kotlin
/**
 * Manages device identity and payload signing.
 */
class DeviceIdentityManager(private val context: Context) {
    private val prefs = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * Get or generate persistent device UUID.
     */
    fun getDeviceId(): String {
        var deviceId = prefs.getString(KEY_DEVICE_ID, null)
        if (deviceId == null) {
            deviceId = UUID.randomUUID().toString()
            prefs.edit().putString(KEY_DEVICE_ID, deviceId).apply()
        }
        return deviceId
    }
    
    /**
     * Generate device fingerprint (hash of device characteristics).
     */
    fun getDeviceFingerprint(): String {
        val components = listOf(
            Build.MODEL,
            Build.MANUFACTURER,
            Build.BRAND,
            Build.DEVICE,
            Build.VERSION.SDK_INT.toString()
        )
        val combined = components.joinToString("-")
        return hashSHA256(combined)
    }
    
    /**
     * Sign payload with HMAC-SHA256 using device secret.
     */
    fun signPayload(payload: String, timestamp: Long): String {
        val secret = getOrCreateDeviceSecret()
        val message = "$payload:$timestamp"
        return hmacSHA256(message, secret)
    }
    
    private fun getOrCreateDeviceSecret(): String {
        var secret = prefs.getString(KEY_DEVICE_SECRET, null)
        if (secret == null) {
            secret = generateSecureRandom(32)
            prefs.edit().putString(KEY_DEVICE_SECRET, secret).apply()
        }
        return secret
    }
    
    companion object {
        private const val PREFS_NAME = "vitruvyan_device_identity"
        private const val KEY_DEVICE_ID = "device_id"
        private const val KEY_DEVICE_SECRET = "device_secret"
    }
}
```

### 5.2 Secure Token Storage

```kotlin
/**
 * Manages API token using EncryptedSharedPreferences.
 */
class SecureTokenManager(context: Context) {
    private val encryptedPrefs = EncryptedSharedPreferences.create(
        context,
        "vitruvyan_secure_prefs",
        MasterKey.Builder(context)
            .setKeyScheme(MasterKey.KeyScheme.AES256_GCM)
            .build(),
        EncryptedSharedPreferences.PrefKeyEncryptionScheme.AES256_SIV,
        EncryptedSharedPreferences.PrefValueEncryptionScheme.AES256_GCM
    )
    
    fun saveToken(token: String) {
        encryptedPrefs.edit().putString(KEY_API_TOKEN, token).apply()
    }
    
    fun getToken(): String? {
        return encryptedPrefs.getString(KEY_API_TOKEN, null)
    }
    
    fun clearToken() {
        encryptedPrefs.edit().remove(KEY_API_TOKEN).apply()
    }
    
    companion object {
        private const val KEY_API_TOKEN = "api_token"
    }
}
```

### 5.3 Security Checklist

| Security Feature | Implementation | Priority |
|------------------|----------------|----------|
| **Bearer Token Auth** | `Authorization: Bearer <token>` header | ✅ MVP |
| **Token Encryption** | EncryptedSharedPreferences (AES256-GCM) | ✅ MVP |
| **Device Identity** | Persistent UUID + fingerprint | ✅ MVP |
| **Payload Signing** | HMAC-SHA256 with device secret | 🔶 Phase 2 |
| **Anti-Replay** | Nonce + timestamp window validation | 🔶 Phase 2 |
| **mTLS** | Client certificate authentication | 🔶 Production |
| **Certificate Pinning** | Prevent MITM attacks | 🔶 Production |
| **Root Detection** | Block execution on rooted devices | 🔵 Optional |

---

## 6. Struttura Repository Proposta

```
vitruvyan-core/
├── vitruvyan_core/                       # Existing core
├── services/                             # Existing services
│   └── api_edge_oculus_prime/            # ✅ Already exists
├── infrastructure/
│   └── edge/
│       └── oculus_prime/
│           ├── core/                     # ✅ Already exists
│           └── android/                  # ← NEW: Android-specific edge client
│               ├── vitruvyan-sdk/        # Android SDK Kotlin modules
│               │   ├── sdk-core/
│               │   │   ├── build.gradle.kts
│               │   │   └── src/
│               │   │       └── main/kotlin/com/vitruvyan/sdk/
│               │   │           ├── OculusPrimeClient.kt
│               │   │           ├── models/
│               │   │           └── api/
│               │   ├── sdk-offline/
│               │   │   ├── build.gradle.kts
│               │   │   └── src/
│               │   │       └── main/kotlin/com/vitruvyan/sdk/offline/
│               │   │           ├── LocalOutboxManager.kt
│               │   │           ├── database/
│               │   │           └── models/
│               │   ├── sdk-sensors/
│               │   │   ├── build.gradle.kts
│               │   │   └── src/
│               │   │       └── main/kotlin/com/vitruvyan/sdk/sensors/
│               │   │           ├── CameraIntakeHelper.kt
│               │   │           ├── AudioRecorder.kt
│               │   │           └── GeoLocationTracker.kt
│               │   ├── build.gradle.kts  # Root SDK build file
│               │   ├── settings.gradle.kts
│               │   └── README.md
│               └── examples/
│                   └── oculus-prime-demo/  # Reference Android app
│                       ├── app/
│                       │   ├── build.gradle.kts
│                       │   └── src/
│                       │       └── main/
│                       │           ├── kotlin/com/vitruvyan/demo/
│                       │           │   ├── MainActivity.kt
│                       │           │   ├── data/
│                       │           │   ├── domain/
│                       │           │   ├── presentation/
│                       │           │   └── workers/
│                       │           ├── res/
│                       │           └── AndroidManifest.xml
│                       ├── gradle/
│                       ├── build.gradle.kts
│                       ├── settings.gradle.kts
│                       └── README.md
├── docs/
│   └── planning/
│       └── ANDROID_OCULUS_PRIME_APP_ROADMAP_FEB17_2026.md  # ← This file
```

---

## 7. Implementation Roadmap

### Sprint 1: SDK Foundation (Week 1 — Feb 17-23, 2026)

**Goals**:
- ✅ Setup Android SDK multi-module Gradle project
- ✅ Implement `OculusPrimeClient` with Retrofit
- ✅ Implement `LocalOutboxManager` with Room
- ✅ Unit tests for SDK core (JUnit + MockK)

**Deliverables**:
1. `vitruvyan-sdk/sdk-core` module (networking + contracts)
2. `vitruvyan-sdk/sdk-offline` module (outbox + sync)
3. Unit test coverage ≥ 80%
4. SDK README with integration guide

**Acceptance Criteria**:
- Upload image via `OculusPrimeClient.uploadImage()` succeeds in integration test
- Offline enqueue + sync completes without errors
- Oculus Prime API accepts uploaded media and returns evidence IDs

### Sprint 2: Android Demo App (Week 2 — Feb 24 - Mar 2, 2026)

**Goals**:
- ✅ Setup Jetpack Compose UI project
- ✅ Integrate CameraX for photo capture
- ✅ Implement upload flow (online/offline)
- ✅ Dashboard with upload status

**Deliverables**:
1. `oculus-prime-demo` app with Jetpack Compose UI
2. Camera capture screen
3. Upload queue screen (pending/sent/failed list)
4. Dashboard with metrics (pending count, sync progress)

**Acceptance Criteria**:
- Capture photo → auto-upload in online mode
- Capture photo → enqueue in offline mode → sync on reconnect
- UI shows real-time upload status

### Sprint 3: IoT Sensors Integration (Week 3 — Mar 3-9, 2026)

**Goals**:
- ✅ Implement GPS tracking
- ✅ Auto-upload with location metadata
- ✅ Background WorkManager sync
- ✅ Upload completion notifications

**Deliverables**:
1. `sdk-sensors` module (camera, audio, GPS helpers)
2. Periodic GPS tracking worker
3. Background sync worker
4. Android notifications for upload completion

**Acceptance Criteria**:
- GPS coordinates embedded in image metadata
- Background sync runs every 15 minutes (configurable)
- User receives notification on successful upload

### Sprint 4: Security Hardening (Week 4 — Mar 10-16, 2026)

**Goals**:
- ✅ Device identity + fingerprinting
- ✅ Token encryption (EncryptedSharedPreferences)
- ✅ Payload signing (HMAC-SHA256)
- ✅ mTLS setup (optional for production)

**Deliverables**:
1. `DeviceIdentityManager` implementation
2. `SecureTokenManager` with AES256-GCM encryption
3. Payload signing integration
4. Security audit report

**Acceptance Criteria**:
- API token encrypted at rest
- Device ID persists across app restarts
- HMAC signature validated server-side (if implemented)

### Sprint 5: End-to-End Validation (Week 5 — Mar 17-23, 2026)

**Goals**:
- ✅ End-to-end test from Android to Sacred Orders
- ✅ Performance benchmarking (upload latency, battery usage)
- ✅ Documentation + deployment guide

**Deliverables**:
1. E2E test suite (Android → Oculus Prime → Redis Streams)
2. Performance benchmark report
3. Final user documentation
4. Video demo

**Acceptance Criteria**:
- Uploaded image appears in Qdrant vector store (downstream processing)
- Upload latency < 5 seconds (WiFi) / < 10 seconds (4G)
- Battery drain < 5% per hour (background tracking)

---

## 8. Vantaggi Architettura Proposta

| Aspetto | Beneficio | Dettagli |
|---------|-----------|----------|
| **Gateway unico** | Minore complessità architetturale | SDK integra direttamente Oculus Prime |
| **Offline-first nativo** | SQLite locale + sync automatico | Funziona senza connessione, sincronizzazione trasparente |
| **SDK generico** | Riutilizzabile per iOS/Flutter/React Native | Pattern adattabile a qualsiasi mobile platform |
| **Event-driven** | Allineato a Sacred Orders processing | Eventi Redis Streams → pipeline epistemic standard |
| **Scalabile IoT** | Pattern testato per M2M (MQTT futuro) | Architettura pronta per fleet management, sensori industriali |
| **Security-first** | Device identity + mTLS ready | Sicurezza baked-in, non patchwork |
| **Battery-efficient** | WorkManager + FusedLocation | Android-native ottimizzazioni batteria |
| **Type-safe** | Kotlin + Compose | Crash-resistant, compile-time checks |

---

## 9. Acceptance Criteria

### 9.1 Functional Requirements

1. ✅ **Upload media files** (image, audio, video, document) da Android device
2. ✅ **Offline buffering** con queue persistente (SQLite)
3. ✅ **Auto-sync** quando connessione torna disponibile
4. ✅ **GPS metadata** automatica per foto/video
5. ✅ **Background sync** non blocca UI, battery-aware
6. ✅ **Real-time status** (pending uploads, sync progress, errors)
7. ✅ **Token authentication** sicura (Bearer token + encryption)

### 9.2 Non-Functional Requirements

| Requirement | Target | Measurement |
|-------------|--------|-------------|
| **Upload latency** | < 5 sec (WiFi), < 10 sec (4G) | Time to HTTP 200 response |
| **Battery usage** | < 5% drain/hour (background tracking) | Battery Historian profiling |
| **Offline capacity** | ≥ 100 uploads queued | SQLite row count |
| **Sync reliability** | ≥ 99% success (excludes network failure) | Sent / (Sent + Failed) ratio |
| **Crash rate** | < 0.1% sessions | Firebase Crashlytics |
| **App size** | < 20 MB APK | APK Analyzer |

### 9.3 Integration Requirements

1. ✅ **Compatibility** con Oculus Prime API multipart contract
2. ✅ **Evidence Pack** creati downstream in PostgreSQL
3. ✅ **Redis Streams** events emessi (`oculus_prime.evidence.created`)
4. ✅ **Sacred Orders** processing attivato (Codex → Memory → Vault)
5. ✅ **Qdrant embeddings** disponibili post-processing
6. ✅ **Remote pipeline validation**: test superato con artifact inviati da device remoto verso core Vitruvyan

---

## 10. Risks and Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| **Android API fragmentation** | Medium | Medium | Min SDK 26 (Android 8+), CameraX backport |
| **Battery drain** | High | Medium | WorkManager constraints, FusedLocation |
| **Network instability** | Medium | High | Offline-first design, retry with backoff |
| **Storage overflow** | Medium | Low | Auto-cleanup sent uploads, configurable retention |
| **Security breach** | High | Low | Token encryption, mTLS optional, payload signing |
| **SDK maintenance burden** | Medium | Medium | Clear versioning, semantic release, CI/CD |

---

## 11. Success Metrics

### 11.1 Technical Metrics

- **Code coverage**: ≥ 80% (unit + integration tests)
- **Build time**: < 2 minutes (clean build)
- **APK size**: < 20 MB
- **Method count**: < 64K (no MultiDex needed)

### 11.2 Product Metrics

- **Upload success rate**: ≥ 99% (excludes network failures)
- **Offline queue capacity**: ≥ 100 uploads
- **Background sync efficiency**: ≥ 95% uploads synced within 1 hour
- **User-perceived latency**: < 5 seconds (WiFi)

### 11.3 Ecosystem Metrics

- **Cross-platform reusability**: SDK pattern adaptable to iOS/Flutter
- **Downstream processing**: Evidence Packs reach Qdrant within 30 seconds
- **Event emission**: Redis Streams events consumed by Sacred Orders

---

## 12. Next Actions (Immediate Sprint Planning)

### Week 1 (Feb 17-23, 2026) — SDK Foundation

**Day 1-2**:
- [ ] Create `infrastructure/edge/oculus_prime/android/vitruvyan-sdk/` structure
- [ ] Setup Gradle multi-module build (`sdk-core`, `sdk-offline`, `sdk-sensors`)
- [ ] Define Kotlin package structure (`com.vitruvyan.sdk.*`)

**Day 3-4**:
- [ ] Implement `OculusPrimeClient` with Retrofit
- [ ] Implement media request data classes (`ImageUploadRequest`, `DocumentUploadRequest`, ...)
- [ ] Add Bearer token authentication interceptor

**Day 5**:
- [ ] Implement `LocalOutboxManager` with Room
- [ ] Write unit tests (JUnit + MockK)
- [ ] SDK README with integration examples

### Week 2 (Feb 24 - Mar 2, 2026) — Android Demo App

**Day 1-2**:
- [ ] Create `oculus-prime-demo` Android project (Jetpack Compose)
- [ ] Setup Hilt dependency injection
- [ ] Implement `HomeScreen` dashboard UI

**Day 3-4**:
- [ ] Integrate CameraX for photo capture
- [ ] Implement `CameraScreen` + `CameraViewModel`
- [ ] Wire upload flow (capture → enqueue → upload)

**Day 5**:
- [ ] Implement upload queue screen (pending/sent/failed)
- [ ] Add real-time status updates (StateFlow)
- [ ] Integration test: capture → upload → verify server-side

---

## 13. References

- **Oculus Prime API**: `services/api_edge_oculus_prime/README.md`
- **Infrastructure Core**: `infrastructure/edge/oculus_prime/core/README.md`
- **Intake + Edge Plan**: `docs/planning/INTAKE_EDGE_REFACTOR_INTEGRATION_PLAN_FEB16_2026.md`
- **Jetpack Compose**: https://developer.android.com/jetpack/compose
- **CameraX**: https://developer.android.com/training/camerax
- **WorkManager**: https://developer.android.com/topic/libraries/architecture/workmanager
- **Retrofit**: https://square.github.io/retrofit/
- **Room**: https://developer.android.com/training/data-storage/room

---

## Appendix A: API Contract Examples

### A.1 Upload Image Request (Android → Oculus Prime)

```http
POST /api/oculus-prime/image HTTP/1.1
Host: vitruvyan.example.com:9050
Authorization: Bearer eyJhbGc...
Content-Type: multipart/form-data; boundary=----boundary123

------boundary123
Content-Disposition: form-data; name="file"; filename="photo_123.jpg"
Content-Type: image/jpeg

[binary image data]
------boundary123
Content-Disposition: form-data; name="metadata"

{"latitude": 45.464, "longitude": 9.188, "device_id": "uuid-xyz"}
------boundary123
Content-Disposition: form-data; name="correlation_id"

android-session-abc123
------boundary123--
```

### A.2 Upload Response

```json
{
  "status": "success",
  "message": "Image processed successfully. Created 1 Evidence Packs.",
  "evidence_ids": ["EVD-123"]
}
```

### A.3 Health Check Response

```json
{
  "service": "vitruvyan_oculus_prime_api",
  "version": "1.0.0",
  "status": "healthy",
  "timestamp": "2026-02-17T14:30:00Z",
  "postgresql": "connected"
}
```

---

## Appendix B: Kotlin Code Snippets

### B.1 Usage Example (Android App)

```kotlin
class UploadViewModel @Inject constructor(
    private val oculusPrimeClient: OculusPrimeClient,
    private val outboxManager: LocalOutboxManager
) : ViewModel() {
    
    fun uploadPhoto(photoFile: File, location: Location?) {
        viewModelScope.launch {
            val metadata = buildMap {
                location?.let {
                    put("latitude", it.latitude.toString())
                    put("longitude", it.longitude.toString())
                }
                put("timestamp", System.currentTimeMillis().toString())
                put("device_id", DeviceIdentityManager.getDeviceId())
            }
            
            val result = oculusPrimeClient.uploadImage(
                file = photoFile,
                metadata = metadata,
                correlationId = "android-session-${UUID.randomUUID()}"
            )
            
            result.fold(
                onSuccess = { response ->
                    Log.i(TAG, "Upload success: ${response.envelope_id}")
                    _uploadStatus.value = UploadStatus.Success(response.envelope_id)
                },
                onFailure = { error ->
                    Log.e(TAG, "Upload failed: ${error.message}")
                    // Enqueue for offline retry
                    outboxManager.enqueue(buildEnvelope(...), photoFile.path)
                    _uploadStatus.value = UploadStatus.Queued
                }
            )
        }
    }
}
```

### B.2 Background Sync Worker

```kotlin
class SyncWorker(
    context: Context,
    params: WorkerParameters
) : CoroutineWorker(context, params) {
    
    override suspend fun doWork(): Result {
        val client = OculusPrimeClient(...)
        val outbox = LocalOutboxManager(...)
        
        val syncResult = outbox.syncPending(client) { current, total ->
            setProgress(workDataOf("current" to current, "total" to total))
        }
        
        return if (syncResult.failed == 0) {
            Result.success()
        } else {
            Result.retry()
        }
    }
}

// Schedule periodic sync
WorkManager.getInstance(context).enqueueUniquePeriodicWork(
    "oculus_prime_sync",
    ExistingPeriodicWorkPolicy.KEEP,
    PeriodicWorkRequestBuilder<SyncWorker>(15, TimeUnit.MINUTES)
        .setConstraints(
            Constraints.Builder()
                .setRequiredNetworkType(NetworkType.CONNECTED)
                .build()
        )
        .build()
)
```

---

**End of Document**
