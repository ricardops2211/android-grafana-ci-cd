package com.example.app
import android.app.Application
import android.os.SystemClock
import android.util.Log
import org.json.JSONObject

class AppStartup : Application() {
  private val start = SystemClock.uptimeMillis()
  override fun onCreate() {
    super.onCreate()
    val ms = SystemClock.uptimeMillis() - start
    val obj = JSONObject()
      .put("ts", System.currentTimeMillis())
      .put("metric", "app_startup_ms")
      .put("value", ms)
      .put("build", BuildConfig.VERSION_NAME)
      .put("commit", BuildConfig.GIT_SHA)
    Log.i("METRIC_JSON", obj.toString())
  }
}
