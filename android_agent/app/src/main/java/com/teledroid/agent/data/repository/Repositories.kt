package com.teledroid.agent.data.repository

import com.teledroid.agent.data.local.CommandDao
import com.teledroid.agent.data.local.DeviceDao
import com.teledroid.agent.data.local.DeviceEntity
import com.teledroid.agent.data.local.CommandEntity
import com.teledroid.agent.data.model.Device
import com.teledroid.agent.data.model.Command
import com.teledroid.agent.data.model.DeviceLinkResponse
import com.teledroid.agent.data.remote.ApiService

/**
 * مستودع الأجهزة
 * يتعامل مع عمليات الأجهزة بين قاعدة البيانات والخادم
 */
class DeviceRepository(
    private val deviceDao: DeviceDao,
    private val apiService: ApiService
) {
    /**
     * ربط جهاز جديد
     */
    suspend fun linkDevice(device: Device): Result<DeviceLinkResponse> {
        // حفظ محلياً أولاً
        deviceDao.insertDevice(
            DeviceEntity(
                deviceId = device.deviceId,
                deviceName = device.deviceName,
                deviceModel = device.deviceModel,
                androidVersion = device.androidVersion,
                telegramId = device.telegramId,
                isOnline = true
            )
        )

        // إرسال للخادم
        return apiService.linkDevice(device)
    }

    /**
     * الحصول على معلومات الجهاز
     */
    suspend fun getDevice(deviceId: String): Device? {
        val entity = deviceDao.getDevice(deviceId) ?: return null
        return Device(
            deviceId = entity.deviceId,
            deviceName = entity.deviceName,
            deviceModel = entity.deviceModel,
            androidVersion = entity.androidVersion,
            telegramId = entity.telegramId,
            isOnline = entity.isOnline,
            lastSeen = entity.lastSeen
        )
    }

    /**
     * تحديث حالة الاتصال
     */
    suspend fun updateOnlineStatus(deviceId: String, isOnline: Boolean) {
        val device = deviceDao.getDevice(deviceId) ?: return
        deviceDao.insertDevice(device.copy(isOnline = isOnline, lastSeen = System.currentTimeMillis()))
    }

    /**
     * إلغاء ربط الجهاز
     */
    suspend fun unlinkDevice(deviceId: String) {
        deviceDao.deleteDevice(DeviceEntity(deviceId = deviceId))
    }
}

/**
 * مستودع الأوامر
 * يتعامل مع عمليات الأوامر بين قاعدة البيانات والخادم
 */
class CommandRepository(
    private val commandDao: CommandDao,
    private val apiService: ApiService
) {
    /**
     * الحصول على الأوامر المعلقة
     */
    suspend fun getPendingCommands(): List<Command> {
        return commandDao.getPendingCommands().map { it.toCommand() }
    }

    /**
     * حفظ أمر محلياً
     */
    suspend fun saveCommand(command: Command): Long {
        return commandDao.insertCommand(command.toEntity()).toLong()
    }

    /**
     * تحديث حالة الأمر
     */
    suspend fun updateCommandStatus(commandId: Int, status: String, result: String? = null, error: String? = null) {
        val command = commandDao.getCommand(commandId) ?: return
        commandDao.updateCommand(
            command.copy(
                status = status,
                result = result,
                errorMessage = error,
                completedAt = if (status == "completed" || status == "failed") System.currentTimeMillis() else null
            )
        )
    }

    /**
     * الحصول على الأوامر الأخيرة
     */
    suspend fun getRecentCommands(limit: Int = 50): List<Command> {
        return commandDao.getRecentCommands(limit).map { it.toCommand() }
    }

    /**
     * حذف الأوامر المنتهية القديمة
     */
    suspend fun cleanupOldCommands(daysToKeep: Int = 7) {
        val cutoffTime = System.currentTimeMillis() - (daysToKeep * 24 * 60 * 60 * 1000L)
        commandDao.deleteOldCompletedCommands(cutoffTime)
    }

    // دوال التحويل
    private fun CommandEntity.toCommand() = Command(
        id = id,
        commandType = commandType,
        action = action,
        parameters = parameters,
        status = status,
        result = result,
        errorMessage = errorMessage,
        createdAt = createdAt,
        completedAt = completedAt
    )

    private fun Command.toEntity() = CommandEntity(
        id = id,
        commandType = commandType,
        action = action,
        parameters = parameters,
        status = status,
        result = result,
        errorMessage = errorMessage,
        createdAt = createdAt,
        completedAt = completedAt
    )

    private fun DeviceEntity.toDevice() = Device(
        deviceId = deviceId,
        deviceName = deviceName,
        deviceModel = deviceModel,
        androidVersion = androidVersion,
        telegramId = telegramId,
        isOnline = isOnline,
        lastSeen = lastSeen
    )

    private fun Device.toEntity() = DeviceEntity(
        deviceId = deviceId,
        deviceName = deviceName,
        deviceModel = deviceModel,
        androidVersion = androidVersion,
        telegramId = telegramId,
        isOnline = isOnline,
        lastSeen = lastSeen
    )
}
