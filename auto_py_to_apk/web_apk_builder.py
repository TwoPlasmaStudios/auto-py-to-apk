import os
import sys
import platform
import subprocess
import tempfile
import shutil
import zipfile
import urllib.request
from pathlib import Path

# ---------- Yardımcı ----------
def download_file(url, dest_path, description="İndiriliyor"):
    print(f"{description}: {url}")
    urllib.request.urlretrieve(url, dest_path, lambda count, block, total: print(f"\r   {count*block/(1024*1024):.1f} MB / {total/(1024*1024):.1f} MB", end="") if total>0 else None)
    print()

def extract_zip(zip_path, extract_to):
    print(f"📦 Çıkartılıyor: {zip_path}")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    os.remove(zip_path)

def run_cmd_live(cmd, env=None, cwd=None, description="", input_data=None):
    """Komutu canlı çalıştır, isteğe bağlı input gönder (manuel onay için)"""
    if description:
        print(description)
    if isinstance(cmd, str):
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=cwd, shell=True, bufsize=1, stdin=subprocess.PIPE if input_data else None)
    else:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, env=env, cwd=cwd, bufsize=1, stdin=subprocess.PIPE if input_data else None)
    
    if input_data:
        process.stdin.write(input_data)
        process.stdin.close()
    
    for line in process.stdout:
        print(line, end='')
    process.wait()
    if process.returncode != 0:
        raise Exception(f"Komut başarısız: {cmd}")
    return process.returncode

# ---------- JDK (portable) ----------
def ensure_jdk():
    home = Path.home() / ".auto-py-to-apk" / "jdk"
    home.mkdir(parents=True, exist_ok=True)
    marker = home / "jdk_installed.txt"
    if marker.exists():
        for item in home.iterdir():
            if item.is_dir() and item.name.startswith("jdk"):
                java_exe = item / "bin" / "java.exe" if sys.platform == "win32" else item / "bin" / "java"
                if java_exe.exists():
                    return str(java_exe)
    print("⚙️ JDK kuruluyor (ilk seferde)...")
    if sys.platform == "win32":
        url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk-17.0.12%2B7/OpenJDK17U-jdk_x64_windows_hotspot_17.0.12_7.zip"
        zip_path = home / "jdk.zip"
        download_file(url, zip_path, "📥 JDK indiriliyor")
        extract_zip(zip_path, home)
        for item in home.iterdir():
            if item.is_dir() and item.name.startswith("jdk"):
                java_exe = item / "bin" / "java.exe"
                if java_exe.exists():
                    with open(marker, "w") as f:
                        f.write(str(java_exe))
                    return str(java_exe)
    else:
        raise Exception("Otomatik JDK sadece Windows'ta destekleniyor. Lütfen Java 17 kurun.")
    raise Exception("JDK kurulumu başarısız")

# ---------- Android SDK (portable) ----------
def ensure_android_sdk(java_exe):
    sdk_root = Path.home() / ".auto-py-to-apk" / "android-sdk"
    sdk_root.mkdir(parents=True, exist_ok=True)
    marker = sdk_root / "sdk_installed.txt"
    if marker.exists():
        return str(sdk_root)

    print("⚙️ Android SDK kuruluyor (ilk seferde 10-20 dk)...")
    if sys.platform == "win32":
        tools_url = "https://dl.google.com/android/repository/commandlinetools-win-11076708_latest.zip"
    elif sys.platform == "darwin":
        tools_url = "https://dl.google.com/android/repository/commandlinetools-mac-11076708_latest.zip"
    else:
        tools_url = "https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"

    tools_zip = sdk_root / "cmdline-tools.zip"
    download_file(tools_url, tools_zip, "📥 Command line tools indiriliyor")

    temp_extract = sdk_root / "temp_extract"
    temp_extract.mkdir(exist_ok=True)
    with zipfile.ZipFile(tools_zip, 'r') as zip_ref:
        zip_ref.extractall(temp_extract)
    os.remove(tools_zip)

    cmdline_dest = sdk_root / "cmdline-tools" / "latest"
    cmdline_dest.mkdir(parents=True, exist_ok=True)
    extracted_cmdline = temp_extract / "cmdline-tools"
    if extracted_cmdline.exists():
        for item in extracted_cmdline.iterdir():
            dest = cmdline_dest / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    else:
        for item in temp_extract.iterdir():
            dest = cmdline_dest / item.name
            if item.is_dir():
                shutil.copytree(item, dest, dirs_exist_ok=True)
            else:
                shutil.copy2(item, dest)
    shutil.rmtree(temp_extract)

    sdkmanager = cmdline_dest / "bin" / "sdkmanager.bat" if sys.platform == "win32" else cmdline_dest / "bin" / "sdkmanager"
    if not sdkmanager.exists():
        raise Exception("sdkmanager bulunamadı")

    # Lisansları kabul et (kullanıcıdan manuel 'y' girmesini iste)
    print("📜 Lisansları kabul etmek için aşağıdaki sorulara 'y' yazın (ve Enter'a basın).")
    print("   Bu sadece ilk kurulumda bir kere yapılacaktır.\n")
    env = os.environ.copy()
    env["JAVA_HOME"] = str(Path(java_exe).parent.parent)
    # Etkileşimli olarak çalıştır, kullanıcı 'y' yazacak
    subprocess.run([str(sdkmanager), "--licenses"], env=env, cwd=str(sdk_root))

    components = [
        "platform-tools",
        "build-tools;36.0.0",
        "platforms;android-36",
        "ndk;23.1.7779620"
    ]
    print("📱 Android SDK bileşenleri indiriliyor (1.2 GB)...")
    for comp in components:
        print(f"   Yükleniyor: {comp}")
        cmd = [str(sdkmanager), f"--sdk_root={sdk_root}", comp]
        try:
            run_cmd_live(cmd, env=env, cwd=str(sdk_root), description=f"   İndiriliyor {comp}...")
        except Exception as e:
            print(f"   Uyarı: {comp} yüklenemedi: {e}")
    with open(marker, "w") as f:
        f.write(str(sdk_root))
    return str(sdk_root)

# ---------- Gradle (portable) ----------
def ensure_gradle():
    home = Path.home() / ".auto-py-to-apk" / "gradle"
    home.mkdir(parents=True, exist_ok=True)
    marker = home / "gradle_installed.txt"
    if marker.exists():
        for item in home.iterdir():
            if item.is_dir() and item.name.startswith("gradle"):
                gradle_bin = item / "bin" / "gradle.bat" if sys.platform == "win32" else item / "bin" / "gradle"
                if gradle_bin.exists():
                    return str(gradle_bin)
    print("⚙️ Gradle kuruluyor...")
    url = "https://services.gradle.org/distributions/gradle-8.7-bin.zip"
    zip_path = home / "gradle.zip"
    download_file(url, zip_path, "📥 Gradle indiriliyor")
    extract_zip(zip_path, home)
    for item in home.iterdir():
        if item.is_dir() and item.name.startswith("gradle"):
            gradle_bin = item / "bin" / "gradle.bat" if sys.platform == "win32" else item / "bin" / "gradle"
            if gradle_bin.exists():
                with open(marker, "w") as f:
                    f.write(str(gradle_bin))
                return str(gradle_bin)
    raise Exception("Gradle kurulumu başarısız")

# ---------- Node.js (portable) ----------
def ensure_nodejs():
    home = Path.home() / ".auto-py-to-apk" / "nodejs"
    home.mkdir(parents=True, exist_ok=True)
    marker = home / "node_installed.txt"
    if marker.exists():
        with open(marker, "r") as f:
            node_exe = f.readline().strip()
            npm_cmd = f.readline().strip()
        if os.path.exists(node_exe) and os.path.exists(npm_cmd):
            return node_exe, npm_cmd
    if sys.platform != "win32":
        raise Exception("Node.js kurulumu sadece Windows'ta otomatik. Lütfen Node.js kurun.")
    print("⚙️ Node.js kuruluyor...")
    node_version = "v22.14.0"
    url = f"https://nodejs.org/dist/{node_version}/node-{node_version}-win-x64.zip"
    zip_path = home / "node.zip"
    download_file(url, zip_path, "📥 Node.js indiriliyor")
    extract_zip(zip_path, home)
    for item in home.iterdir():
        if item.is_dir() and item.name.startswith("node-"):
            node_exe = item / "node.exe"
            npm_cmd = item / "npm.cmd"
            if node_exe.exists() and npm_cmd.exists():
                with open(marker, "w") as f:
                    f.write(f"{node_exe}\n{npm_cmd}")
                return str(node_exe), str(npm_cmd)
    raise Exception("Node.js kurulumu başarısız")

# ---------- Cordova (portable) ----------
def ensure_cordova(npm_cmd):
    cordova_home = Path.home() / ".auto-py-to-apk" / "cordova_package"
    cordova_home.mkdir(parents=True, exist_ok=True)
    marker = cordova_home / "cordova_installed.txt"
    if marker.exists():
        cordova_bin = cordova_home / "node_modules" / ".bin" / "cordova"
        if sys.platform == "win32":
            cordova_bin = cordova_home / "node_modules" / ".bin" / "cordova.cmd"
        if cordova_bin.exists():
            return str(cordova_bin)
    print("📦 Cordova kuruluyor...")
    subprocess.run([npm_cmd, "install", "cordova", "--prefix", str(cordova_home)], check=True, capture_output=True)
    with open(marker, "w") as f:
        f.write("installed")
    cordova_bin = cordova_home / "node_modules" / ".bin" / "cordova"
    if sys.platform == "win32":
        cordova_bin = cordova_home / "node_modules" / ".bin" / "cordova.cmd"
    if not cordova_bin.exists():
        raise Exception("Cordova kurulumu başarısız")
    return str(cordova_bin)

# ---------- Pyodide HTML ----------
def create_pyodide_html(py_code, app_name):
    py_code_escaped = py_code.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")
    return f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1, user-scalable=no">
    <title>{app_name}</title>
    <script src="https://cdn.jsdelivr.net/pyodide/v0.26.1/full/pyodide.js"></script>
    <style>
        body {{ margin: 0; padding: 0; background: #1e1e1e; color: #d4d4d4; font-family: monospace; }}
        #output {{ white-space: pre-wrap; padding: 10px; height: 75vh; overflow-y: auto; background: #1e1e1e; }}
        #input-line {{ display: flex; padding: 5px; background: #2d2d2d; position: fixed; bottom: 0; width: 100%; }}
        #prompt {{ padding: 5px; }}
        #input {{ flex: 1; background: #2d2d2d; border: none; color: white; padding: 5px; outline: none; }}
        button {{ background: #0e639c; border: none; color: white; padding: 5px 10px; cursor: pointer; }}
    </style>
</head>
<body>
<div id="output">Pyodide yükleniyor...</div>
<div id="input-line">
    <span id="prompt">>>> </span>
    <input type="text" id="input" autofocus>
    <button onclick="runCode()">Çalıştır</button>
</div>
<script>
    let pyodide;
    async function main() {{
        let output = document.getElementById("output");
        output.innerText = "Pyodide başlatılıyor...\\n";
        pyodide = await loadPyodide();
        output.innerText = "Python ortamı hazır. Kodunuz çalıştırılıyor...\\n";
        try {{
            await pyodide.runPythonAsync(`{py_code_escaped}`);
            output.innerText += "\\nKod başarıyla çalıştı. Şimdi komut girebilirsiniz.\\n";
        }} catch(err) {{
            output.innerText += "\\nHata: " + err + "\\n";
        }}
    }}
    main();
    async function runCode() {{
        let code = document.getElementById("input").value;
        if (!code) return;
        document.getElementById("input").value = "";
        let output = document.getElementById("output");
        output.innerText += "\\n>>> " + code;
        try {{
            let result = await pyodide.runPythonAsync(code);
            if (result !== undefined) output.innerText += "\\n" + result;
        }} catch(err) {{
            output.innerText += "\\nHata: " + err;
        }}
        output.scrollTop = output.scrollHeight;
    }}
</script>
</body>
</html>"""

# ---------- Ana APK yapım fonksiyonu ----------
def build_apk_with_cordova(py_path, app_name, package_name, icon_path=None, extra_files=None):
    if extra_files is None:
        extra_files = []

    print("🔧 Gerekli araçlar hazırlanıyor (ilk seferde uzun sürebilir)...")
    java_exe = ensure_jdk()
    sdk_root = ensure_android_sdk(java_exe)
    gradle_bin = ensure_gradle()
    node_exe, npm_cmd = ensure_nodejs()
    cordova_bin = ensure_cordova(npm_cmd)

    env = os.environ.copy()
    env["JAVA_HOME"] = str(Path(java_exe).parent.parent)
    env["ANDROID_HOME"] = sdk_root
    env["ANDROID_SDK_ROOT"] = sdk_root
    gradle_dir = str(Path(gradle_bin).parent)
    env["PATH"] = f"{gradle_dir};{env.get('PATH', '')}"

    temp_dir = tempfile.mkdtemp(prefix="auto_apk_")
    try:
        with open(py_path, "r", encoding="utf-8") as f:
            py_code = f.read()
        html_content = create_pyodide_html(py_code, app_name)

        print("📁 Cordova projesi oluşturuluyor...")
        run_cmd_live([cordova_bin, "create", temp_dir, package_name, app_name], env=env)

        www_dir = os.path.join(temp_dir, "www")
        for item in os.listdir(www_dir):
            p = os.path.join(www_dir, item)
            if os.path.isfile(p):
                os.unlink(p)
            elif os.path.isdir(p):
                shutil.rmtree(p)
        with open(os.path.join(www_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(html_content)
        for extra in extra_files:
            if os.path.exists(extra):
                shutil.copy2(extra, www_dir)
        if icon_path and os.path.exists(icon_path):
            icon_dir = os.path.join(temp_dir, "res", "icon", "android")
            os.makedirs(icon_dir, exist_ok=True)
            shutil.copy(icon_path, os.path.join(icon_dir, "icon.png"))

        print("➕ Android platform ekleniyor...")
        run_cmd_live([cordova_bin, "platform", "add", "android"], cwd=temp_dir, env=env)

        print("🏗️ APK derleniyor (2-5 dk)...")
        run_cmd_live([cordova_bin, "build", "android"], cwd=temp_dir, env=env)

        apk_path = None
        debug_dir = os.path.join(temp_dir, "platforms", "android", "app", "build", "outputs", "apk", "debug")
        if os.path.exists(debug_dir):
            for f in os.listdir(debug_dir):
                if f.endswith(".apk"):
                    apk_path = os.path.join(debug_dir, f)
                    break
        if not apk_path:
            for root, dirs, files in os.walk(os.path.join(temp_dir, "platforms")):
                for f in files:
                    if f.endswith(".apk"):
                        apk_path = os.path.join(root, f)
                        break
                if apk_path:
                    break
        if not apk_path:
            raise Exception("APK bulunamadı")

        output_apk = os.path.join(os.getcwd(), f"{app_name.replace(' ', '_')}.apk")
        shutil.copy2(apk_path, output_apk)
        return True, output_apk
    except Exception as e:
        return False, str(e)
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)