package com.teledroid.agent.data.model

import androidx.room.Entity
import androidx.room.PrimaryKey

/**
 * نموذج الجهاز
 */
@Entity(tableName = "devices")
data class Device(
    @PrimaryKey
    val deviceId: String,
    val deviceName: String? = null,
    val deviceModel: String? = null,
    val androidVersion: String? = null,
    val telegramId: Long? = null,
    val isOnline: Boolean = false,
    val lastSeen: Long = System.currentTimeMillis()
)

/**
 * نموذج الأمر
 */
@Entity(tableName = "commands")
data class Command(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val commandType: String,
    val action: String,
    val parameters: String? = null,
    val status: String = "pending", // pending, processing, completed, failed
    val result: String? = null,
    val errorMessage: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val completedAt: Long? = null
)

/**
 * نموذج إحصائيات الجهاز
 */
@Entity(tableName = "device_stats")
data class DeviceStats(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val deviceId: String,
    val batteryLevel: Int = 0,
    val batteryStatus: String = "Unknown",
    val storageTotal: Float = 0f,
    val storageUsed: Float = 0f,
    val networkType: String = "Unknown",
    val networkSpeed: Float = 0f,
    val memoryUsed: Float = 0f,
    val memoryTotal: Float = 0f,
    val cpuUsage: Float = 0f,
    val timestamp: Long = System.currentTimeMillis()
)

/**
 * استجابة ربط الجهاز
 */
data class DeviceLinkResponse(
    val success: Boolean,
    val message: String,
    val deviceToken: String? = null
)

/**
 * نموذج المهمة المجدولة
 */
data class ScheduledTask(
    val id: Int,
    val name: String,
    val commandType: String,
    val action: String,
    val parameters: String? = null,
    val scheduleType: String, // once, hourly, daily, weekly
    val scheduleValue: String? = null,
    val isActive: Boolean = true,
    val lastRun: Long? = null,
    val nextRun: Long? = null
)
