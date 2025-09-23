package com.example.app

import android.os.Bundle
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    val tv = TextView(this)
    tv.text = if (BuildConfig.DEBUG) "Hello (debug)" else "Hello"
    setContentView(tv)
  }
}
