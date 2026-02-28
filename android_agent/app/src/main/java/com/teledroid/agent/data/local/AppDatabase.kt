package com.teledroid.agent.data.local

import android.content.Context
import androidx.room.*

/**
 * قاعدة البيانات المحلية
 * تخزن بيانات الأجهزة والأوامر محلياً
 */
@Database(
    entities = [DeviceEntity::class, CommandEntity::class],
    version = 1,
    exportSchema = false
)
abstract class AppDatabase : RoomDatabase() {

    abstract fun deviceDao(): DeviceDao
    abstract fun commandDao(): CommandDao

    companion object {
        @Volatile
        private var instance: AppDatabase? = null

        fun getInstance(context: Context): AppDatabase {
            return instance ?: synchronized(this) {
                instance ?: buildDatabase(context).also { instance = it }
            }
        }

        private fun buildDatabase(context: Context): AppDatabase {
            return Room.databaseBuilder(
                context.applicationContext,
                AppDatabase::class.java,
                "teledroid_agent.db"
            )
                .fallbackToDestructiveMigration()
                .build()
        }
    }
}

/**
 * جدول الأجهزة
 */
@Entity(tableName = "devices")
data class DeviceEntity(
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
 * جدول الأوامر
 */
@Entity(tableName = "commands")
data class CommandEntity(
    @PrimaryKey(autoGenerate = true)
    val id: Int = 0,
    val commandType: String,
    val action: String,
    val parameters: String? = null,
    val status: String = "pending",
    val result: String? = null,
    val errorMessage: String? = null,
    val createdAt: Long = System.currentTimeMillis(),
    val completedAt: Long? = null
)

/**
 * DAO للأجهزة
 */
@Dao
interface DeviceDao {
    @Query("SELECT * FROM devices WHERE deviceId = :deviceId")
    suspend fun getDevice(deviceId: String): DeviceEntity?

    @Query("SELECT * FROM devices")
    suspend fun getAllDevices(): List<DeviceEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertDevice(device: DeviceEntity)

    @Delete
    suspend fun deleteDevice(device: DeviceEntity)

    @Query("DELETE FROM devices")
    suspend fun deleteAllDevices()
}

/**
 * DAO للأوامر
 */
@Dao
interface CommandDao {
    @Query("SELECT * FROM commands WHERE status = 'pending' ORDER BY createdAt DESC")
    suspend fun getPendingCommands(): List<CommandEntity>

    @Query("SELECT * FROM commands WHERE id = :id")
    suspend fun getCommand(id: Int): CommandEntity?

    @Query("SELECT * FROM commands ORDER BY createdAt DESC LIMIT :limit")
    suspend fun getRecentCommands(limit: Int): List<CommandEntity>

    @Insert(onConflict = OnConflictStrategy.REPLACE)
    suspend fun insertCommand(command: CommandEntity)

    @Update
    suspend fun updateCommand(command: CommandEntity)

    @Delete
    suspend fun deleteCommand(command: CommandEntity)

    @Query("DELETE FROM commands WHERE status = 'completed' AND createdAt < :timestamp")
    suspend fun deleteOldCompletedCommands(timestamp: Long)
}
