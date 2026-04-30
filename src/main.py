"""
py2apk ana giriş noktası.
Terminalden py2apk veya auto-py-to-apk yazınca GUI'yi başlatır.
"""

import sys


def main():
    """Ana fonksiyon - GUI'yi başlatır."""
    print("🚀 py2apk v0.1.0 başlatılıyor...")
    print("📱 Python kodunu APK'ya dönüştürme aracı")
    print("=" * 50)

    try:
        from py2apk.app import launch_gui
        launch_gui()
    except ImportError as e:
        print(f"❌ GUI başlatılamadı: {e}")
        print("💡 Gerekli: tkinter (Python ile birlikte gelir)")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Beklenmeyen hata: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()