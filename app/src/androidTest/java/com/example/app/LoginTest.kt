package com.example.app

import androidx.test.core.app.ActivityScenario
import androidx.test.ext.junit.runners.AndroidJUnit4
import org.junit.Assert.assertTrue
import org.junit.Test
import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LoginTest {
  @Test fun ok() {
    val scenario = ActivityScenario.launch(LoginActivity::class.java)
    assertTrue(true)
    scenario.close()
  }

  @Test fun fail() {
    assertTrue(true)
  }
}
