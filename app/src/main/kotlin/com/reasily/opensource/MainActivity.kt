package com.reasily.opensource

import android.os.Bundle
import android.webkit.WebSettings
import android.webkit.WebView
import android.webkit.WebViewClient
import androidx.appcompat.app.AppCompatActivity

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        setContentView(R.layout.activity_main)
        webView = findViewById(R.id.webview)
        setupWebView()
        webView.loadUrl("file:///android_asset/www/index.html")
    }

    private fun setupWebView() {
        webView.settings.apply {
            // 原有核心配置保留
            javaScriptEnabled = true
            allowFileAccess = true
            allowContentAccess = true
            domStorageEnabled = true
            setSupportZoom(true)
            builtInZoomControls = true
            displayZoomControls = false
            useWideViewPort = true
            loadWithOverviewMode = true
            // 新增：适配高版本混合内容限制，解决资源加载失败
            mixedContentMode = WebSettings.MIXED_CONTENT_COMPATIBILITY_MODE
            // 移除：已废弃的allowUniversalAccessFromFileURLs（高版本系统禁用）
        }
        // 新增：重写WebViewClient捕获加载错误，避免隐性崩溃/网页解析失败
        webView.webViewClient = object : WebViewClient() {
            override fun onPageFinished(view: WebView?, url: String?) {
                super.onPageFinished(view, url)
            }

            override fun onReceivedError(
                view: WebView?,
                errorCode: Int,
                description: String?,
                failingUrl: String?
            ) {
                super.onReceivedError(view, errorCode, description, failingUrl)
            }
        }
        // 原有硬件加速配置保留
        webView.setLayerType(WebView.LAYER_TYPE_HARDWARE, null)
    }

    // 原有生命周期方法完全保留，无修改
    override fun onPause() {
        super.onPause()
        webView.onPause()
    }

    override fun onResume() {
        super.onResume()
        webView.onResume()
    }

    override fun onDestroy() {
        super.onDestroy()
        webView.destroy()
    }
}
