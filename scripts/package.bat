@echo off
:: ============================================================
:: Cursiv - Package Script
:: Compiles installer\cursiv_setup.iss into installer\Output\Cursiv-Setup-*.exe
:: (exact filename comes from cursiv_setup.iss's OutputBaseFilename — this
:: script doesn't hardcode a version, so it won't go stale on the next bump.)
:: Requires Inno Setup 6 (iscc must be in PATH or found below).
:: Run from repo root:  scripts\package.bat
:: ============================================================
setlocal enabledelayedexpansion

set "ROOT=%~dp0.."
cd /d "%ROOT%"

echo.
echo  Cursiv Installer Packager
echo  =========================================
echo.

:: ---- Locate iscc -------------------------------------------
set "ISCC="

where iscc >nul 2>&1
if %errorlevel% equ 0 set "ISCC=iscc"

:: Check Program Files (x86) directly - no for-loop, no nesting
if not defined ISCC (
    set "_T=%ProgramFiles(x86)%\Inno Setup 6\iscc.exe"
    if exist "!_T!" set "ISCC=!_T!"
)

:: Check Program Files (64-bit)
if not defined ISCC (
    set "_T=%ProgramFiles%\Inno Setup 6\iscc.exe"
    if exist "!_T!" set "ISCC=!_T!"
)

:: Check user AppData\Local\Programs (non-admin install)
if not defined ISCC (
    set "_T=%LOCALAPPDATA%\Programs\Inno Setup 6\iscc.exe"
    if exist "!_T!" set "ISCC=!_T!"
)

if not defined ISCC (
    echo [ERROR] Inno Setup 6 compiler ^(iscc^) not found.
    echo.
    echo  Download from: https://jrsoftware.org/isdl.php
    echo  After installing, re-run this script.
    pause & exit /b 1
)
echo  Inno Setup: %ISCC%

:: ---- Check build exists ------------------------------------
if not exist "dist\Cursiv\Cursiv.exe" (
    echo [ERROR] dist\Cursiv\Cursiv.exe not found.
    echo  Run scripts\build.bat first.
    pause & exit /b 1
)

:: ---- Compile installer -------------------------------------
echo  Compiling installer...
echo.
"%ISCC%" "installer\cursiv_setup.iss"
if %errorlevel% neq 0 (
    echo.
    echo [ERROR] Inno Setup compilation failed.
    pause & exit /b 1
)

:: ---- Verify output -------------------------------------------
:: Version-agnostic: finds the most-recently-built Cursiv-Setup-*.exe
:: (sorted by date, not name — Output\ can hold several old versions
:: at once, and a plain name-sorted match can pick the wrong one).
set "OUT_EXE="
for /f "delims=" %%F in ('dir /b /o-d "installer\Output\Cursiv-Setup-*.exe" 2^>nul') do (
    if not defined OUT_EXE set "OUT_EXE=%%F"
)

if not defined OUT_EXE (
    echo [ERROR] No installer found in installer\Output\
    pause & exit /b 1
)

echo.
echo  Installer created!
echo  File: installer\Output\%OUT_EXE%
echo.
pause
