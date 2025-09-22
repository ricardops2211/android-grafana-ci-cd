plugins { id("com.android.application"); id("org.jetbrains.kotlin.android") }
android {
  namespace = "com.example.app"
  compileSdk = 34
  defaultConfig {
    applicationId = "com.example.app"
    minSdk = 26; targetSdk = 34
    versionCode = 1; versionName = "1.0"
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
    buildConfigField("String","GIT_SHA","\"DEV\"")
  }
  packaging { resources.excludes += setOf("META-INF/LICENSE*", "META-INF/NOTICE*") }
}
dependencies {
  implementation("androidx.core:core-ktx:1.13.1")
  implementation("androidx.appcompat:appcompat:1.7.0")
  implementation("com.google.android.material:material:1.12.0")
  implementation("androidx.constraintlayout:constraintlayout:2.1.4")
  androidTestImplementation("androidx.test.ext:junit:1.2.1")
  androidTestImplementation("androidx.test.espresso:espresso-core:3.6.1")
  testImplementation("junit:junit:4.13.2")
}
