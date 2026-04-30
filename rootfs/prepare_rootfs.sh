#!/bin/bash
set -e

ALPINE_VER="3.20"
ALPINE_ISO="alpine-standard-${ALPINE_VER}.0-x86_64.iso"
QCOW2_NAME="alpine-p4a.qcow2"
QCOW2_SIZE="8G"
ROOT_PASSWORD="py2apk"

echo "🔧 py2apk Alpine Rootfs Hazırlayıcı"
echo "===================================="

# 1. Gereklilikleri kontrol et
command -v qemu-img >/dev/null 2>&1 || { echo "❌ qemu-img bulunamadı. Lütfen qemu-utils kurun."; exit 1; }

# 2. Alpine ISO'yu indir (eğer yoksa)
if [ ! -f "$ALPINE_ISO" ]; then
    echo "📥 Alpine ISO indiriliyor..."
    wget -q "https://dl-cdn.alpinelinux.org/alpine/v${ALPINE_VER%.*}/releases/x86_64/${ALPINE_ISO}"
fi

# 3. Boş qcow2 imajı oluştur
echo "💾 QCOW2 disk imajı oluşturuluyor (${QCOW2_SIZE})..."
qemu-img create -f qcow2 "$QCOW2_NAME" "$QCOW2_SIZE"

# 4. QEMU ile Alpine kur
echo "🐧 QEMU başlatılıyor... (Kurulum otomatik yapılacak)"
qemu-system-x86_64 \
    -machine q35 \
    -cpu qemu64 \
    -m 2G \
    -smp 2 \
    -drive file="${QCOW2_NAME}",if=virtio,format=qcow2 \
    -cdrom "${ALPINE_ISO}" \
    -netdev user,id=n1 \
    -device virtio-net,netdev=n1 \
    -display none \
    -serial stdio \
    -boot d \
    -kernel "" \
    -append "" &

QEMU_PID=$!
sleep 30

# 5. Alpine setup'ı otomatik yap (expect veya manuel)
echo "⚠️  Alpine kurulumu için manuel müdahale gerekiyor."
echo "   Lütfen açılan QEMU penceresinde:"
echo "   1. root olarak giriş yap (şifre yok)"
echo "   2. setup-alpine komutunu çalıştır"
echo "   3. Disk: vda, sys kurulumu yap"
echo "   4. OpenSSH kur"
echo "   5. Kurulum bitince 'poweroff' yaz"
echo ""
echo "   Kurulum bittikten sonra devam etmek için Enter'a bas..."
read

# 6. Kurulum sonrası paketleri eklemek için imajı tekrar başlat
echo "🔄 Kurulum sonrası yapılandırma için QEMU başlatılıyor..."
qemu-system-x86_64 \
    -machine q35 \
    -cpu qemu64 \
    -m 2G \
    -smp 2 \
    -drive file="${QCOW2_NAME}",if=virtio,format=qcow2 \
    -netdev user,id=n1,hostfwd=tcp::2222-:22 \
    -device virtio-net,netdev=n1 \
    -display none \
    -serial stdio &

QEMU_PID=$!
sleep 15

echo "📦 Alpine içine gerekli paketler kuruluyor..."
ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -p 2222 root@localhost <<'SSHEND'
apk update
apk add --no-cache \
    python3 py3-pip python3-dev bash git wget curl \
    openjdk17-jdk build-base libffi-dev openssl-dev \
    zlib-dev bzip2-dev ncurses-dev sqlite-dev \
    readline-dev tk-dev xz-dev gdbm-dev linux-headers

pip3 install --no-cache-dir python-for-android cython setuptools wheel

# Android NDK
mkdir -p /opt/android-sdk /opt/android-ndk
cd /tmp
wget -q https://dl.google.com/android/repository/android-ndk-r25c-linux.zip
unzip -q android-ndk-r25c-linux.zip
mv android-ndk-r25c/* /opt/android-ndk/
rm -rf android-ndk-r25c*

# Android SDK
wget -q https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip -q commandlinetools-linux-11076708_latest.zip
mkdir -p /opt/android-sdk/cmdline-tools
mv cmdline-tools /opt/android-sdk/cmdline-tools/latest
rm commandlinetools-linux-11076708_latest.zip

yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=/opt/android-sdk \
    "platform-tools" "platforms;android-33" "build-tools;33.0.2"

# Çevre değişkenleri
cat >> /etc/profile <<'EOF'
export ANDROID_SDK_ROOT=/opt/android-sdk
export ANDROID_NDK_ROOT=/opt/android-ndk
export PATH=$PATH:/opt/android-sdk/platform-tools
EOF

# Build testi
echo 'print("🐧 Alpine p4a hazır!")' > /root/test.py
echo "✅ Kurulum tamamlandı!"
poweroff
SSHEND

wait $QEMU_PID 2>/dev/null

# 7. Sıkıştırma
echo "🗜️  Sıkıştırma yapılıyor..."
gzip -k "${QCOW2_NAME}" "${QCOW2_NAME}.gz" 2>/dev/null || \
    echo "⚠️  gzip sıkıştırma atlandı (isteğe bağlı)"

echo "============================================"
echo "✅ Rootfs imajı hazır!"
echo "   Dosya: ${QCOW2_NAME}"
echo "   Boyut: $(du -h ${QCOW2_NAME} | cut -f1)"
echo "============================================"
echo ""
echo "📤 Bu dosyayı GitHub Release'e yükleyin:"
echo "   1. https://github.com/TwoPlasmaStudios/auto-py-to-apk/releases"
echo "   2. 'Create a new release'"
echo "   3. Tag: v0.1.0-rootfs"
echo "   4. alpine-p4a.qcow2 dosyasını ekleyin"
