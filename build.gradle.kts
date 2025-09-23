plugins {
  id("com.android.application") version "8.5.2" apply false
  id("org.jetbrains.kotlin.android") version "1.9.24" apply false
}


allprojects {
  // nada especial aquí normalmente
}

android {
  compileSdk = 34
  defaultConfig {
    minSdk = 24
    targetSdk = 34
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
  }
}
