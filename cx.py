import os
import urllib.request

# 项目根目录（和之前保持一致）
PROJECT_ROOT = "/data/data/com.termux/files/home/reasily-open-source/epub-reader-light"

# 资源下载配置
RESOURCES = [
    {
        "name": "KaTeX CSS",
        "url": "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.css",
        "target": os.path.join(PROJECT_ROOT, "assets", "css", "katex.min.css")
    },
    {
        "name": "KaTeX JS",
        "url": "https://cdn.jsdelivr.net/npm/katex@0.16.9/dist/katex.min.js",
        "target": os.path.join(PROJECT_ROOT, "assets", "js", "katex.min.js")
    },
    {
        "name": "Zepto.js",
        "url": "https://cdn.jsdelivr.net/npm/zepto@1.2.0/dist/zepto.min.js",
        "target": os.path.join(PROJECT_ROOT, "assets", "js", "zepto.min.js")
    },
    {
        "name": "epub.js",
        "url": "https://cdn.jsdelivr.net/npm/epubjs@0.3.93/dist/epub.min.js",
        "target": os.path.join(PROJECT_ROOT, "assets", "js", "epub.min.js")
    },
    {
        "name": "Material Icons TTF",
        "url": "https://fonts.gstatic.com/s/materialicons/v142/MaterialIcons-Regular.ttf",
        "target": os.path.join(PROJECT_ROOT, "assets", "fonts", "MaterialIcons-Regular.ttf")
    }
]

def download_resource(name, url, target):
    try:
        print(f"📥 正在下载 {name}...")
        # 确保目标目录存在
        os.makedirs(os.path.dirname(target), exist_ok=True)
        # 下载文件
        urllib.request.urlretrieve(url, target)
        print(f"✅ {name} 下载完成: {target}")
    except Exception as e:
        print(f"❌ 下载 {name} 失败: {e}")

if __name__ == "__main__":
    print("🚀 开始下载开源资源到 EPUB 阅读器项目...\n")
    for res in RESOURCES:
        download_resource(res["name"], res["url"], res["target"])
    print("\n🎉 所有资源下载完成！")
