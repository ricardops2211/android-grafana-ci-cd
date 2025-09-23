android {
  namespace = "com.example.app"
  defaultConfig {
    applicationId = "com.example.app"
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
  }
}

dependencies {
  androidTestImplementation("androidx.test:core:1.5.0")
  androidTestImplementation("androidx.test.ext:junit:1.1.5")
  androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}
