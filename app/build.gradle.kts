plugins {
  id("com.android.application") version "8.5.2"
  id("org.jetbrains.kotlin.android") version "1.9.24"
}

android {
  namespace = "com.example.app"
  compileSdk = 34

  defaultConfig {
    applicationId = "com.example.app"
    minSdk = 24
    targetSdk = 34
    versionCode = 1
    versionName = "1.0"
    testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
  }

  buildTypes {
    release {
      isMinifyEnabled = false
      proguardFiles(
        getDefaultProguardFile("proguard-android-optimize.txt"),
        "proguard-rules.pro"
      )
    }
  }

  // Java/Kotlin 17
  compileOptions {
    sourceCompatibility = JavaVersion.VERSION_17
    targetCompatibility = JavaVersion.VERSION_17
  }
  kotlinOptions {
    jvmTarget = "17"
  }
}

dependencies {
  implementation("androidx.core:core-ktx:1.13.1")
  implementation("androidx.appcompat:appcompat:1.7.0")
  implementation("com.google.android.material:material:1.12.0")
  implementation("androidx.activity:activity-ktx:1.9.2")
  implementation("androidx.constraintlayout:constraintlayout:2.1.4")

  testImplementation("junit:junit:4.13.2")

  // UI/instrumentation
  androidTestImplementation("androidx.test:core:1.5.0")
  androidTestImplementation("androidx.test.ext:junit:1.1.5")
  androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
  androidTestImplementation("androidx.test:rules:1.5.0")
}
