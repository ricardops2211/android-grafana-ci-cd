package com.example.app
import com.example.app.BuildConfig
import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)

    // Ejemplo de “métrica” en logcat para Promtail/Loki:
    // tu test instrumentado puede medir el startup real y loguearlo así:
    Log.i("METRIC_JSON", """{"metric":"app_startup_ms","value":1234}""")
  }
}
