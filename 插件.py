import os
from pathlib import Path

# ===================== 适配你的仓库的配置（无需修改）=====================
PROJECT_ROOT = Path.cwd()  # 直接用你当前的仓库根目录
PACKAGE_NAME = "com.reasily.opensource"
APP_NAME = "Reasily"
VERSION_CODE = 1
VERSION_NAME = "1.0.0"
COMPILE_SDK = 34
MIN_SDK = 24
TARGET_SDK = 34
AGP_VERSION = "8.2.2"
KOTLIN_VERSION = "1.9.22"

# 包名转路径
PACKAGE_PATH = PACKAGE_NAME.replace(".", "/")
# 你已有的前端资源目录
FRONTEND_DIR = PROJECT_ROOT / "epub-reader-light"

# ===================== 要生成的文件（全量闭合，无截断）=====================
FILES = {}

# 1. 根目录Gradle核心配置
FILES["settings.gradle.kts"] = f"""
pluginManagement {{
    repositories {{
        google()
        mavenCentral()
        gradlePluginPortal()
    }}
}}
dependencyResolutionManagement {{
    repositoriesMode.set(RepositoriesMode.FAIL_ON_PROJECT_REPOS)
    repositories {{
        google()
        mavenCentral()
    }}
}}
rootProject.name = "Reasily"
include(":app")
""".strip()

FILES["build.gradle.kts"] = f"""
plugins {{
    id("com.android.application") version "{AGP_VERSION}" apply false
    id("org.jetbrains.kotlin.android") version "{KOTLIN_VERSION}" apply false
}}
""".strip()

FILES["gradle.properties"] = """
org.gradle.jvmargs=-Xmx2048m -Dfile.encoding=UTF-8
org.gradle.parallel=true
org.gradle.configuration-cache=true
android.useAndroidX=true
android.nonTransitiveRClass=true
kotlin.code.style=official
""".strip()

# 2. Gradle Wrapper配置（无语法错误，完整闭合）
FILES["gradle/wrapper/gradle-wrapper.properties"] = """
distributionBase=GRADLE_USER_HOME
distributionPath=wrapper/dists
distributionUrl=https\://services.gradle.org/distributions/gradle-8.2-bin.zip
networkTimeout=10000
validateDistributionUrl=true
zipStoreBase=GRADLE_USER_HOME
zipStorePath=wrapper/dists
""".strip()

# 3. GitHub Actions 自动打包配置（核心，推代码就出包）
FILES[".github/workflows/build-apk.yml"] = """
name: 安卓APP自动打包
on:
  push:
    branches: [ main ]
    paths:
      - "app/**"
      - "epub-reader-light/**"
      - "*.gradle.kts"
      - "gradle.properties"
      - ".github/workflows/build-apk.yml"
  workflow_dispatch:

jobs:
  build-release-apk:
    runs-on: ubuntu-latest
    timeout-minutes: 15
    steps:
      - name: 拉取仓库代码
        uses: actions/checkout@v4
        with:
          fetch-depth: 0

      - name: 配置JDK 17
        uses: actions/setup-java@v4
        with:
          java-version: '17'
          distribution: 'temurin'
          cache: gradle

      - name: 配置Android SDK环境
        uses: android-actions/setup-android@v3

      - name: 同步前端资源到安卓项目
        run: |
          mkdir -p app/src/main/assets/www
          cp -r epub-reader-light/* app/src/main/assets/www/
          echo "✅ 前端资源同步完成"
          ls -la app/src/main/assets/www/

      - name: 生成调试签名文件（无需手动配置，直接打包）
        run: |
          keytool -genkey -v -keystore app/debug.keystore \
            -alias androiddebugkey \
            -keyalg RSA \
            -keysize 2048 \
            -validity 10000 \
            -storepass android \
            -keypass android \
            -dname "CN=Android Debug,O=Android,C=US"
          echo "✅ 调试签名文件生成完成"

      - name: 授予Gradle执行权限
        run: chmod +x gradlew

      - name: 构建Release APK
        run: ./gradlew assembleRelease

      - name: 上传APK安装包
        uses: actions/upload-artifact@v4
        with:
          name: Reasily-Release-APK
          path: app/build/outputs/apk/release/*.apk
          retention-days: 30
""".strip()

# 4. app模块核心配置（最小可编译版本）
FILES["app/build.gradle.kts"] = f"""
plugins {{
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}}

android {{
    namespace = "{PACKAGE_NAME}"
    compileSdk = {COMPILE_SDK}

    defaultConfig {{
        applicationId = "{PACKAGE_NAME}"
        minSdk = {MIN_SDK}
        targetSdk = {TARGET_SDK}
        versionCode = {VERSION_CODE}
        versionName = "{VERSION_NAME}"
        testInstrumentationRunner = "androidx.test.runner.AndroidJUnitRunner"
        vectorDrawables.useSupportLibrary = true
    }}

    signingConfigs {{
        create("release") {{
            storeFile = file("debug.keystore")
            storePassword = "android"
            keyAlias = "androiddebugkey"
            keyPassword = "android"
        }}
    }}

    buildTypes {{
        release {{
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(
                getDefaultProguardFile("proguard-android-optimize.txt"),
                "proguard-rules.pro"
            )
            signingConfig = signingConfigs.getByName("release")
        }}
        debug {{
            applicationIdSuffix = ".debug"
            signingConfig = signingConfigs.getByName("release")
        }}
    }}

    compileOptions {{
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }}

    kotlinOptions {{
        jvmTarget = "17"
    }}

    buildFeatures {{
        viewBinding = true
        buildConfig = true
    }}
}}

dependencies {{
    implementation("androidx.core:core-ktx:1.12.0")
    implementation("androidx.appcompat:appcompat:1.6.1")
    implementation("com.google.android.material:material:1.11.0")
    implementation("androidx.constraintlayout:constraintlayout:2.1.4")
    testImplementation("junit:junit:4.13.2")
    androidTestImplementation("androidx.test.ext:junit:1.1.5")
    androidTestImplementation("androidx.test.espresso:espresso-core:3.5.1")
}}
""".strip()

FILES["app/proguard-rules.pro"] = """
-keepattributes *Annotation*
-keepattributes JavascriptInterface
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}
-dontwarn **
""".strip()

# 5. AndroidManifest.xml（最小可运行版本）
FILES["app/src/main/AndroidManifest.xml"] = f"""
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    xmlns:tools="http://schemas.android.com/tools">

    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.READ_MEDIA_DOCUMENTS" />
    <uses-permission android:name="android.permission.WAKE_LOCK" />

    <application
        android:allowBackup="true"
        android:dataExtractionRules="@xml/data_extraction_rules"
        android:hardwareAccelerated="true"
        android:icon="@mipmap/ic_launcher"
        android:label="@string/app_name"
        android:roundIcon="@mipmap/ic_launcher_round"
        android:supportsRtl="false"
        android:theme="@style/Theme.Reasily"
        tools:targetApi="31">

        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:theme="@style/Theme.Reasily"
            android:configChanges="orientation|screenSize|keyboardHidden">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
            <intent-filter>
                <action android:name="android.intent.action.VIEW" />
                <category android:name="android.intent.category.DEFAULT" />
                <data android:scheme="content" />
                <data android:scheme="file" />
                <data android:mimeType="application/epub+zip" />
            </intent-filter>
        </activity>
    </application>
</manifest>
""".strip()

# 6. 基础资源文件
FILES["app/src/main/res/values/themes.xml"] = """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <style name="Theme.Reasily" parent="android:Theme.Material.Light.NoActionBar">
        <item name="android:windowBackground">@color/background</item>
        <item name="android:statusBarColor">@color/surface</item>
        <item name="android:navigationBarColor">@color/surface</item>
        <item name="android:windowLightStatusBar">true</item>
        <item name="android:windowLightNavigationBar">true</item>
    </style>
</resources>
""".strip()

FILES["app/src/main/res/values/colors.xml"] = """
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <color name="primary">#1a73e8</color>
    <color name="primary_container">#d6e4ff</color>
    <color name="on_primary">#ffffff</color>
    <color name="background">#fafafa</color>
    <color name="on_background">#1a1a1a</color>
    <color name="surface">#ffffff</color>
    <color name="on_surface">#1a1a1a</color>
    <color name="surface_variant">#f1f3f4</color>
    <color name="on_surface_variant">#444746</color>
    <color name="outline">#747775</color>
</resources>
""".strip()

FILES["app/src/main/res/values/strings.xml"] = f"""
<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">{APP_NAME}</string>
</resources>
""".strip()

FILES["app/src/main/res/xml/data_extraction_rules.xml"] = """
<?xml version="1.0" encoding="utf-8"?>
<data-extraction-rules xmlns:android="http://schemas.android.com/apk/res/android">
    <cloud-backup>
        <include domain="sharedpref" path="."/>
        <include domain="file" path="."/>
    </cloud-backup>
</data-extraction-rules>
""".strip()

# 7. 核心主页面代码（WebView加载你的阅读器界面，最小可运行）
FILES[f"app/src/main/kotlin/{PACKAGE_PATH}/MainActivity.kt"] = f"""
package {PACKAGE_NAME}

import android.os.Bundle
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {{
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {{
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webview)
        setupWebView()
        // 加载你写的阅读器界面
        webView.loadUrl("file:///android_asset/www/index.html")
    }}

    private fun setupWebView() {{
        webView.settings.apply {{
            // 核心权限开启，保证epub.js正常运行
            javaScriptEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            allowUniversalAccessFromFileURLs = true
            allowFileAccessFromFileURLs = true
            domStorageEnabled = true
            databaseEnabled = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
            setRenderPriority(WebSettings.RenderPriority.HIGH)
        }}
        webView.webViewClient = WebViewClient()
        webView.setLayerType(WebView.LAYER_TYPE_HARDWARE, null)
    }}

    override fun onPause() {{
        super.onPause()
        webView.onPause()
    }}

    override fun onResume() {{
        super.onResume()
        webView.onResume()
    }}

    override fun onDestroy() {{
        super.onDestroy()
        webView.destroy()
    }}

    override fun onBackPressed() {{
        if (webView.canGoBack()) {{
            webView.goBack()
        }} else {{
            super.onBackPressed()
        }}
    }}
}}
""".strip()

# 8. 布局文件
FILES["app/src/main/res/layout/activity_main.xml"] = """
<?xml version="1.0" encoding="utf-8"?>
<WebView xmlns:android="http://schemas.android.com/apk/res/android"
    android:id="@+id/webview"
    android:layout_width="match_parent"
    android:layout_height="match_parent" />
""".strip()

# 9. .gitignore 追加内容（不覆盖你已有的）
GITIGNORE_APPEND = """
# Gradle 构建缓存
.gradle/
build/
app/build/
local.properties

# IDE 配置
.idea/
.vscode/
*.iml
.DS_Store

# 签名文件
*.jks
*.keystore

# 构建产物
*.apk
*.aab

# 日志
*.log
"""

# ===================== 脚本执行逻辑 =====================
def main():
    print("🚀 开始生成Reasily安卓项目基础结构...")
    
    # 1. 创建所有必要的目录
    dirs = [
        "gradle/wrapper",
        ".github/workflows",
        "app/src/main/kotlin/" + PACKAGE_PATH,
        "app/src/main/res/values",
        "app/src/main/res/layout",
        "app/src/main/res/xml",
        "app/src/main/assets/www",
    ]
    
    for dir_path in dirs:
        full_path = PROJECT_ROOT / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"✅ 目录创建完成: {dir_path}")
    
    # 2. 写入所有文件（已存在的文件不会覆盖）
    for file_path, content in FILES.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            print(f"⚠️  文件已存在，跳过: {file_path}")
            continue
        full_path.write_text(content, encoding="utf-8")
        print(f"✅ 文件生成完成: {file_path}")
    
    # 3. 追加.gitignore内容
    gitignore_path = PROJECT_ROOT / ".gitignore"
    if gitignore_path.exists():
        existing_content = gitignore_path.read_text(encoding="utf-8")
        if "# Gradle 构建缓存" not in existing_content:
            gitignore_path.write_text(existing_content + "\n" + GITIGNORE_APPEND, encoding="utf-8")
            print("✅ .gitignore 内容追加完成")
    else:
        gitignore_path.write_text(GITIGNORE_APPEND, encoding="utf-8")
        print("✅ .gitignore 文件生成完成")
    
    # 4. 同步你已有的前端资源
    if FRONTEND_DIR.exists():
        target_assets_dir = PROJECT_ROOT / "app/src/main/assets/www"
        os.system(f"cp -r {FRONTEND_DIR}/* {target_assets_dir}/")
        print(f"✅ 前端资源同步完成，从 {FRONTEND_DIR} 到 {target_assets_dir}")
    else:
        print(f"⚠️  前端目录 {FRONTEND_DIR} 不存在，跳过同步")
    
    print("\n🎉 阶段一执行完成！")
    print("📌 下一步操作：")
    print("1. 执行 git add . && git commit -m 'feat: 新增安卓项目基础结构与自动打包配置'")
    print("2. 执行 git push origin main 推送到GitHub")
    print("3. 打开GitHub仓库的Actions页面，即可看到自动打包正在运行，3分钟后就能下载APK安装包")

if __name__ == "__main__":
    main()
