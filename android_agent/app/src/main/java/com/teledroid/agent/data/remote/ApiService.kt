package com.teledroid.agent.data.remote

import android.content.Context
import android.util.Log
import com.teledroid.agent.data.model.*
import kotlinx.coroutines.Dispatchers
import kotlinx.coroutines.withContext
import okhttp3.MediaType.Companion.toMediaType
import okhttp3.MultipartBody
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.RequestBody.Companion.asRequestBody
import okhttp3.RequestBody.Companion.toRequestBody
import org.json.JSONObject
import java.io.File
import java.util.concurrent.TimeUnit

/**
 * خدمة API للتواصل مع الخادم
 * تتعامل مع جميع طلبات HTTP للخادم الخلفي
 */
class ApiService(private val context: Context) {

    private val client = OkHttpClient.Builder()
        .connectTimeout(30, TimeUnit.SECONDS)
        .readTimeout(30, TimeUnit.SECONDS)
        .writeTimeout(30, TimeUnit.SECONDS)
        .build()

    // عنوان الخادم - يجب تغييره إلى عنوان الخادم الفعلي
    private var baseUrl = "http://10.0.2.2:8000" // localhost للـ emulator

    fun setBaseUrl(url: String) {
        baseUrl = url
    }

    /**
     * ربط الجهاز بالخادم
     */
    suspend fun linkDevice(device: Device): Result<DeviceLinkResponse> = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("device_id", device.deviceId)
                put("device_name", device.deviceName)
                put("device_model", device.deviceModel)
                put("android_version", device.androidVersion)
                put("telegram_id", device.telegramId)
            }

            val requestBody = json.toString()
                .toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url("$baseUrl/api/v1/devices/link")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                val body = response.body?.string()
                val jsonResponse = JSONObject(body ?: "{}")

                Result.success(DeviceLinkResponse(
                    success = jsonResponse.getBoolean("success"),
                    message = jsonResponse.getString("message"),
                    deviceToken = jsonResponse.optString("device_token")
                ))
            } else {
                Result.failure(Exception("HTTP ${response.code}: ${response.message}"))
            }
        } catch (e: Exception) {
            Log.e("ApiService", "Error linking device", e)
            Result.failure(e)
        }
    }

    /**
     * إرسال إشارة حياة للخادم
     */
    suspend fun sendHeartbeat(deviceId: String): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("$baseUrl/api/v1/devices/heartbeat?device_id=$deviceId")
                .post("".toRequestBody("application/json".toMediaType()))
                .build()

            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * الحصول على الأوامر المعلقة
     */
    suspend fun getPendingCommands(deviceId: String): Result<List<Command>> = withContext(Dispatchers.IO) {
        try {
            val request = Request.Builder()
                .url("$baseUrl/api/v1/commands/pending?device_id=$deviceId")
                .get()
                .build()

            val response = client.newCall(request).execute()

            if (response.isSuccessful) {
                val body = response.body?.string() ?: "[]"
                val commands = parseCommands(body)
                Result.success(commands)
            } else {
                Result.failure(Exception("HTTP ${response.code}"))
            }
        } catch (e: Exception) {
            Log.e("ApiService", "Error getting commands", e)
            Result.failure(e)
        }
    }

    /**
     * إرسال نتيجة الأمر
     */
    suspend fun submitCommandResult(
        commandId: Int,
        status: String,
        result: Map<String, Any>? = null,
        errorMessage: String? = null
    ): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("command_id", commandId)
                put("status", status)
                result?.let { put("result", JSONObject(it)) }
                errorMessage?.let { put("error_message", it) }
            }

            val requestBody = json.toString()
                .toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url("$baseUrl/api/v1/commands/result")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * رفع ملف إلى الخادم
     */
    suspend fun uploadFile(file: File, deviceId: String, path: String): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val requestBody = MultipartBody.Builder()
                .setType(MultipartBody.FORM)
                .addFormDataPart("file", file.name, file.asRequestBody("application/octet-stream".toMediaType()))
                .addFormDataPart("device_id", deviceId)
                .addFormDataPart("path", path)
                .build()

            val request = Request.Builder()
                .url("$baseUrl/api/v1/files/upload")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    /**
     * إرسال إحصائيات الجهاز
     */
    suspend fun sendDeviceStats(deviceId: String, stats: DeviceStats): Result<Boolean> = withContext(Dispatchers.IO) {
        try {
            val json = JSONObject().apply {
                put("device_id", deviceId)
                put("battery_level", stats.batteryLevel)
                put("battery_status", stats.batteryStatus)
                put("storage_total", stats.storageTotal)
                put("storage_used", stats.storageUsed)
                put("network_type", stats.networkType)
                put("network_speed", stats.networkSpeed)
            }

            val requestBody = json.toString()
                .toRequestBody("application/json".toMediaType())

            val request = Request.Builder()
                .url("$baseUrl/api/v1/device/stats")
                .post(requestBody)
                .build()

            val response = client.newCall(request).execute()
            Result.success(response.isSuccessful)
        } catch (e: Exception) {
            Result.failure(e)
        }
    }

    private fun parseCommands(json: String): List<Command> {
        // تحليل JSON للأوامر
        // هذا تبسيط، في الإنتاج يجب استخدام JSON library
        return try {
            val commands = mutableListOf<Command>()
            // ...
            commands
        } catch (e: Exception) {
            emptyList()
        }
    }
}
