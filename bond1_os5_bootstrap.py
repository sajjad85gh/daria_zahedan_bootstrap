"""
Daria Bond 1 Flash Script
Cross-platform fastboot flashing utility for Windows and Linux
"""

import os
import sys
import subprocess
import time
import platform
from pathlib import Path
import hashlib
from tqdm import tqdm

IS_TESTING = False

IS_WINDOWS = platform.system() == "Windows"

PARTITIONS = [
    "boot", "cam_vpu1", "cam_vpu2", "cam_vpu3", "dpm", "dtbo", 
    "gz", "lk", "mcupm", "md1img", "pi_img", "preloader", 
    "scp", "spmfw", "sspm", "tee", "vbmeta_system", "vbmeta_vendor"
]

ROM_DOWNLOAD_LINK = "https://pixeldrain.com/u/dQZ5AeoJ"

ROM_DIR = "ROM"

def get_fastboot_path():
    """Get the appropriate fastboot path for the current OS"""
    try:
        subprocess.run(["fastboot", "--version"], 
                        capture_output=True, check=True)
        return "fastboot"
    except (subprocess.CalledProcessError, FileNotFoundError):
        if IS_WINDOWS:
            fastboot = Path("platform-tools/fastboot.exe")
        else:
            # Try local platform-tools first, then system fastboot
            fastboot = Path("platform-tools/fastboot")
    
    if not fastboot.exists():
        print(f"ERROR: {fastboot} not found!")
        print("Place this script next to platform-tools folder or install fastboot.")
        sys.exit(1)
    
    return str(fastboot)


def run_fastboot(fastboot_path, *args):
    """Run fastboot command and return result"""
    cmd = [fastboot_path] + list(args)
    if IS_TESTING:
        while True:
            inp = input(f"[TESTING] Run '{cmd}'? [y/n]: ").lower()
            if inp == "y":
                result = subprocess.run(cmd, capture_output=True, text=True)
                return result
            elif inp == "n":
                print("Skipped command, be careful!")
                break
            else:
                print("Invalid option.")
    else:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return result


def check_device(fastboot_path):
    """Check if device is in fastboot mode"""
    print("Checking device...")
    result = run_fastboot(fastboot_path, "devices")
    
    if not result.stdout.strip() or "fastboot" not in result.stdout:
        print()
        print("ERROR: No device in fastboot mode!")
        print("   Run: adb reboot bootloader")
        sys.exit(1)
    
    result = run_fastboot(fastboot_path, "getvar", "product")

    if "k6877v1_64" in result.stdout:
        print("Daria Bond 1 on ")

def md5(file_path):
    # Calculate the MD5 hash of a file.
    with open(file_path, 'rb') as f:
        file_hash = hashlib.md5()
        while chunk := f.read(8192):
            file_hash.update(chunk)
    return file_hash.hexdigest()

def check_file_hashes():
    if not Path(ROM_DIR).exists():
        print("ERROR: The ROM directory doesn't exist,")
        print(f"Download it from the script or '{ROM_DOWNLOAD_LINK}'")
        sys.exit(1)

    with open("rom_checksums.txt", "r") as checksum_file:
        lines = checksum_file.readlines()
        for line in tqdm(lines, desc="Checking file integrity"):
            expected_md5hash, filename = line.strip().split("  ")
            filepath = Path(ROM_DIR) / filename

            if not filepath.exists():
                print(f"ERROR: {filepath} not found!")
                sys.exit(1)

            file_md5hash = md5(str(filepath))
            if file_md5hash == expected_md5hash:
                tqdm.write(f"{filename}: PASSED")
                continue
            else:
                tqdm.write(f"ERROR: {filename} is corrupted!\nMD5 Hash: {file_md5hash}\nExpected: {expected_md5hash}")
                sys.exit(1)
        return True
    
def flash_partition(fastboot_path, partition, img_path, quiet=True):
    """Flash a single partition"""
    print(f"Flashing {partition} <- {img_path}")
    
    result = run_fastboot(fastboot_path, "flash", partition, img_path)
    
    if result.returncode != 0:
        print()
        print(f"ERROR: Failed to flash {partition}")
        print(result.stderr)
        sys.exit(1)
    
    if not quiet:
        print(result.stdout)
    print(f"{partition} flashed")


def flash_vbmeta(fastboot_path, img_path):
    """Flash vbmeta with disabled verification"""
    print(f"Flashing vbmeta <- {img_path}")
    
    result = run_fastboot(fastboot_path, "--disable-verity", 
                         "--disable-verification", "flash", "vbmeta", img_path)
    
    if result.returncode != 0:
        print()
        print("ERROR: Failed to flash vbmeta.img")
        print(result.stderr)
        sys.exit(1)
    
    print("vbmeta.img flashed")


def set_active_slot(fastboot_path, slot):
    """Set active boot slot"""
    print(f"\n=== Setting active slot to {slot.upper()} ===")
    result = run_fastboot(fastboot_path, f"--set-active={slot}")
    
    if result.returncode != 0:
        print(f"ERROR: Failed to set active slot to {slot}")
        print(result.stderr)
        sys.exit(1)
    
    print(f"Active slot set to {slot.upper()}")

def show_disclaimer():
    print("Note: If at any stage of flashing the partitions to the phone, a partition fails to flash, the phone must not be restarted under any circumstances, and the script must be run again.")
    print()
    print("توجه: اگر در هر مرحله‌ای از فلش پارتیشن ها به گوشی، یک پارتیشن فلش نشد یا هر خطای دیگری دریافت شد، گوشی به هیچ وجه نباید راه‌انداری مجدد شود و اسکریپت باید دوباره اجرا شود.")
    print()
    for i in list(reversed(range(10))):
        print(f"{i}s to continue...", end="\r")
        time.sleep(1)
    
    while True:
        match input(f"Continue - ادامه? [y/n]: ").lower():
            case "y": return True
            case "n": sys.exit(1)
            case _: print("Invalid Option.")

def clear_screen():
    """Clear screen for both Windows and Linux"""
    os.system('cls' if IS_WINDOWS else 'clear')

def start_downgrade(fastboot):
    """Main flashing procedure"""
    
    show_disclaimer()    

    # Check the integrity of all files
    check_file_hashes()

    # Check device connection
    check_device(fastboot)
    
    # Flash super.img (shared between slots)
    print("\n=== Flashing super.img ===")
    flash_partition(fastboot, "super", "ROM/super.img")
    
    # Flash to slot A & B
    print("\n=== Flashing all partitions to slot A and B ===")
    for part in PARTITIONS:
        img = f"ROM/{part}.img"

        target = f"{part}_a"
        flash_partition(fastboot, target, img)

        target = f"{part}_b"
        flash_partition(fastboot, target, img)
    
    # Flash misc.img (shared)
    print("\n=== Flashing misc.img ===")
    flash_partition(fastboot, "misc", "ROM/misc.img")
    
    # Flash vbmeta.img to slot B
    print("\n=== Flashing vbmeta.img ===")
    flash_vbmeta(fastboot, "ROM/vbmeta.img")
    
    # Set active slot to A
    set_active_slot(fastboot, "a")
    
    # Flash misc.img again
    print("\n=== Flashing misc.img ===")
    flash_partition(fastboot, "misc", "ROM/misc.img")
    
    # Flash vbmeta.img to slot A
    print("\n=== Flashing vbmeta.img ===")
    flash_vbmeta(fastboot, "ROM/vbmeta.img")
    
    # Final success message
    print()
    print("=" * 42)
    print("   ALL PARTITIONS FLASHED ON BOTH SLOTS")
    print("   super.img: shared")
    print("   All others: flashed to _a and _b")
    print("   Final active slot: A")
    print("=" * 42)
    print()

    time.sleep(3)
    
    # Reboot device
    print("Do you want the device to reboot? Only type 'y' if all images flashed without any error.")
    print("آیا می‌خواهید دستگاه راه‌اندازی مجدد شود؟ فقط اگر همهٔ ایمیج‌ها بدون هیچ خطایی فلش شده‌اند، حرف 'y' را وارد کنید.")
    if input("Reboot? [y/n]: "):
        result = run_fastboot(fastboot, "reboot")
        print("Device rebooted into slot A")
    
    # Pause on Windows to keep window open
    if platform.system() == "Windows":
        input("\nPress Enter to exit...")

def main():
    # Get fastboot path
    fastboot = get_fastboot_path()
    clear_screen()

    while True:
        print("=" * 60)
        print("   Daria Bond 1 (zahedan) - bootstrap to DariaOS5 - k4.19 Script")
        print(f"   Fastboot: {fastboot}")
        print("   Enter fastboot and type 1 to start bootstrap.")
        print()
        print("   Credits: @Itis_Sajjad - @Fanniasl - @FarzinKazemzadeh")
        print("=" * 60)


        print("1) Start bootstrap - شروع بوت‌استرپ")
        print("2) Download ROM - بارگیری رام (بزودی)")
        print("3) Enable TESTING mode - فعال کردن حالت تست")
        print("4) Exit- خروح")
        print()
        
        choice = input("Choose an option [1-4]: ").strip()
        
        match choice:
            case "1":
                start_downgrade(fastboot)
            # case "2":
            #     download_rom()
            case "3":
                global IS_TESTING 
                IS_TESTING = True
                print("Test mode enabled!")
                sys.exit(0)
            case "4":
                print("Goodbye!")
                sys.exit(0)
            case _:
                print("Invalid choice.")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        sys.exit(1)