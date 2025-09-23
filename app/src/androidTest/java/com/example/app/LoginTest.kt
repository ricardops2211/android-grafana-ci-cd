package com.example.app
import androidx.test.ext.junit.rules.ActivityScenarioRule
import androidx.test.ext.junit.runners.AndroidJUnit4
import com.example.app.BuildConfig
import androidx.test.espresso.Espresso.onView
import androidx.test.espresso.action.ViewActions.*
import androidx.test.espresso.assertion.ViewAssertions.matches
import androidx.test.espresso.matcher.ViewMatchers.*
import org.junit.Rule; import org.junit.Test; import org.junit.runner.RunWith

@RunWith(AndroidJUnit4::class)
class LoginTest {
  @get:Rule val rule = ActivityScenarioRule(LoginActivity::class.java)
  @Test fun ok() {
    onView(withId(R.id.etUser)).perform(typeText("admin"), closeSoftKeyboard())
    onView(withId(R.id.etPass)).perform(typeText("admin123"), closeSoftKeyboard())
    onView(withId(R.id.btnLogin)).perform(click())
    onView(withId(R.id.tvStatus)).check(matches(withText("Login OK")))
  }
  @Test fun fail() {
    onView(withId(R.id.etUser)).perform(typeText("bad"), closeSoftKeyboard())
    onView(withId(R.id.etPass)).perform(typeText("123"), closeSoftKeyboard())
    onView(withId(R.id.btnLogin)).perform(click())
    onView(withId(R.id.tvStatus)).check(matches(withText("Login FAIL")))
  }
}
