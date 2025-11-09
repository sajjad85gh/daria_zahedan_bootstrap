@echo off
echo ======================================
echo   DariaOS 5 Downgrade Flash Script
echo ======================================

:: Set fastboot path
set "FASTBOOT=platform-tools\fastboot.exe"

:: Check fastboot exists
if not exist "%FASTBOOT%" (
    echo ERROR: %FASTBOOT% not found!
    echo Place this script next to platform-tools folder.
    pause
    exit /b 1
)

:: Check device
echo Checking device...
%FASTBOOT% devices | findstr /r /c:"fastboot" >nul
if %errorlevel% neq 0 (
    echo.
    echo ERROR: No device in fastboot mode!
    echo Run: adb reboot bootloader
    pause
    exit /b 1
)
echo Device detected

:: Partitions list
set "PARTITIONS=boot cam_vpu1 cam_vpu2 cam_vpu3 dpm dtbo gz lk mcupm md1img pi_img preloader scp spmfw sspm tee vbmeta vbmeta_system vbmeta_vendor"

:: Flash super.img
echo.
echo === Flashing super.img (shared) ===
if not exist "ROM\super.img" (
    echo ERROR: ROM\super.img not found!
    pause
    exit /b 1
)
%FASTBOOT% flash super ROM\super.img >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to flash super.img
    pause
    exit /b 1
)
echo super.img flashed

:: Flash to slot B
echo.
echo === Flashing all partitions to slot B ===
for %%P in (%PARTITIONS%) do (
    set "IMG=ROM\%%P.img"
    if not exist "!IMG!" (
        echo.
        echo ERROR: !IMG! not found!
        pause
        exit /b 1
    )
    set "TARGET=%%P_b"
    echo Flashing !TARGET! ^<- !IMG!
    %FASTBOOT% flash !TARGET! "!IMG!" >nul
    if !errorlevel! neq 0 (
        echo.
        echo ERROR: Failed to flash !TARGET!
        pause
        exit /b 1
    )
    echo !TARGET! flashed
)

:: Flash to slot A
echo.
echo === Flashing all partitions to slot A ===
for %%P in (%PARTITIONS%) do (
    set "IMG=ROM\%%P.img"
    if not exist "!IMG!" (
        echo.
        echo ERROR: !IMG! not found!
        pause
        exit /b 1
    )
    set "TARGET=%%P_a"
    echo Flashing !TARGET! ^<- !IMG!
    %FASTBOOT% flash !TARGET! "!IMG!" >nul
    if !errorlevel! neq 0 (
        echo.
        echo ERROR: Failed to flash !TARGET!
        pause
        exit /b 1
    )
    echo !TARGET! flashed
)

:: Set active slot to A
echo.
echo === Setting active slot to A ===
%FASTBOOT% --set-active=a >nul
if %errorlevel% neq 0 (
    echo ERROR: Failed to set active slot to a
    pause
    exit /b 1
)
echo Active slot set to A

:: Final success + reboot
echo.
echo ======================================
echo   ALL PARTITIONS FLASHED ON BOTH SLOTS
echo   super.img: shared
echo   All others: flashed to _a and _b
echo   Final active slot: A
echo   Rebooting in 3 seconds...
echo ======================================
timeout /t 3 >nul
%FASTBOOT% reboot
echo Device rebooted into slot A

:: Credits
echo.
echo --------------------------------------
echo Script by @itis_sajjad
echo Thanks to @FarzinKazemzadeh for guidance
echo --------------------------------------

pause
