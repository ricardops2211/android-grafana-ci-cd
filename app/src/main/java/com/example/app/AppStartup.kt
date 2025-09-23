package com.example.app

import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.example.app.BuildConfig as AppBuildConfig 

class AppStartup : Application() {
  override fun onCreate() {
    super.onCreate()
    Log.i("AppStartup", "App started. debug=${BuildConfig.DEBUG}")
  }
}
