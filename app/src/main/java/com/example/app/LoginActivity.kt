package com.example.app

import android.os.Bundle
import com.example.app.BuildConfig
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.example.app.BuildConfig

class LoginActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)

    Log.i("LoginActivity", "Build type debug? ${BuildConfig.DEBUG}")
  }
}
