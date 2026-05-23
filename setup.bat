@echo off
setlocal EnableDelayedExpansion
title LOWDownloader - Setup
cd /d "%~dp0"

echo.
echo ============================================================
echo   LOWDownloader - Setup
echo ============================================================
echo.

REM --- Python ---
where python >nul 2>nul
if errorlevel 1 (
    echo [ERRO] Python nao encontrado no PATH.
    echo        Instale o Python em https://www.python.org/downloads/
    echo        e marque "Add Python to PATH".
    pause
    exit /b 1
)
echo [ok] Python encontrado.

REM --- yt-dlp via pip ---
echo.
echo [..] Instalando / atualizando yt-dlp via pip...
python -m pip install --upgrade --quiet yt-dlp
if errorlevel 1 (
    echo [ERRO] Falha ao instalar yt-dlp.
    pause
    exit /b 1
)
echo [ok] yt-dlp instalado.

REM --- ffmpeg via imageio-ffmpeg + Pillow (preview de frames) + pywebview ---
echo.
echo [..] Instalando dependencias (imageio-ffmpeg, pillow, pywebview)...
python -m pip install --upgrade --quiet imageio-ffmpeg pillow pywebview
if errorlevel 1 (
    echo [ERRO] Falha ao instalar dependencias.
    pause
    exit /b 1
)

REM valida que o ffmpeg foi baixado
python -c "import imageio_ffmpeg, os, sys; p=imageio_ffmpeg.get_ffmpeg_exe(); sys.exit(0 if os.path.exists(p) else 1)"
if errorlevel 1 (
    echo [ERRO] imageio-ffmpeg instalado mas ffmpeg.exe nao encontrado.
    pause
    exit /b 1
)
echo [ok] ffmpeg pronto.

echo.
echo ============================================================
echo   Setup concluido. Rode "LOWDownloader.bat" para abrir.
echo ============================================================
echo.
pause
