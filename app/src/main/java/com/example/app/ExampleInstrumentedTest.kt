package com.example.app

import android.util.Log
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import org.junit.Assert.assertEquals
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class ExampleInstrumentedTest {
  @Test
  fun useAppContext() {
    val appContext = InstrumentationRegistry.getInstrumentation().targetContext
    assertEquals("com.example.app", appContext.packageName)

    // Simula una métrica: el test podría medir tiempos y reportarlos
    Log.i("METRIC_JSON", """{"metric":"app_startup_ms","value":987}""")
  }
}
