package com.example.app
import android.os.Bundle
import android.widget.*
import androidx.appcompat.app.AppCompatActivity
import org.json.JSONObject
import android.util.Log
import kotlin.random.Random

class LoginActivity : AppCompatActivity() {
  private fun logMetric(name: String, value: Number, extra: JSONObject = JSONObject()) {
    val o = JSONObject()
      .put("ts", System.currentTimeMillis())
      .put("metric", name)
      .put("value", value)
      .put("commit", BuildConfig.GIT_SHA)
      .put("build", BuildConfig.VERSION_NAME)
    extra.keys().forEach { k -> o.put(k, extra.get(k)) }
    Log.i("METRIC_JSON", o.toString())
  }
  override fun onCreate(savedInstanceState: Bundle?) {
    super.onCreate(savedInstanceState)
    setContentView(R.layout.activity_login)
    val u=findViewById<EditText>(R.id.etUser)
    val p=findViewById<EditText>(R.id.etPass)
    val b=findViewById<Button>(R.id.btnLogin)
    val s=findViewById<TextView>(R.id.tvStatus)
    b.setOnClickListener {
      val ok = u.text.toString().length>=4 && p.text.toString().length>=6 && p.text.toString().any{it.isDigit()} && (u.text.toString()=="admin" && p.text.toString()=="admin123")
      if (ok) { s.text="Login OK";   logMetric("login_success_total",1) }
      else    { s.text="Login FAIL"; logMetric("login_failure_total",1, JSONObject().put("reason","invalid_credentials")) }
      logMetric("render_missed_frames_total", Random.nextInt(0,8))
    }
  }
}
