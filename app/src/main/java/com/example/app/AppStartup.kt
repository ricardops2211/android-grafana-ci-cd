package com.example.app

import android.app.Application
import android.util.Log

class AppStartup : Application() {
  override fun onCreate() {
    super.onCreate()
    Log.i("AppStartup", "App in DEBUG? ${BuildConfig.DEBUG}")
  }
}
