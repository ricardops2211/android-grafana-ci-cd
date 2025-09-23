package com.example.app

import android.content.Intent
import androidx.test.ext.junit.runners.AndroidJUnit4
import androidx.test.platform.app.InstrumentationRegistry
import androidx.test.core.app.ActivityScenario
import org.junit.Test
import org.junit.runner.RunWith
import org.junit.Assert.assertTrue

@RunWith(AndroidJUnit4::class)
class LoginTest {

    @Test
    fun ok() {
        val targetPkg = InstrumentationRegistry.getInstrumentation().targetContext.packageName
        val intent = Intent(Intent.ACTION_MAIN).apply {
            setClassName(targetPkg, LoginActivity::class.java.name)
            addCategory(Intent.CATEGORY_LAUNCHER)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        ActivityScenario.launch<LoginActivity>(intent).use {
            // Aquí tus aserciones reales. Por ahora, una de ejemplo:
            assertTrue(true)
        }
    }

    @Test
    fun fail() {
        val targetPkg = InstrumentationRegistry.getInstrumentation().targetContext.packageName
        val intent = Intent(Intent.ACTION_MAIN).apply {
            setClassName(targetPkg, LoginActivity::class.java.name)
            addCategory(Intent.CATEGORY_LAUNCHER)
            addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        }
        ActivityScenario.launch<LoginActivity>(intent).use {
            // Un ejemplo de “fallo” controlado: comentar o ajustar según tu caso
            assertTrue("Fallo intencional", false)
        }
    }
}
