package com.example.app

import android.os.Bundle
import android.util.Log
import androidx.appcompat.app.AppCompatActivity
import com.example.app.BuildConfig as AppBuildConfig 

class MainActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_main)
    Log.i("MainActivity", "isDebug=${AppBuildConfig.DEBUG}")
  }
}
