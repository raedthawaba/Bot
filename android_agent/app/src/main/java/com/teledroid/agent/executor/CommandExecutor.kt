package com.teledroid.agent.executor

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.net.ConnectivityManager
import android.net.NetworkCapabilities
import android.net.wifi.WifiManager
import android.os.BatteryManager
import android.os.Environment
import android.os.StatFs
import android.util.Log
import com.teledroid.agent.data.model.Command
import com.teledroid.agent.data.model.DeviceStats
import org.json.JSONObject
import java.io.File

/**
 * محرك تنفيذ الأوامر
 * يتلقى الأوامر من الخادم وينفذها على الجهاز
 */
class CommandExecutor(private val context: Context) {

    private val tag = "CommandExecutor"

    /**
     * تنفيذ الأمر
     */
    suspend fun executeCommand(command: Command): CommandResult {
        Log.d(tag, "Executing command: ${command.action}")

        return try {
            when (command.action) {
                // أوامر النظام
                "device_status" -> executeDeviceStatus()
                "battery_info" -> executeBatteryInfo()
                "storage_info" -> executeStorageInfo()
                "network_info" -> executeNetworkInfo()
                "system_info" -> executeSystemInfo()

                // أوامر الملفات
                "list_files" -> executeListFiles(command.parameters)
                "create_folder" -> executeCreateFolder(command.parameters)
                "delete_file" -> executeDeleteFile(command.parameters)
                "upload_file" -> executeUploadFile(command.parameters)
                "download_file" -> executeDownloadFile(command.parameters)

                // أوامر التطبيقات
                "open_app" -> executeOpenApp(command.parameters)
                "close_app" -> executeCloseApp(command.parameters)
                "list_apps" -> executeListApps()

                else -> CommandResult(
                    success = false,
                    error = "Unknown command: ${command.action}"
                )
            }
        } catch (e: Exception) {
            Log.e(tag, "Error executing command", e)
            CommandResult(
                success = false,
                error = e.message ?: "Unknown error"
            )
        }
    }

    // ==================== أوامر النظام ====================

    private fun executeDeviceStatus(): CommandResult {
        val batteryInfo = getBatteryInfo()
        val storageInfo = getStorageInfo()
        val networkInfo = getNetworkInfo()

        val result = JSONObject().apply {
            put("battery", JSONObject(batteryInfo))
            put("storage", JSONObject(storageInfo))
            put("network", JSONObject(networkInfo))
            put("timestamp", System.currentTimeMillis())
        }

        return CommandResult(success = true, result = result.toString())
    }

    private fun executeBatteryInfo(): CommandResult {
        val info = getBatteryInfo()
        return CommandResult(success = true, result = JSONObject(info).toString())
    }

    private fun executeStorageInfo(): CommandResult {
        val info = getStorageInfo()
        return CommandResult(success = true, result = JSONObject(info).toString())
    }

    private fun executeNetworkInfo(): CommandResult {
        val info = getNetworkInfo()
        return CommandResult(success = true, result = JSONObject(info).toString())
    }

    private fun executeSystemInfo(): CommandResult {
        val info = mapOf(
            "device" to android.os.Build.MODEL,
            "manufacturer" to android.os.Build.MANUFACTURER,
            "android_version" to android.os.Build.VERSION.RELEASE,
            "sdk_version" to android.os.Build.VERSION.SDK_INT,
            "device_id" to android.provider.Settings.Secure.getString(
                context.contentResolver,
                android.provider.Settings.Secure.ANDROID_ID
            )
        )
        return CommandResult(success = true, result = JSONObject(info).toString())
    }

    // ==================== أوامر الملفات ====================

    private fun executeListFiles(parameters: String?): CommandResult {
        val path = extractParameter(parameters, "path") ?: Environment.getExternalStorageDirectory().absolutePath

        val directory = File(path)
        if (!directory.exists() || !directory.isDirectory) {
            return CommandResult(success = false, error = "Directory not found: $path")
        }

        val files = directory.listFiles()?.map { file ->
            mapOf(
                "name" to file.name,
                "path" to file.absolutePath,
                "size" to file.length(),
                "isDirectory" to file.isDirectory,
                "lastModified" to file.lastModified()
            )
        } ?: emptyList()

        val result = JSONObject().apply {
            put("path", path)
            put("files", files)
            put("count", files.size)
        }

        return CommandResult(success = true, result = result.toString())
    }

    private fun executeCreateFolder(parameters: String?): CommandResult {
        val folderName = extractParameter(parameters, "name")
            ?: return CommandResult(success = false, error = "Folder name required")

        val parentPath = extractParameter(parameters, "path")
            ?: Environment.getExternalStorageDirectory().absolutePath

        val folder = File(parentPath, folderName)

        return try {
            if (folder.mkdir()) {
                CommandResult(success = true, result = JSONObject().put("path", folder.absolutePath).toString())
            } else {
                CommandResult(success = false, error = "Failed to create folder")
            }
        } catch (e: Exception) {
            CommandResult(success = false, error = e.message)
        }
    }

    private fun executeDeleteFile(parameters: String?): CommandResult {
        val filePath = extractParameter(parameters, "path")
            ?: return CommandResult(success = false, error = "File path required")

        val file = File(filePath)

        return try {
            if (file.exists() && file.delete()) {
                CommandResult(success = true, result = JSONObject().put("deleted", filePath).toString())
            } else {
                CommandResult(success = false, error = "File not found or cannot be deleted")
            }
        } catch (e: Exception) {
            CommandResult(success = false, error = e.message)
        }
    }

    private fun executeUploadFile(parameters: String?): CommandResult {
        // يتم التعامل مع رفع الملفات في AgentService
        return CommandResult(success = true, result = "File upload initiated")
    }

    private fun executeDownloadFile(parameters: String?): CommandResult {
        // يتم التعامل مع تنزيل الملفات في AgentService
        return CommandResult(success = true, result = "File download initiated")
    }

    // ==================== أوامر التطبيقات ====================

    private fun executeOpenApp(parameters: String?): CommandResult {
        val packageName = extractParameter(parameters, "package")
            ?: return CommandResult(success = false, error = "Package name required")

        return try {
            val intent = context.packageManager.getLaunchIntentForPackage(packageName)
            if (intent != null) {
                intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
                context.startActivity(intent)
                CommandResult(success = true, result = "App opened: $packageName")
            } else {
                CommandResult(success = false, error = "App not found: $packageName")
            }
        } catch (e: Exception) {
            CommandResult(success = false, error = e.message)
        }
    }

    private fun executeCloseApp(parameters: String?): CommandResult {
        val packageName = extractParameter(parameters, "package")
            ?: return CommandResult(success = false, error = "Package name required")

        return try {
            val intent = Intent(Intent.ACTION_DELETE)
            intent.data = android.net.Uri.parse("package:$packageName")
            intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
            context.startActivity(intent)
            CommandResult(success = true, result = "Close app initiated: $packageName")
        } catch (e: Exception) {
            CommandResult(success = false, error = e.message)
        }
    }

    private fun executeListApps(): CommandResult {
        val packages = context.packageManager.getInstalledApplications(0)
            .filter { it.packageName != context.packageName }
            .map { appInfo ->
                mapOf(
                    "name" to appInfo.loadLabel(context.packageManager),
                    "package" to appInfo.packageName
                )
            }

        return CommandResult(
            success = true,
            result = JSONObject().put("apps", packages).toString()
        )
    }

    // ==================== دوال المساعدة ====================

    private fun extractParameter(parameters: String?, key: String): String? {
        if (parameters == null) return null
        return try {
            val json = JSONObject(parameters)
            json.optString(key)
        } catch (e: Exception) {
            null
        }
    }

    private fun getBatteryInfo(): Map<String, Any> {
        val batteryManager = context.getSystemService(Context.BATTERY_SERVICE) as BatteryManager
        val level = batteryManager.getIntProperty(BatteryManager.BATTERY_PROPERTY_CAPACITY)
        val status = getBatteryStatus()

        return mapOf(
            "level" to level,
            "status" to status,
            "charging" to (status == "Charging")
        )
    }

    private fun getBatteryStatus(): String {
        val intent = context.registerReceiver(null, android.content.IntentFilter(Intent.ACTION_BATTERY_CHANGED))
        val status = intent?.getIntExtra(BatteryManager.EXTRA_STATUS, -1) ?: -1

        return when (status) {
            BatteryManager.BATTERY_STATUS_CHARGING -> "Charging"
            BatteryManager.BATTERY_STATUS_DISCHARGING -> "Discharging"
            BatteryManager.BATTERY_STATUS_FULL -> "Full"
            BatteryManager.BATTERY_STATUS_NOT_CHARGING -> "Not Charging"
            else -> "Unknown"
        }
    }

    private fun getStorageInfo(): Map<String, Any> {
        val stat = StatFs(Environment.getExternalStorageDirectory().path)
        val total = stat.blockCountLong * stat.blockSizeLong
        val available = stat.availableBlocksLong * stat.blockSizeLong

        return mapOf(
            "total" to (total / (1024 * 1024 * 1024)).toFloat(),
            "used" to ((total - available) / (1024 * 1024 * 1024)).toFloat(),
            "available" to (available / (1024 * 1024 * 1024)).toFloat()
        )
    }

    private fun getNetworkInfo(): Map<String, Any> {
        val connectivityManager = context.getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        val network = connectivityManager.activeNetwork
        val capabilities = connectivityManager.getNetworkCapabilities(network)

        var type = "None"
        var speed = 0f

        if (capabilities != null) {
            type = when {
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_WIFI) -> "WiFi"
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_CELLULAR) -> "Cellular"
                capabilities.hasTransport(NetworkCapabilities.TRANSPORT_ETHERNET) -> "Ethernet"
                else -> "Unknown"
            }

            speed = capabilities.linkDownstreamBandwidthKbps.toFloat() / 1000
        }

        return mapOf(
            "type" to type,
            "speed" to speed,
            "connected" to (type != "None")
        )
    }

    fun getDeviceStats(): DeviceStats {
        val batteryInfo = getBatteryInfo()
        val storageInfo = getStorageInfo()
        val networkInfo = getNetworkInfo()

        val activityManager = context.getSystemService(Context.ACTIVITY_SERVICE) as ActivityManager
        val memInfo = ActivityManager.MemoryInfo()
        activityManager.getMemoryInfo(memInfo)

        return DeviceStats(
            deviceId = android.provider.Settings.Secure.getString(
                context.contentResolver,
                android.provider.Settings.Secure.ANDROID_ID
            ),
            batteryLevel = batteryInfo["level"] as Int,
            batteryStatus = batteryInfo["status"] as String,
            storageTotal = storageInfo["total"] as Float,
            storageUsed = storageInfo["used"] as Float,
            networkType = networkInfo["type"] as String,
            networkSpeed = networkInfo["speed"] as Float,
            memoryTotal = (memInfo.totalMem / (1024 * 1024 * 1024)).toFloat(),
            memoryUsed = ((memInfo.totalMem - memInfo.availMem) / (1024 * 1024 * 1024)).toFloat()
        )
    }
}

/**
 * نتيجة الأمر
 */
data class CommandResult(
    val success: Boolean,
    val result: String? = null,
    val error: String? = null
)
