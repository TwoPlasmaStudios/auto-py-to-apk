import sys
import webbrowser
import threading
import os
import tempfile
import shutil
from flask import Flask, render_template, request, jsonify
from werkzeug.utils import secure_filename
from .web_apk_builder import build_apk_with_cordova

app = Flask(__name__, template_folder="templates")
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/build", methods=["POST"])
def build():
    py_file = request.files.get('py_file')
    app_name = request.form.get('app_name', '').strip()
    package_name = request.form.get('package_name', '').strip()
    icon_file = request.files.get('icon_file')
    additional_files = request.files.getlist('additional_files')

    if not py_file or not app_name or not package_name:
        return jsonify({"status": "error", "message": "Lütfen .py dosyası, uygulama adı ve paket adını girin."})
    if not py_file.filename.endswith('.py'):
        return jsonify({"status": "error", "message": "Sadece .py dosyası yükleyebilirsiniz."})

    temp_dir = tempfile.mkdtemp(prefix="auto_py_to_apk_")
    try:
        py_path = os.path.join(temp_dir, secure_filename(py_file.filename))
        py_file.save(py_path)

        icon_path = None
        if icon_file and icon_file.filename:
            if icon_file.filename.lower().endswith(('.png', '.jpg', '.jpeg')):
                icon_path = os.path.join(temp_dir, secure_filename(icon_file.filename))
                icon_file.save(icon_path)
            else:
                return jsonify({"status": "error", "message": "İkon PNG/JPG olmalıdır."})

        extra_files = []
        for f in additional_files:
            if f and f.filename:
                dest = os.path.join(temp_dir, secure_filename(f.filename))
                f.save(dest)
                extra_files.append(dest)

        success, result = build_apk_with_cordova(
            py_path=py_path,
            app_name=app_name,
            package_name=package_name,
            icon_path=icon_path,
            extra_files=extra_files
        )
        if success:
            return jsonify({"status": "success", "apk_path": result})
        else:
            return jsonify({"status": "error", "message": result})
    except Exception as e:
        return jsonify({"status": "error", "message": f"Sunucu hatası: {str(e)}"})
    finally:
        shutil.rmtree(temp_dir, ignore_errors=True)

def open_browser():
    webbrowser.open("http://127.0.0.1:5000")

def main():
    print("✅ Auto-Py-to-APK başlatılıyor...")
    print("   Web arayüzü açılacak. (İlk kullanımda JDK, Android SDK, Gradle, Node.js, Cordova hazırlanır - 20-40 dk sürebilir.)")
    threading.Timer(1, open_browser).start()
    app.run(debug=False, port=5000)

if __name__ == "__main__":
    main()