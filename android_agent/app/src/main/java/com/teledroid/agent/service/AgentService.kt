package com.teledroid.agent.service

import android.app.Notification
import android.app.PendingIntent
import android.app.Service
import android.content.Intent
import android.os.IBinder
import android.util.Log
import androidx.core.app.NotificationCompat
import com.teledroid.agent.R
import com.teledroid.agent.TeleDroidApp
import com.teledroid.agent.data.model.Command
import com.teledroid.agent.executor.CommandExecutor
import com.teledroid.agent.ui.MainActivity
import kotlinx.coroutines.*

/**
 * خدمة الخلفية للتعامل مع الأوامر
 * تعمل في الخلفية وتتصل بالخادم للحصول على الأوامر وتنفيذها
 */
class AgentService : Service() {

    private val tag = "AgentService"
    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())

    private lateinit var commandExecutor: CommandExecutor
    private var pollingJob: Job? = null
    private var deviceId: String? = null

    companion object {
        private const val NOTIFICATION_ID = 1001
        private const val POLLING_INTERVAL = 5000L // 5 ثوانٍ

        const val ACTION_START = "com.teledroid.agent.START"
        const val ACTION_STOP = "com.teledroid.agent.STOP"
    }

    override fun onCreate() {
        super.onCreate()
        Log.d(tag, "Service created")

        commandExecutor = CommandExecutor(this)
        deviceId = getDeviceId()
    }

    override fun onStartCommand(intent: Intent?, flags: Int, startId: Int): Int {
        Log.d(tag, "Service started")

        when (intent?.action) {
            ACTION_STOP -> {
                stopPolling()
                stopForeground(STOP_FOREGROUND_REMOVE)
                stopSelf()
                return START_NOT_STICKY
            }
        }

        // بدء الإشعار
        startForeground(NOTIFICATION_ID, createNotification())

        // بدء استطلاع الأوامر
        startPolling()

        return START_STICKY
    }

    override fun onBind(intent: Intent?): IBinder? = null

    override fun onDestroy() {
        super.onDestroy()
        Log.d(tag, "Service destroyed")
        stopPolling()
        scope.cancel()
    }

    private fun startPolling() {
        if (pollingJob?.isActive == true) return

        pollingJob = scope.launch {
            while (isActive) {
                try {
                    pollAndExecuteCommands()
                    sendHeartbeat()
                } catch (e: Exception) {
                    Log.e(tag, "Error in polling", e)
                }

                delay(POLLING_INTERVAL)
            }
        }
    }

    private fun stopPolling() {
        pollingJob?.cancel()
        pollingJob = null
    }

    private suspend fun pollAndExecuteCommands() {
        val currentDeviceId = deviceId ?: return
        val app = TeleDroidApp.getInstance()

        // الحصول على الأوامر المعلقة
        val result = app.apiService.getPendingCommands(currentDeviceId)

        result.onSuccess { commands ->
            for (command in commands) {
                executeCommand(command)
            }
        }
    }

    private suspend fun executeCommand(command: Command) {
        Log.d(tag, "Executing command: ${command.id} - ${command.action}")

        // تنفيذ الأمر
        val result = commandExecutor.executeCommand(command)

        // إرسال النتيجة للخادم
        val app = TeleDroidApp.getInstance()
        app.apiService.submitCommandResult(
            commandId = command.id,
            status = if (result.success) "completed" else "failed",
            result = if (result.success) mapOf("data" to result.result) else null,
            errorMessage = result.error
        )

        Log.d(tag, "Command ${command.id} completed: ${result.success}")
    }

    private suspend fun sendHeartbeat() {
        val currentDeviceId = deviceId ?: return

        try {
            val app = TeleDroidApp.getInstance()
            app.apiService.sendHeartbeat(currentDeviceId)

            // إرسال إحصائيات الجهاز كل دقيقة
            val stats = commandExecutor.getDeviceStats()
            app.apiService.sendDeviceStats(currentDeviceId, stats)
        } catch (e: Exception) {
            Log.e(tag, "Error sending heartbeat", e)
        }
    }

    private fun createNotification(): Notification {
        val intent = Intent(this, MainActivity::class.java)
        val pendingIntent = PendingIntent.getActivity(
            this,
            0,
            intent,
            PendingIntent.FLAG_IMMUTABLE
        )

        val stopIntent = Intent(this, AgentService::class.java).apply {
            action = ACTION_STOP
        }
        val stopPendingIntent = PendingIntent.getService(
            this,
            1,
            stopIntent,
            PendingIntent.FLAG_IMMUTABLE
        )

        return NotificationCompat.Builder(this, TeleDroidApp.CHANNEL_ID)
            .setContentTitle("TeleDroid Agent")
            .setContentText("جاري التشغيل...")
            .setSmallIcon(android.R.drawable.ic_menu_compass)
            .setContentIntent(pendingIntent)
            .addAction(android.R.drawable.ic_menu_close_clear_cancel, "إيقاف", stopPendingIntent)
            .setOngoing(true)
            .build()
    }

    private fun getDeviceId(): String {
        return android.provider.Settings.Secure.getString(
            contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )
    }
}
