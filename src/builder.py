"""
py2apk Build Motoru.
QEMU sistem emülasyonu ile Alpine Linux içinde p4a ile APK oluşturur.
Tamamen Docker'sız, her platformda çalışır.
"""

import os
import sys
import shutil
import subprocess
import hashlib
import json
import platform
from pathlib import Path
import urllib.request

# ============================================================
# KONFİGÜRASYON
# ============================================================

CACHE_DIR = Path.home() / ".py2apk" / "cache"
ROOTFS_DIR = Path.home() / ".py2apk" / "rootfs"
BUILD_DIR = Path.home() / ".py2apk" / "build"

# GitHub Release URL'leri (önceden hazırlanmış rootfs)
ROOTFS_URL = "https://github.com/twoplasmastudios/py2apk-rootfs/releases/latest/download/alpine-p4a.qcow2"
ROOTFS_SHA256_URL = "https://github.com/twoplasmastudios/py2apk-rootfs/releases/latest/download/alpine-p4a.sha256"

# QEMU sistem emülasyonu binary URL'leri
QEMU_URLS = {
    "Windows": "https://github.com/twoplasmastudios/py2apk-qemu/releases/latest/download/qemu-system-x86_64.exe",
    "Darwin": "https://github.com/twoplasmastudios/py2apk-qemu/releases/latest/download/qemu-system-x86_64-macos",
    "Linux": "https://github.com/twoplasmastudios/py2apk-qemu/releases/latest/download/qemu-system-x86_64",
}

ROOTFS_SIZE_MB = 800  # genişlemiş hali


# ============================================================
# YARDIMCI FONKSİYONLAR
# ============================================================

def get_platform():
    return platform.system()


def ensure_dir(path):
    Path(path).mkdir(parents=True, exist_ok=True)


def download_file(url, dest, log_callback=None):
    if log_callback:
        log_callback(f"📥 İndiriliyor: {url}", "info")
    urllib.request.urlretrieve(url, dest)
    if log_callback:
        log_callback(f"✅ İndirme tamamlandı: {dest}", "success")


# ============================================================
# QEMU YÖNETİMİ
# ============================================================

def get_qemu_path(log_callback=None):
    """QEMU sistem emülasyonu binary'sini bul veya indir."""
    qemu_dir = CACHE_DIR / "qemu"
    ensure_dir(qemu_dir)

    current_os = get_platform()
    qemu_filename = f"qemu-system-x86_64"
    if current_os == "Windows":
        qemu_filename += ".exe"

    qemu_path = qemu_dir / qemu_filename

    if not qemu_path.exists():
        url = QEMU_URLS.get(current_os)
        if not url:
            raise RuntimeError(f"Desteklenmeyen platform: {current_os}")
        download_file(url, str(qemu_path), log_callback)
        if current_os != "Windows":
            os.chmod(qemu_path, 0o755)

    return str(qemu_path)


# ============================================================
# ROOTFS YÖNETİMİ
# ============================================================

def get_rootfs_path(log_callback=None):
    """Alpine rootfs imajını bul veya indir."""
    rootfs_path = ROOTFS_DIR / "alpine-p4a.qcow2"

    if rootfs_path.exists():
        return str(rootfs_path)

    if log_callback:
        log_callback("📦 Alpine rootfs bulunamadı.", "warning")
        log_callback(f"   İndirilecek boyut: ~{ROOTFS_SIZE_MB} MB", "info")
        log_callback("   Bu işlem yalnızca bir kere yapılır.", "info")

    ensure_dir(ROOTFS_DIR)
    download_file(ROOTFS_URL, str(rootfs_path), log_callback)
    return str(rootfs_path)


# ============================================================
# BUILD İŞLEMİ
# ============================================================

def prepare_build_environment(config, log_callback=None):
    build_id = f"{config['app_name']}_{hashlib.md5(config['py_file'].encode()).hexdigest()[:8]}"
    build_path = BUILD_DIR / build_id
    shutil.rmtree(build_path, ignore_errors=True)
    ensure_dir(build_path)

    if log_callback:
        log_callback(f"🔧 Build ortamı hazırlanıyor: {build_path}", "info")

    py_dest = build_path / "main.py"
    shutil.copy2(config["py_file"], py_dest)
    if log_callback:
        log_callback(f"   📄 {config['py_file']} → main.py", "info")

    if config.get("req_file") and os.path.exists(config["req_file"]):
        shutil.copy2(config["req_file"], build_path / "requirements.txt")
        if log_callback:
            log_callback("   📋 requirements.txt kopyalandı", "info")

    if config.get("icon_file") and os.path.exists(config["icon_file"]):
        shutil.copy2(config["icon_file"], build_path / "icon.png")
        if log_callback:
            log_callback("   🖼️ Simge kopyalandı", "info")

    p4a_config = {
        "app_name": config["app_name"],
        "package_name": config["domain"],
        "main_file": "main.py",
        "requirements": [],
        "permissions": config.get("permissions", ["INTERNET"]),
        "arch": "arm64-v8a",
        "icon": "icon.png" if config.get("icon_file") else None,
    }

    if config.get("req_file") and os.path.exists(config["req_file"]):
        with open(config["req_file"], "r") as f:
            reqs = [line.strip() for line in f if line.strip() and not line.startswith("#")]
        p4a_config["requirements"] = reqs

    config_path = build_path / "p4a_config.json"
    with open(config_path, "w") as f:
        json.dump(p4a_config, f, indent=2)

    if log_callback:
        log_callback("   ⚙️ p4a yapılandırması oluşturuldu", "info")
        if p4a_config["requirements"]:
            log_callback(f"   📦 Bağımlılıklar: {', '.join(p4a_config['requirements'])}", "info")

    return str(build_path), p4a_config


def run_qemu_build(build_path, config, log_callback=None, progress_callback=None):
    qemu_path = get_qemu_path(log_callback)
    rootfs_path = get_rootfs_path(log_callback)

    if log_callback:
        log_callback("=" * 50, "header")
        log_callback("🔨 QEMU build motoru başlatılıyor...", "info")
        log_callback(f"   QEMU: {qemu_path}", "info")
        log_callback(f"   Rootfs: {rootfs_path}", "info")
        log_callback(f"   Build dizini: {build_path}", "info")
        log_callback("=" * 50, "header")

    if progress_callback:
        progress_callback(15, "QEMU başlatılıyor...")

    # QEMU sistem emülasyonu: Alpine'ı başlat, p4a komutunu çalıştır, kapat
    qemu_cmd = [
        qemu_path,
        "-machine", "q35",
        "-cpu", "qemu64",
        "-m", "2G",
        "-smp", "2",
        "-drive", f"file={rootfs_path},if=virtio,format=qcow2",
        "-net", "user,hostfwd=tcp::2222-:22",
        "-net", "nic",
        "-display", "none",
        "-serial", "stdio",
        "-append", "console=ttyS0 root=/dev/vda rw",
        "-kernel", f"{ROOTFS_DIR}/vmlinuz-virt",  # kernel ayrı olabilir
        "-initrd", f"{ROOTFS_DIR}/initramfs-virt",
    ]

    if log_callback:
        log_callback("🚀 QEMU başlıyor...", "info")

    process = subprocess.Popen(qemu_cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                               text=True, bufsize=1)
    try:
        for line in process.stdout:
            if log_callback:
                log_callback(f"   {line.rstrip()}", "info")
        process.wait()
    except KeyboardInterrupt:
        process.terminate()
        raise

    if process.returncode != 0:
        raise RuntimeError(f"Build başarısız oldu. Çıkış kodu: {process.returncode}")

    if log_callback:
        log_callback("✅ Build tamamlandı!", "success")


def copy_apk_to_desktop(build_path, app_name, log_callback=None, progress_callback=None):
    desktop = Path.home() / "Desktop"
    if not desktop.exists():
        desktop = Path.home() / "Masaüstü"

    apk_source = Path(build_path) / f"{app_name}-release.apk"
    apk_dest = desktop / f"{app_name}.apk"

    if apk_source.exists():
        shutil.copy2(apk_source, apk_dest)
        if log_callback:
            log_callback(f"📱 APK masaüstüne kopyalandı: {apk_dest}", "success")
        if progress_callback:
            progress_callback(100, "Tamamlandı! ✅")
        return str(apk_dest)

    raise FileNotFoundError(f"APK bulunamadı. Build çıktısı: {build_path}")


# ============================================================
# ANA BUILD FONKSİYONU
# ============================================================

def build_apk(config, log_callback=None, progress_callback=None):
    log = lambda msg, tag=None: log_callback and log_callback(msg, tag)
    progress = lambda val, text: progress_callback and progress_callback(val, text)

    log("═" * 60, "header")
    log(f"  🚀 Build başlatılıyor: {config['app_name']}", "success")
    log(f"  📅 Domain: {config['domain']}", "info")
    log(f"  🐍 Python: {config['py_file']}", "info")
    if config.get("req_file"):
        log(f"  📦 requirements: {config['req_file']}", "info")
    log("═" * 60, "header")

    progress(2, "Build ortamı hazırlanıyor...")

    try:
        build_path, p4a_config = prepare_build_environment(config, log)
        progress(10, "QEMU ve rootfs kontrol ediliyor...")
        run_qemu_build(build_path, p4a_config, log, progress)
        copy_apk_to_desktop(build_path, config['app_name'], log, progress)

        progress(100, "✅ Build tamamlandı!")
        log("═" * 60, "header")
        log(f"  🎉 APK hazır: Masaüstü/{config['app_name']}.apk", "success")
        log("═" * 60, "header")
    except Exception as e:
        log(f"❌ Build başarısız: {e}", "error")
        progress(0, "Hata oluştu")
        raise