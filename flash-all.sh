#!/bin/bash

set -e

echo "======================================"
echo "   DariaOS 5 Downgrade Flash Script"
echo "======================================"

# Check device
echo "Checking device..."
if ! fastboot devices | grep -q .; then
    echo "ERROR: No device in fastboot mode!"
    echo "   Run: adb reboot bootloader"
    exit 1
fi
echo "Device detected"

# List of slot-specific partitions
PARTITIONS="boot cam_vpu1 cam_vpu2 cam_vpu3 dpm dtbo gz lk mcupm md1img pi_img preloader scp spmfw sspm tee vbmeta vbmeta_system vbmeta_vendor"

# Flash super.img
echo
echo "=== Flashing super.img ==="
[ ! -f "ROM/super.img" ] && { echo "ERROR: ROM/super.img not found!"; exit 1; }
fastboot flash super ROM/super.img || { echo "ERROR: Failed to flash super.img"; exit 1; }
echo "super.img flashed"

# Flash to slot B
echo
echo "=== Flashing all partitions to slot B ==="
for part in $PARTITIONS; do
    img="ROM/${part}.img"
    [ ! -f "$img" ] && { echo "ERROR: $img not found!"; exit 1; }
    target="${part}_b"
    echo "Flashing $target <- $img"
    fastboot flash "$target" "$img" || { echo "ERROR: Failed to flash $target"; exit 1; }
    echo "$target flashed"
done

# Flash to slot A
echo
echo "=== Flashing all partitions to slot A ==="
for part in $PARTITIONS; do
    img="ROM/${part}.img"
    [ ! -f "$img" ] && { echo "ERROR: $img not found!"; exit 1; }
    target="${part}_a"
    echo "Flashing $target <- $img"
    fastboot flash "$target" "$img" || { echo "ERROR: Failed to flash $target"; exit 1; }
    echo "$target flashed"
done

# Set active slot to A (final)
echo
echo "=== Setting active slot to A ==="
fastboot --set-active=a || { echo "ERROR: Failed to set active slot to a"; exit 1; }
echo "Active slot set to A"

# Final success + reboot
echo
echo "======================================"
echo "   ALL PARTITIONS FLASHED ON BOTH SLOTS"
echo "   super.img: shared"
echo "   All others: flashed to _a and _b"
echo "   Final active slot: A"
echo "   Rebooting in 3 seconds..."
echo "======================================"
sleep 3
fastboot reboot
echo "Device rebooted into slot A"