package com.teledroid.agent

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import com.teledroid.agent.data.local.AppDatabase
import com.teledroid.agent.data.remote.ApiService
import com.teledroid.agent.data.repository.DeviceRepository
import com.teledroid.agent.data.repository.CommandRepository

/**
 * فئة التطبيق الرئيسية
 * تقوم بتهيئة المكونات الأساسية عند بدء التطبيق
 */
class TeleDroidApp : Application() {

    // المكونات الأساسية
    lateinit var apiService: ApiService
        private set

    lateinit var database: AppDatabase
        private set

    lateinit var deviceRepository: DeviceRepository
        private set

    lateinit var commandRepository: CommandRepository
        private set

    override fun onCreate() {
        super.onCreate()
        instance = this

        // تهيئة المكونات
        initializeComponents()

        // إنشاء قناة الإشعارات
        createNotificationChannel()
    }

    private fun initializeComponents() {
        // تهيئة خدمة API
        apiService = ApiService(this)

        // تهيئة قاعدة البيانات المحلية
        database = AppDatabase.getInstance(this)

        // تهيئة المستودعات
        deviceRepository = DeviceRepository(database.deviceDao(), apiService)
        commandRepository = CommandRepository(database.commandDao(), apiService)
    }

    private fun createNotificationChannel() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "TeleDroid Agent",
                NotificationManager.IMPORTANCE_LOW
            ).apply {
                description = "خدمة التحكم في الهاتف"
                setShowBadge(false)
            }

            val notificationManager = getSystemService(NotificationManager::class.java)
            notificationManager.createNotificationChannel(channel)
        }
    }

    companion object {
        const val CHANNEL_ID = "teledroid_agent_channel"

        @Volatile
        private var instance: TeleDroidApp? = null

        fun getInstance(): TeleDroidApp {
            return instance ?: throw IllegalStateException("Application not initialized")
        }
    }
}
