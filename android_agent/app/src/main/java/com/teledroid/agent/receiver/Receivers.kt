package com.teledroid.agent.receiver

import android.content.BroadcastReceiver
import android.content.Context
import android.content.Intent
import android.util.Log
import com.teledroid.agent.service.AgentService

/**
 * مستلم الإقلاع
 * يبدأ الخدمة تلقائياً عند إقلاع الجهاز
 */
class BootReceiver : BroadcastReceiver() {

    private val tag = "BootReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == Intent.ACTION_BOOT_COMPLETED) {
            Log.d(tag, "Device booted, starting Agent service")

            val serviceIntent = Intent(context, AgentService::class.java)
            context.startForegroundService(serviceIntent)
        }
    }
}

/**
 * مستلم تغيير الشبكة
 * يتعامل مع تغييرات حالة الشبكة
 */
class NetworkReceiver : BroadcastReceiver() {

    private val tag = "NetworkReceiver"

    override fun onReceive(context: Context, intent: Intent) {
        if (intent.action == android.net.conn.CONNECTIVITY_CHANGE) {
            val isConnected = intent.getBooleanExtra(android.net.ConnectivityManager.EXTRA_NO_CONNECTIVITY, false)

            Log.d(tag, "Network changed, connected: $isConnected")

            if (!isConnected) {
                // الشبكة متصلة - يمكن إرسال البيانات
                Log.d(tag, "Network available")
            } else {
                // الشبكة غير متصلة
                Log.d(tag, "Network unavailable")
            }
        }
    }
}
