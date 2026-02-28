package com.teledroid.agent.ui

import android.content.Intent
import android.os.Build
import android.os.Bundle
import android.view.View
import android.widget.Toast
import androidx.appcompat.app.AppCompatActivity
import androidx.lifecycle.lifecycleScope
import com.teledroid.agent.TeleDroidApp
import com.teledroid.agent.data.model.Device
import com.teledroid.agent.databinding.ActivityMainBinding
import com.teledroid.agent.service.AgentService
import kotlinx.coroutines.launch

/**
 * النشاط الرئيسي لتطبيق Android Agent
 * واجهة المستخدم لربط الجهاز وإظهار الحالة
 */
class MainActivity : AppCompatActivity() {

    private lateinit var binding: ActivityMainBinding
    private val app by lazy { TeleDroidApp.getInstance() }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        binding = ActivityMainBinding.inflate(layoutInflater)
        setContentView(binding.root)

        setupUI()
        checkDeviceStatus()
    }

    private fun setupUI() {
        // إعداد معلومات الجهاز
        binding.deviceName.text = android.os.Build.MODEL
        binding.deviceId.text = getDeviceId()

        // زر الربط
        binding.linkButton.setOnClickListener {
            linkDevice()
        }

        // زر بدء الخدمة
        binding.startServiceButton.setOnClickListener {
            startAgentService()
        }

        // زر إيقاف الخدمة
        binding.stopServiceButton.setOnClickListener {
            stopAgentService()
        }

        // زر تحديث الحالة
        binding.refreshButton.setOnClickListener {
            checkDeviceStatus()
        }
    }

    private fun getDeviceId(): String {
        // إنشاء معرف فريد للجهاز
        return android.provider.Settings.Secure.getString(
            contentResolver,
            android.provider.Settings.Secure.ANDROID_ID
        )
    }

    private fun linkDevice() {
        val telegramId = binding.telegramIdInput.text.toString().toLongOrNull()

        if (telegramId == null) {
            Toast.makeText(this, "الرجاء إدخال معرف Telegram", Toast.LENGTH_SHORT).show()
            return
        }

        binding.progressBar.visibility = View.VISIBLE

        lifecycleScope.launch {
            try {
                val device = Device(
                    deviceId = getDeviceId(),
                    deviceName = android.os.Build.MODEL,
                    deviceModel = android.os.Build.MANUFACTURER + " " + android.os.Build.MODEL,
                    androidVersion = "Android ${Build.VERSION.RELEASE}",
                    telegramId = telegramId
                )

                val result = app.deviceRepository.linkDevice(device)

                if (result.isSuccess) {
                    Toast.makeText(this@MainActivity, "تم ربط الجهاز بنجاح!", Toast.LENGTH_SHORT).show()
                    checkDeviceStatus()
                } else {
                    Toast.makeText(this@MainActivity, "فشل الربط: ${result.exceptionOrNull()?.message}", Toast.LENGTH_SHORT).show()
                }
            } catch (e: Exception) {
                Toast.makeText(this@MainActivity, "خطأ: ${e.message}", Toast.LENGTH_SHORT).show()
            } finally {
                binding.progressBar.visibility = View.GONE
            }
        }
    }

    private fun checkDeviceStatus() {
        lifecycleScope.launch {
            val isServiceRunning = isAgentServiceRunning()

            if (isServiceRunning) {
                binding.statusIndicator.setImageResource(android.R.drawable.presence_online)
                binding.statusText.text = "متصل"
                binding.startServiceButton.isEnabled = false
                binding.stopServiceButton.isEnabled = true
            } else {
                binding.statusIndicator.setImageResource(android.R.drawable.presence_away)
                binding.statusText.text = "غير متصل"
                binding.startServiceButton.isEnabled = true
                binding.stopServiceButton.isEnabled = false
            }
        }
    }

    private fun startAgentService() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val intent = Intent(this, AgentService::class.java)
            startForegroundService(intent)
        } else {
            val intent = Intent(this, AgentService::class.java)
            startService(intent)
        }

        Toast.makeText(this, "تم بدء الخدمة", Toast.LENGTH_SHORT).show()
        checkDeviceStatus()
    }

    private fun stopAgentService() {
        val intent = Intent(this, AgentService::class.java)
        stopService(intent)

        Toast.makeText(this, "تم إيقاف الخدمة", Toast.LENGTH_SHORT).show()
        checkDeviceStatus()
    }

    private fun isAgentServiceRunning(): Boolean {
        val manager = getSystemService(ACTIVITY_SERVICE) as android.app.ActivityManager
        @Suppress("DEPRECATION")
        for (service in manager.getRunningServices(Integer.MAX_VALUE)) {
            if (AgentService::class.java.name == service.service.className) {
                return true
            }
        }
        return false
    }

    override fun onResume() {
        super.onResume()
        checkDeviceStatus()
    }
}
