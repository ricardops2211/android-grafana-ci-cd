package com.example.app

import android.app.Application
import android.util.Log
import com.example.app.BuildConfig as AppBuildConfig  // evita conflictos de nombre

class AppStartup : Application() {
  override fun onCreate() {
    super.onCreate()
    Log.i("AppStartup", "App started. debug=${AppBuildConfig.DEBUG}")
  }
}
