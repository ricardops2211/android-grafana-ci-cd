package com.example.app

import android.app.Application
import com.example.app.BuildConfig
import android.util.Log
import com.example.app.BuildConfig

class AppStartup : Application() {
  override fun onCreate() {
    super.onCreate()
    Log.i("AppStartup", "App started. debug=${BuildConfig.DEBUG}")
  }
}
