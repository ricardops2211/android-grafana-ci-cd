package com.example.app

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class LoginActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    // UI mínima sin layout XML
    val tv = TextView(this).apply { text = "LoginActivity (DEBUG=${BuildConfig.DEBUG})" }
    setContentView(tv)
  }
}
