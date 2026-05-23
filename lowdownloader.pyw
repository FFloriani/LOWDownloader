"""
LOWDownloader — Interface Webview Premium via HTML5/CSS3/Tailwind.
Funde a robustez do backend Python (yt-dlp + ffmpeg) com a estética de ponta da Web.
"""
from __future__ import annotations

import base64
import io
import json
import os
import queue
import re
import subprocess
import sys
import threading
import urllib.request
from pathlib import Path

# Fallback amigável caso rode o script sem as dependências instaladas
try:
    import webview
except ImportError:
    try:
        from tkinter import messagebox, Tk
        root = Tk()
        root.withdraw()
        messagebox.showerror(
            "Interface Moderna - Dependência Ausente", 
            "O pacote 'pywebview' não está instalado.\n\n"
            "Por favor, dê um duplo clique no arquivo 'setup.bat' para instalar "
            "automaticamente a nova interface web premium e todas as dependências."
        )
        root.destroy()
    except Exception:
        print("[ERRO] pywebview não está instalado. Por favor, rode setup.bat.")
    sys.exit(1)

APP_DIR = Path(__file__).resolve().parent
BIN_DIR = APP_DIR / "bin"
CACHE_DIR = APP_DIR / ".cache"
DEFAULT_DOWNLOAD_DIR = APP_DIR / "downloads"

# Resolução padrão dos previews
THUMB_W, THUMB_H = 260, 146
MAIN_THUMB_W, MAIN_THUMB_H = 340, 191
CREATIONFLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


def find_yt_dlp() -> str | None:
    try:
        subprocess.run(
            [sys.executable, "-m", "yt_dlp", "--version"],
            capture_output=True, check=True, timeout=10,
        )
        return f'"{sys.executable}" -m yt_dlp'
    except Exception:
        pass
    for name in ("yt-dlp.exe", "yt-dlp"):
        local = APP_DIR / name
        if local.exists():
            return f'"{local}"'
    from shutil import which
    found = which("yt-dlp")
    if found:
        return f'"{found}"'
    return None


def find_ffmpeg() -> str | None:
    local_bin = BIN_DIR / "ffmpeg.exe"
    if local_bin.exists():
        return str(local_bin)
    try:
        import imageio_ffmpeg
        path = imageio_ffmpeg.get_ffmpeg_exe()
        if path and Path(path).exists():
            return path
    except Exception:
        pass
    from shutil import which
    return which("ffmpeg")


def get_windows_clipboard() -> str:
    """Captura o texto da área de transferência do Windows via Win32 API pura."""
    if sys.platform != "win32":
        return ""
    import ctypes
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
    if not user32.OpenClipboard(None):
        return ""
    try:
        if user32.IsClipboardFormatAvailable(13):  # CF_UNICODETEXT
            h = user32.GetClipboardData(13)
            p = kernel32.GlobalLock(h)
            try:
                text = ctypes.c_wchar_p(p).value
            finally:
                kernel32.GlobalUnlock(h)
            return text or ""
    finally:
        user32.CloseClipboard()
    return ""


def parse_time_to_seconds(text: str) -> int | None:
    text = text.strip()
    if not text:
        return None
    parts = text.split(":")
    try:
        parts = [int(p) for p in parts]
    except ValueError:
        return None
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return parts[0] * 60 + parts[1]
    if len(parts) == 3:
        return parts[0] * 3600 + parts[1] * 60 + parts[2]
    return None


def fmt_hms(seconds: float) -> str:
    seconds = max(0, int(seconds))
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


def format_duration(seconds: float) -> str:
    seconds = int(seconds)
    h, rem = divmod(seconds, 3600)
    m, s = divmod(rem, 60)
    if h:
        return f"{h}h {m:02d}m {s:02d}s"
    return f"{m}m {s:02d}s"


# =====================================================================
# INTERFACE ULTRA-MODERNA FUTURISTA DE RETRO-ALIMENTAÇÃO COSMICA
# =====================================================================
HTML_CONTENT = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LOWDownloader Pro — Espelho do Universo</title>
    <link href="https://fonts.googleapis.com/css2?family=Orbitron:wght@400;600;700;800;900&family=Inter:wght@300;400;500;600;700&display=swap" rel="stylesheet">
    <style>
        :root {
            --bg:       #050507;
            --panel:    rgba(8,6,18,0.78);
            --border:   rgba(139,0,255,0.18);
            --purple:   #A020F0;
            --violet:   #8B00FF;
            --magenta:  #FF00FF;
            --gold:     #FFD700;
            --gold2:    #FFA500;
            --cyan:     #00E5FF;
            --text:     #EDE9FE;
            --muted:    #7C6FAE;
        }
        * { box-sizing: border-box; margin: 0; padding: 0; }
        html, body { height: 100%; overflow: hidden; }
        body {
            font-family: 'Inter', sans-serif;
            background: var(--bg);
            color: var(--text);
            user-select: none;
        }
        /* CANVAS */
        #stars-canvas {
            position: fixed; inset: 0;
            pointer-events: none; z-index: 0;
        }
        /* NEBULAE */
        .nbl { position: fixed; border-radius: 50%; pointer-events: none; z-index: 1; filter: blur(120px); }
        .nbl-1 { width:80vw; height:70vh; top:-22vh; left:-18vw;
            background:radial-gradient(circle,rgba(139,0,255,.15) 0%,transparent 70%);
            animation:nbl 24s ease-in-out infinite alternate; }
        .nbl-2 { width:70vw; height:65vh; bottom:-28vh; right:-12vw;
            background:radial-gradient(circle,rgba(255,0,255,.10) 0%,rgba(139,0,255,.05) 55%,transparent 70%);
            animation:nbl 30s ease-in-out infinite alternate-reverse; }
        .nbl-3 { width:45vw; height:45vh; top:38vh; left:33vw;
            background:radial-gradient(circle,rgba(0,229,255,.05) 0%,transparent 70%);
            animation:nbl 38s ease-in-out infinite alternate; }
        @keyframes nbl {
            0%   { transform:scale(1) translate(0,0) rotate(0deg); opacity:.9; }
            100% { transform:scale(1.28) translate(4vw,3vh) rotate(45deg); opacity:1; }
        }
        /* SCROLLBAR */
        ::-webkit-scrollbar { width: 4px; }
        ::-webkit-scrollbar-track { background: rgba(5,5,10,.5); }
        ::-webkit-scrollbar-thumb { background:rgba(139,0,255,.3); border-radius:9999px; }

        /* ── GLASS ── */
        .glass {
            background: var(--panel);
            backdrop-filter: blur(32px) saturate(1.5);
            -webkit-backdrop-filter: blur(32px) saturate(1.5);
            border: 1px solid var(--border);
            border-radius: 20px;
            box-shadow: 0 8px 44px rgba(0,0,0,.6),
                        inset 0 1px 0 rgba(255,255,255,.045);
            position: relative; overflow: hidden;
            transition: border-color .4s, box-shadow .4s, transform .3s cubic-bezier(.16,1,.3,1);
        }
        .glass::before {
            content:''; position:absolute; inset:0; pointer-events:none; z-index:0;
            background:linear-gradient(135deg,rgba(255,0,255,.05) 0%,transparent 55%,rgba(139,0,255,.045) 100%);
            opacity:0; transition:opacity .4s;
        }
        .glass:hover::before { opacity:1; }
        .glass:hover {
            border-color: rgba(160,32,240,.38);
            box-shadow: 0 12px 52px rgba(160,32,240,.22),
                        0 0 22px rgba(160,32,240,.09),
                        inset 0 1px 0 rgba(255,255,255,.075);
            transform: translateY(-1px);
        }
        .glass > * { position: relative; z-index: 1; }

        /* ── TYPOGRAPHY ── */
        .orb { font-family:'Orbitron',sans-serif; }
        .grad-cosmic {
            background:linear-gradient(90deg,#C026FF 0%,#FF00FF 40%,#A020F0 70%,#C026FF 100%);
            background-size:220%; -webkit-background-clip:text;
            -webkit-text-fill-color:transparent; background-clip:text;
            animation:shimmer 4s linear infinite;
        }
        .grad-gold {
            background:linear-gradient(90deg,#FFD700 0%,#FFA500 40%,#FFD700 100%);
            background-size:200%; -webkit-background-clip:text;
            -webkit-text-fill-color:transparent; background-clip:text;
            animation:shimmer 3s linear infinite;
        }
        @keyframes shimmer { 0%{background-position:0%} 100%{background-position:220%} }

        /* ── SEC LABEL ── */
        .sec {
            font-size:8.5px; font-weight:800; letter-spacing:.18em;
            text-transform:uppercase; color:var(--muted);
            display:flex; align-items:center; gap:7px; margin-bottom:10px;
        }
        .sec::before {
            content:''; flex:0 0 3px; height:13px; border-radius:9999px;
            background:linear-gradient(to bottom,var(--purple),var(--magenta));
        }

        /* ── INPUTS ── */
        .inp {
            width:100%; background:rgba(0,0,0,.6);
            border:1px solid rgba(139,0,255,.22);
            border-radius:12px; padding:10px 14px;
            font-size:11.5px; font-weight:500; color:var(--text);
            outline:none; font-family:'Inter',sans-serif;
            transition:border-color .25s,box-shadow .25s;
        }
        .inp::placeholder { color:var(--muted); }
        .inp:focus {
            border-color:rgba(160,32,240,.7);
            box-shadow:0 0 0 3px rgba(160,32,240,.13),0 0 20px rgba(160,32,240,.14);
        }
        select.inp { cursor:pointer; appearance:none; }
        .inp-mono { font-family:'Orbitron',sans-serif; font-size:10px; text-align:center; }

        /* ── TOGGLE ── */
        .tog-wrap { display:flex; align-items:center; gap:10px; cursor:pointer; }
        .tog-track {
            position:relative; width:38px; height:21px; flex-shrink:0;
            background:rgba(0,0,0,.65); border:1px solid rgba(139,0,255,.3);
            border-radius:9999px; transition:background .25s,border-color .25s;
        }
        .tog-track::after {
            content:''; position:absolute; top:2px; left:2px;
            width:15px; height:15px; border-radius:50%;
            background:#6B7280; transition:transform .25s,background .25s,box-shadow .25s;
        }
        .tog-on { background:linear-gradient(90deg,var(--violet),var(--magenta)); border-color:rgba(255,0,255,.55); }
        .tog-on::after { transform:translateX(17px); background:#fff; box-shadow:0 0 12px rgba(255,0,255,.7); }

        /* ── BUTTONS ── */
        .btn {
            display:inline-flex; align-items:center; justify-content:center; gap:7px;
            border-radius:12px; border:none; cursor:pointer;
            font-family:'Inter',sans-serif; font-weight:700; font-size:12px;
            padding:9px 16px;
            transition:transform .2s cubic-bezier(.34,1.56,.64,1),box-shadow .3s;
        }
        .btn:active { transform:scale(.96) !important; }
        .btn-ghost {
            background:rgba(255,255,255,.06);
            border:1px solid rgba(255,255,255,.1);
            color:rgba(255,255,255,.75);
        }
        .btn-ghost:hover { background:rgba(160,32,240,.15); border-color:rgba(160,32,240,.4); color:#fff; transform:scale(1.03); }
        .btn-primary {
            background:linear-gradient(135deg,#6C00CC,#A020F0 50%,#C026FF);
            color:#fff; box-shadow:0 4px 22px rgba(160,32,240,.38);
        }
        .btn-primary:hover { box-shadow:0 6px 30px rgba(160,32,240,.58); transform:scale(1.04); }
        /* SSR / GOLD */
        .btn-ssr {
            background:linear-gradient(135deg,#7B4F00,#C98000 30%,#FFD700 55%,#C98000 80%,#7B4F00);
            background-size:220% 100%;
            color:#050507; font-weight:900;
            font-family:'Orbitron',sans-serif; font-size:13px; letter-spacing:.10em;
            border:1px solid rgba(255,215,0,.45);
            box-shadow:0 0 22px rgba(255,215,0,.38),0 6px 32px rgba(255,140,0,.28),
                       inset 0 1px 0 rgba(255,255,255,.28);
            position:relative; overflow:hidden;
            animation:ssr-breathe 2.8s ease-in-out infinite, ssr-shim 3s linear infinite;
        }
        .btn-ssr::before {
            content:''; position:absolute; inset:0;
            background:linear-gradient(90deg,transparent 0%,rgba(255,255,255,.24) 50%,transparent 100%);
            transform:translateX(-130%); animation:sheen 3s ease-in-out infinite;
        }
        .btn-ssr:hover { transform:scale(1.04) translateY(-2px); box-shadow:0 0 38px rgba(255,215,0,.65),0 10px 44px rgba(255,140,0,.44),inset 0 1px 0 rgba(255,255,255,.38); }
        .btn-ssr:disabled { animation:none; opacity:.52; cursor:not-allowed; transform:none; box-shadow:0 2px 10px rgba(0,0,0,.4); }
        .btn-cancel { background:rgba(220,38,38,.12); border:1px solid rgba(220,38,38,.28); color:#F87171; }
        .btn-cancel:hover:not(:disabled) { background:rgba(220,38,38,.24); border-color:rgba(220,38,38,.6); transform:scale(1.03); }
        .btn-cancel:disabled { opacity:.22; cursor:not-allowed; }
        @keyframes ssr-breathe {
            0%,100% { box-shadow:0 0 22px rgba(255,215,0,.38),0 6px 32px rgba(255,140,0,.28),inset 0 1px 0 rgba(255,255,255,.28); }
            50%      { box-shadow:0 0 42px rgba(255,215,0,.68),0 8px 42px rgba(255,140,0,.48),inset 0 1px 0 rgba(255,255,255,.38); }
        }
        @keyframes ssr-shim { 0%{background-position:220% 0} 100%{background-position:-220% 0} }
        @keyframes sheen { 0%{transform:translateX(-130%)} 60%,100%{transform:translateX(220%)} }

        /* ── PROGRESS ── */
        .prog-track {
            width:100%; height:10px; border-radius:9999px;
            background:rgba(0,0,0,.7); border:1px solid rgba(139,0,255,.2);
            padding:2px; overflow:hidden;
        }
        .prog-fill {
            height:100%; border-radius:9999px; width:0%;
            background:linear-gradient(90deg,#6C00CC,#A020F0,#FF00FF,#FFD700);
            background-size:220% 100%;
            transition:width .35s cubic-bezier(.4,0,.2,1);
            box-shadow:0 0 16px rgba(255,0,255,.6),0 0 7px rgba(255,215,0,.3);
            animation:prog-shim 2s linear infinite; position:relative;
        }
        .prog-fill::after {
            content:''; position:absolute; right:-3px; top:50%; transform:translateY(-50%);
            width:8px; height:8px; border-radius:50%;
            background:#FFD700; box-shadow:0 0 14px #FFD700,0 0 6px #fff;
        }
        @keyframes prog-shim { 0%{background-position:220% 0} 100%{background-position:-220% 0} }

        /* ── RANGE SLIDER ── */
        input[type="range"] { -webkit-appearance:none; appearance:none; background:transparent; cursor:pointer; height:20px; width:100%; }
        input[type="range"]::-webkit-slider-runnable-track {
            background:rgba(0,0,0,.75); border:1px solid rgba(139,0,255,.2);
            height:5px; border-radius:9999px;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance:none; margin-top:-6px;
            width:16px; height:16px; border-radius:50%;
            background:linear-gradient(135deg,#FFD700,#FF8C00);
            box-shadow:0 0 13px rgba(255,215,0,.75),0 0 5px rgba(255,140,0,.55);
            transition:transform .18s cubic-bezier(.34,1.56,.64,1),box-shadow .18s;
        }
        input[type="range"]::-webkit-slider-thumb:hover { transform:scale(1.38); box-shadow:0 0 22px rgba(255,215,0,.95),0 0 9px rgba(255,0,255,.45); }

        /* ── HUD CONSOLE ── */
        .hud {
            background:rgba(0,0,0,.78); border:1px solid rgba(139,0,255,.2);
            border-radius:14px; position:relative; overflow:hidden;
        }
        .hud::before {
            content:''; position:absolute; inset:0; pointer-events:none; z-index:2;
            background:repeating-linear-gradient(0deg,rgba(0,0,0,.14) 0px,rgba(0,0,0,.14) 1px,transparent 1px,transparent 3px);
        }
        .hud-log { position:relative; z-index:3; }
        .log-ok   { color:#34D399; font-weight:600; }
        .log-err  { color:#F87171; font-weight:700; }
        .log-cmd  { color:#22D3EE; font-weight:600; }
        .log-info { color:rgba(196,181,253,.72); }

        /* ── THUMBNAIL FRAME ── */
        .thumb-frame {
            position:relative; border-radius:16px; overflow:hidden;
            border:1px solid rgba(160,32,240,.22); background:#000;
        }
        .thumb-frame::after {
            content:''; position:absolute; inset:0; pointer-events:none; z-index:2;
            background:linear-gradient(to top,rgba(5,5,7,.88) 0%,transparent 45%);
        }
        .ch { position:absolute; z-index:3; pointer-events:none; }
        .ch-tl { top:8px;left:8px; width:18px;height:18px; border-top:2px solid rgba(139,0,255,.65); border-left:2px solid rgba(139,0,255,.65); border-radius:3px 0 0 0; transition:border-color .3s; }
        .ch-tr { top:8px;right:8px; width:18px;height:18px; border-top:2px solid rgba(139,0,255,.65); border-right:2px solid rgba(139,0,255,.65); border-radius:0 3px 0 0; transition:border-color .3s; }
        .ch-bl { bottom:8px;left:8px; width:18px;height:18px; border-bottom:2px solid rgba(139,0,255,.65); border-left:2px solid rgba(139,0,255,.65); border-radius:0 0 0 3px; transition:border-color .3s; }
        .ch-br { bottom:8px;right:8px; width:18px;height:18px; border-bottom:2px solid rgba(139,0,255,.65); border-right:2px solid rgba(139,0,255,.65); border-radius:0 0 3px 0; transition:border-color .3s; }
        .thumb-frame:hover .ch-tl,.thumb-frame:hover .ch-tr,.thumb-frame:hover .ch-bl,.thumb-frame:hover .ch-br { border-color:rgba(255,215,0,.95); }
        .thumb-frame img { display:block; width:100%; height:100%; object-fit:cover; transition:transform .6s cubic-bezier(.4,0,.2,1); }
        .thumb-frame:hover img { transform:scale(1.04); }

        /* ── PULSE DOT ── */
        .pdot { width:7px;height:7px;border-radius:50%;flex-shrink:0;animation:pdot 2s ease-out infinite; }
        .pdot-gold   { background:#FFD700;box-shadow:0 0 8px #FFD700; }
        .pdot-purple { background:#C026FF;box-shadow:0 0 8px #C026FF; }
        .pdot-pink   { background:#FF00FF;box-shadow:0 0 8px #FF00FF; }
        .pdot-green  { background:#34D399;box-shadow:0 0 8px #34D399; }
        @keyframes pdot { 0%,100%{opacity:1} 50%{opacity:.38} }

        /* ── CHIP ── */
        .chip {
            display:inline-flex;align-items:center;gap:3px;
            font-size:8px;font-weight:900;letter-spacing:.12em;text-transform:uppercase;
            padding:2px 9px;border-radius:9999px;
            background:linear-gradient(90deg,rgba(139,0,255,.18),rgba(255,0,255,.12));
            border:1px solid rgba(255,0,255,.28);color:#E879F9;
        }

        /* ── LOGO CONTAINER ANIMATION ── */
        @keyframes logo-container-glow {
            0%, 100% {
                box-shadow: 0 0 20px rgba(160,32,240,.25), 0 0 0px rgba(255,0,255,0);
                border-color: rgba(160,32,240,.48);
            }
            50% {
                box-shadow: 0 0 32px rgba(160,32,240,.6), 0 0 14px rgba(255,0,255,.45);
                border-color: rgba(255,0,255,.9);
            }
        }
        @keyframes logo-rotate {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        #logo-container:hover {
            cursor: pointer;
            box-shadow: 0 0 40px rgba(255,0,255,.75), 0 0 18px rgba(139,0,255,.55) !important;
        }
    </style>
</head>
<body>

<!-- CANVAS STARS -->
<canvas id="stars-canvas" style="position:fixed;inset:0;width:100%;height:100%;pointer-events:none;z-index:0;"></canvas>

<!-- NEBULAE -->
<div class="nbl nbl-1"></div>
<div class="nbl nbl-2"></div>
<div class="nbl nbl-3"></div>

<!-- APP SHELL -->
<div style="position:relative;z-index:10;height:100vh;display:flex;flex-direction:column;padding:14px 18px;gap:12px;overflow:hidden;">

    <!-- HEADER -->
    <header style="display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
        <div style="display:flex;align-items:center;gap:12px;">
            <div id="logo-container" style="width:42px;height:42px;border-radius:14px;flex-shrink:0;
                background:#050507;
                border:1px solid rgba(160,32,240,.48);
                box-shadow:0 0 20px rgba(160,32,240,.25);
                display:flex;align-items:center;justify-content:center;position:relative;
                animation:logo-container-glow 3s ease-in-out infinite;">
                <div style="position:absolute;inset:0;border-radius:14px;
                    border:1px dashed rgba(255,0,255,.35);animation:logo-rotate 18s linear infinite;
                    pointer-events:none;"></div>
                {{LOGO_IMAGE}}
            </div>
            <div>
                <h1 class="orb" style="font-size:clamp(15px,2.2vw,21px);font-weight:900;line-height:1;">
                    <span class="grad-cosmic">LOWDOWNLOADER</span>
                </h1>
                <p style="font-size:9.5px;color:var(--muted);margin-top:3px;font-weight:500;letter-spacing:.05em;">
                    Motor de extração cósmica de mídia em alta fidelidade
                </p>
            </div>
        </div>
        <div id="dep-badge" style="display:flex;align-items:center;gap:7px;
            background:rgba(0,0,0,.58);border:1px solid rgba(139,0,255,.28);
            border-radius:12px;padding:7px 14px;flex-shrink:0;">
            <span class="pdot pdot-gold"></span>
            <span class="orb" style="font-size:9.5px;font-weight:700;color:#C084FC;letter-spacing:.06em;">yt-dlp + ffmpeg</span>
        </div>
    </header>

    <!-- 2-COL MAIN -->
    <div style="display:grid;grid-template-columns:1fr 400px;gap:12px;flex:1;min-height:0;overflow:hidden;">

        <!-- LEFT COLUMN -->
        <div style="display:flex;flex-direction:column;gap:10px;overflow-y:auto;padding-right:3px;">

            <!-- URL -->
            <div class="glass" style="padding:14px 16px;">
                <div class="sec">
                    <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M13.19 8.688a4.5 4.5 0 011.242 7.244l-4.5 4.5a4.5 4.5 0 01-6.364-6.364l1.757-1.757m13.35-.622l1.757-1.757a4.5 4.5 0 00-6.364-6.364l-4.5 4.5a4.5 4.5 0 001.242 7.244"/></svg>
                    Fluxo Cósmico — URL de Entrada
                </div>
                <div style="display:flex;gap:8px;align-items:center;">
                    <input type="text" id="url-input" class="inp"
                        placeholder="Cole a URL (YouTube, Twitch, Twitter/X, Facebook…)"
                        style="flex:1;">
                    <button class="btn btn-ghost" onclick="pasteClipboard()" style="flex-shrink:0;white-space:nowrap;">
                        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"/></svg>
                        Colar
                    </button>
                    <button id="verify-btn" class="btn btn-primary" onclick="verifyUrl()" style="flex-shrink:0;min-width:108px;white-space:nowrap;">
                        <svg width="13" height="13" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/></svg>
                        <span id="verify-label">VERIFICAR</span>
                    </button>
                </div>
            </div>

            <!-- SETTINGS -->
            <div class="glass" style="padding:14px 16px;">
                <div class="sec">
                    <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"/></svg>
                    Parâmetros de Extração
                </div>
                <div style="display:grid;grid-template-columns:1fr 1fr;gap:10px 14px;">
                    <!-- Quality -->
                    <div>
                        <div style="font-size:8.5px;font-weight:800;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin-bottom:7px;display:flex;align-items:center;gap:5px;">
                            <span class="pdot pdot-purple" style="width:5px;height:5px;"></span>Resolução
                        </div>
                        <div style="position:relative;">
                            <svg style="position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none;" width="12" height="12" fill="none" stroke="rgba(160,32,240,.8)" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z"/></svg>
                            <select id="quality-select" class="inp" style="padding-left:30px;padding-right:26px;">
                                <option value="Melhor (Source)">&#9733; Melhor (Source)</option>
                                <option value="1080p">1080p Full HD</option>
                                <option value="720p">720p HD</option>
                                <option value="480p">480p SD</option>
                                <option value="360p">360p</option>
                                <option value="Pior (rapido)">&#9889; Rapido (menor)</option>
                            </select>
                            <svg style="position:absolute;right:9px;top:50%;transform:translateY(-50%);pointer-events:none;" width="10" height="10" fill="none" stroke="rgba(139,0,255,.6)" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/></svg>
                        </div>
                    </div>
                    <!-- Cookies -->
                    <div>
                        <div style="font-size:8.5px;font-weight:800;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;margin-bottom:7px;display:flex;align-items:center;gap:5px;">
                            <span class="pdot pdot-purple" style="width:5px;height:5px;"></span>Cookies / Sessao
                        </div>
                        <div style="position:relative;">
                            <svg style="position:absolute;left:11px;top:50%;transform:translateY(-50%);pointer-events:none;" width="12" height="12" fill="none" stroke="rgba(160,32,240,.8)" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 5.25a3 3 0 013 3m3 0a6 6 0 01-7.029 5.912c-.563-.097-1.159.026-1.563.43L10.5 17.25H8.25v2.25H6v2.25H2.25v-2.818c0-.597.237-1.17.659-1.591l6.499-6.499c.404-.404.527-.996.43-1.563A6 6 0 1121.75 8.25z"/></svg>
                            <select id="cookies-select" class="inp" style="padding-left:30px;padding-right:26px;">
                                <option value="Nenhum">Nenhum (Livre)</option>
                                <option value="cookies.txt (Local)">cookies.txt (Local)</option>
                                <option value="Chrome">Chrome</option>
                                <option value="Firefox">Firefox</option>
                                <option value="Edge">Edge</option>
                                <option value="Brave">Brave</option>
                                <option value="Opera">Opera</option>
                                <option value="Vivaldi">Vivaldi</option>
                                <option value="Chromium">Chromium</option>
                                <option value="Safari">Safari</option>
                            </select>
                            <svg style="position:absolute;right:9px;top:50%;transform:translateY(-50%);pointer-events:none;" width="10" height="10" fill="none" stroke="rgba(139,0,255,.6)" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/></svg>
                        </div>
                    </div>
                    <!-- Toggles -->
                    <div style="grid-column:1/-1;display:flex;gap:22px;align-items:center;padding-top:10px;border-top:1px solid rgba(139,0,255,.12);margin-top:2px;">
                        <label class="tog-wrap" id="tog-audio">
                            <input type="checkbox" id="audio-only-toggle" style="display:none;">
                            <div class="tog-track" id="trk-audio"></div>
                            <div style="display:flex;align-items:center;gap:6px;">
                                <svg width="12" height="12" fill="none" stroke="rgba(196,181,253,.75)" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M9 19V6l12-3v13M9 19c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zm12-3c0 1.105-1.343 2-3 2s-3-.895-3-2 1.343-2 3-2 3 .895 3 2zM9 10l12-3"/></svg>
                                <span style="font-size:11px;font-weight:600;color:rgba(237,233,254,.88);">So Audio (MP3)</span>
                            </div>
                        </label>
                        <label class="tog-wrap" id="tog-wa">
                            <input type="checkbox" id="whatsapp-toggle" style="display:none;">
                            <div class="tog-track" id="trk-wa"></div>
                            <div style="display:flex;align-items:center;gap:6px;">
                                <svg width="12" height="12" fill="none" stroke="rgba(196,181,253,.75)" stroke-width="2" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M20.25 8.511c.884.284 1.5 1.128 1.5 2.097v4.286c0 1.136-.847 2.1-1.98 2.193-.34.027-.68.052-1.02.072v3.091l-3-3c-1.354 0-2.694-.055-4.02-.163a2.115 2.115 0 01-.825-.242m9.345-8.334a2.126 2.126 0 00-.476-.095 48.64 48.64 0 00-8.048 0c-1.131.094-1.976 1.057-1.976 2.192v4.286c0 .837.46 1.58 1.155 1.951m9.345-8.334V6.637c0-1.621-1.152-3.026-2.76-3.235A48.455 48.455 0 0011.25 3c-2.115 0-4.198.137-6.24.402-1.608.209-2.76 1.614-2.76 3.235v6.226c0 1.621 1.152 3.026 2.76 3.235.577.075 1.157.14 1.74.194V21l4.155-4.155"/></svg>
                                <span style="font-size:11px;font-weight:600;color:rgba(237,233,254,.88);">Otimizar WhatsApp</span>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <!-- DESTINATION -->
            <div class="glass" style="padding:12px 16px;">
                <div class="sec">
                    <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z"/></svg>
                    Destino de Exportacao
                </div>
                <div style="display:flex;gap:8px;align-items:center;">
                    <input type="text" id="dest-input" class="inp" readonly
                        style="flex:1;color:var(--muted);font-size:11px;cursor:default;">
                    <button class="btn btn-ghost" onclick="chooseDirectory()" style="flex-shrink:0;">Mudar</button>
                    <button class="btn btn-ghost" onclick="openDirectory()" style="flex-shrink:0;">Abrir</button>
                </div>
            </div>

            <!-- DOWNLOAD ACTION -->
            <div class="glass" style="padding:14px 16px;">
                <button id="download-btn" class="btn btn-ssr" onclick="startDownload()"
                    style="width:100%;padding:13px;font-size:13px;gap:10px;margin-bottom:12px;border-radius:14px;">
                    <svg width="17" height="17" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round"
                              d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12M12 16.5V3"/>
                    </svg>
                    &#10022; INICIAR DOWNLOAD &#10022;
                </button>
                <button id="cancel-btn" class="btn btn-cancel" onclick="cancelDownload()" disabled
                    style="width:100%;padding:9px;margin-bottom:11px;border-radius:12px;">
                    Cancelar Operacao
                </button>
                <div class="prog-track" style="margin-bottom:7px;">
                    <div id="progress-bar" class="prog-fill" style="width:0%;"></div>
                </div>
                <div id="progress-text" class="orb"
                    style="font-size:8.5px;font-weight:600;color:var(--muted);letter-spacing:.12em;text-transform:uppercase;text-align:center;">
                    -- PRONTO PARA OPERACAO --
                </div>
            </div>

            <!-- HUD CONSOLE -->
            <div style="flex:1;display:flex;flex-direction:column;min-height:100px;">
                <div class="sec" style="margin-bottom:8px;">
                    <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M17.25 6.75L22.5 12l-5.25 5.25m-10.5 0L1.5 12l5.25-5.25m7.5-3l-4.5 16.5"/></svg>
                    Console HUD
                </div>
                <div class="hud" style="flex:1;overflow:hidden;display:flex;flex-direction:column;">
                    <div id="log-console" class="hud-log"
                        style="flex:1;overflow-y:auto;padding:10px 13px;
                               font-family:'Courier New',monospace;font-size:9.5px;
                               line-height:1.7;display:flex;flex-direction:column;gap:1px;">
                    </div>
                </div>
            </div>

        </div>

        <!-- RIGHT COLUMN -->
        <div style="display:flex;flex-direction:column;gap:10px;overflow:hidden;">
            <div class="glass" style="padding:14px 16px;flex:1;display:flex;flex-direction:column;gap:11px;overflow-y:auto;">

                <div class="sec" style="margin-bottom:0;">
                    <svg width="11" height="11" fill="none" stroke="currentColor" stroke-width="2.5" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.409a2.25 2.25 0 013.182 0l2.909 2.909m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"/></svg>
                    Painel de Telemetria Visual
                </div>

                <!-- THUMBNAIL -->
                <div class="thumb-frame" style="width:100%;aspect-ratio:16/9;flex-shrink:0;">
                    <div class="ch ch-tl"></div><div class="ch ch-tr"></div>
                    <div class="ch ch-bl"></div><div class="ch ch-br"></div>
                    <img id="main-thumb" style="width:100%;height:100%;object-fit:cover;">
                </div>

                <!-- META -->
                <div style="padding-bottom:11px;border-bottom:1px solid rgba(139,0,255,.14);">
                    <div id="video-title"
                        style="font-size:12.5px;font-weight:700;color:#EDE9FE;line-height:1.38;
                               overflow:hidden;display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;
                               margin-bottom:5px;">--</div>
                    <div id="video-meta"
                        style="font-size:9.5px;font-weight:600;color:var(--muted);
                               letter-spacing:.06em;text-transform:uppercase;">
                        Insira uma URL e clique em Verificar.
                    </div>
                </div>

                <!-- SMART CUT TOGGLE -->
                <div style="display:flex;align-items:center;justify-content:space-between;flex-shrink:0;">
                    <div style="display:flex;align-items:center;gap:7px;">
                        <svg width="13" height="13" fill="none" stroke="rgba(196,181,253,.82)" stroke-width="2.5" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" d="M7.848 8.25l1.536.887M7.848 8.25a3 3 0 11-5.196-3 3 3 0 015.196 3zm1.536.887a2.165 2.165 0 011.083 1.839c.005.351.054.695.14 1.024M9.384 9.137l2.077 1.199M7.848 15.75l1.536-.887m-1.536.887a3 3 0 11-5.196 3 3 3 0 015.196-3zm1.536-.887a2.165 2.165 0 001.083-1.838c.005-.352.054-.695.14-1.025m-1.223 2.863l2.077-1.199m0-3.328a4.323 4.323 0 012.068-1.379l5.325-1.628a4.5 4.5 0 012.48-.044l.803.215-7.794 4.5m-2.882-1.664A4.331 4.331 0 0010.607 12m3.736 0l7.794 4.5-.802.215a4.5 4.5 0 01-2.48-.043l-5.326-1.629a4.324 4.324 0 01-2.068-1.379M14.343 12l-2.882 1.664"/>
                        </svg>
                        <span style="font-size:11px;font-weight:700;color:rgba(237,233,254,.92);letter-spacing:.04em;">Corte Inteligente</span>
                        <span class="chip">BETA</span>
                    </div>
                    <label class="tog-wrap" id="tog-cut">
                        <input type="checkbox" id="cut-toggle" onchange="toggleCut()" style="display:none;">
                        <div class="tog-track" id="trk-cut"></div>
                    </label>
                </div>

                <!-- CUT WORKSPACE -->
                <div id="cut-workspace" style="display:none;gap:9px;flex-direction:column;flex-shrink:0;">
                    <div style="display:grid;grid-template-columns:1fr 1fr;gap:9px;">

                        <!-- START -->
                        <div style="background:rgba(0,0,0,.48);border:1px solid rgba(139,0,255,.22);
                            border-radius:14px;padding:10px;display:flex;flex-direction:column;gap:8px;">
                            <div style="display:flex;align-items:center;justify-content:space-between;">
                                <span style="font-size:8.5px;font-weight:800;color:#A78BFA;
                                    letter-spacing:.14em;text-transform:uppercase;
                                    display:flex;align-items:center;gap:5px;">
                                    <span class="pdot pdot-purple" style="width:6px;height:6px;"></span>Inicio
                                </span>
                                <input type="text" id="start-input" onchange="onInputChange('start')"
                                    class="inp inp-mono"
                                    style="width:66px;padding:4px 6px;font-size:9.5px;border-radius:8px;">
                            </div>
                            <input type="range" id="start-slider" min="0" max="100" value="0"
                                oninput="onSliderChange('start', this.value)">
                            <div style="width:100%;aspect-ratio:16/9;border-radius:10px;overflow:hidden;
                                border:1px solid rgba(139,0,255,.2);background:#000;">
                                <img id="start-thumb" style="width:100%;height:100%;object-fit:cover;">
                            </div>
                        </div>

                        <!-- END -->
                        <div style="background:rgba(0,0,0,.48);border:1px solid rgba(255,0,255,.2);
                            border-radius:14px;padding:10px;display:flex;flex-direction:column;gap:8px;">
                            <div style="display:flex;align-items:center;justify-content:space-between;">
                                <span style="font-size:8.5px;font-weight:800;color:#F0ABFC;
                                    letter-spacing:.14em;text-transform:uppercase;
                                    display:flex;align-items:center;gap:5px;">
                                    <span class="pdot pdot-pink" style="width:6px;height:6px;"></span>Fim
                                </span>
                                <input type="text" id="end-input" onchange="onInputChange('end')"
                                    class="inp inp-mono"
                                    style="width:66px;padding:4px 6px;font-size:9.5px;border-radius:8px;">
                            </div>
                            <input type="range" id="end-slider" min="0" max="100" value="100"
                                oninput="onSliderChange('end', this.value)">
                            <div style="width:100%;aspect-ratio:16/9;border-radius:10px;overflow:hidden;
                                border:1px solid rgba(255,0,255,.2);background:#000;">
                                <img id="end-thumb" style="width:100%;height:100%;object-fit:cover;">
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        </div>

    </div>
</div>

<script>
// ── CANVAS STARS + COMETS ──────────────────────────────────────────
const canvas = document.getElementById('stars-canvas');
const ctx    = canvas.getContext('2d');
let stars = [], comets = [];
let mouse = { x:null, y:null, tx:null, ty:null };

window.addEventListener('mousemove', e => { mouse.tx = e.clientX; mouse.ty = e.clientY; });
window.addEventListener('mouseleave', () => { mouse.tx = null; mouse.ty = null; });

function resize() { canvas.width=innerWidth; canvas.height=innerHeight; initAll(); }

class Star {
    constructor(fresh) {
        this.bx = Math.random()*canvas.width;
        this.by = fresh ? Math.random()*canvas.height : canvas.height+4;
        this.x=this.bx; this.y=this.by;
        this.r = Math.random()*1.4+.3;
        this.a = Math.random()*.7+.1;
        this.vy = Math.random()*.06+.01;
        this.fa = Math.random()*.007+.002;
        this.grow = Math.random()>.5;
    }
    update() {
        this.grow?(this.a+=this.fa):(this.a-=this.fa);
        if(this.a>.88)this.grow=false; if(this.a<.08)this.grow=true;
        this.by-=this.vy;
        if(this.by<-2){this.bx=Math.random()*canvas.width;this.by=canvas.height+4;this.x=this.bx;this.y=this.by;}
        if(mouse.x!==null){
            const dx=mouse.x-this.bx,dy=mouse.y-this.by,d=Math.hypot(dx,dy);
            if(d<185){const f=((185-d)/185)*22;this.x=this.bx+(dx/d)*f;this.y=this.by+(dy/d)*f;}
            else{this.x+=(this.bx-this.x)*.08;this.y+=(this.by-this.y)*.08;}
        }else{this.x+=(this.bx-this.x)*.08;this.y+=(this.by-this.y)*.08;}
    }
    draw() {
        ctx.save();ctx.fillStyle=`rgba(196,181,253,${this.a})`;
        ctx.shadowColor='#A020F0';ctx.shadowBlur=this.r*6;
        ctx.beginPath();ctx.arc(this.x,this.y,this.r,0,Math.PI*2);ctx.fill();ctx.restore();
    }
}
class Comet {
    constructor(){this.reset();}
    reset(){
        this.x=Math.random()*canvas.width*.6;this.y=Math.random()*canvas.height*.35;
        this.len=Math.random()*100+60;this.spd=Math.random()*14+7;
        this.ang=Math.PI/6+(Math.random()-.5)*.4;
        this.dx=Math.cos(this.ang)*this.spd;this.dy=Math.sin(this.ang)*this.spd;
        this.a=1;this.active=false;this.wait=Math.floor(Math.random()*400+160);
    }
    update(){
        if(!this.active){if(--this.wait<=0)this.active=true;return;}
        this.x+=this.dx;this.y+=this.dy;this.a-=.016;
        if(this.a<=0||this.x>canvas.width||this.y>canvas.height)this.reset();
    }
    draw(){
        if(!this.active)return;
        ctx.save();
        const g=ctx.createLinearGradient(this.x,this.y,this.x-this.dx*(this.len/this.spd),this.y-this.dy*(this.len/this.spd));
        g.addColorStop(0,`rgba(255,215,0,${this.a})`);g.addColorStop(.35,`rgba(255,0,255,${this.a*.55})`);g.addColorStop(1,'rgba(0,0,0,0)');
        ctx.strokeStyle=g;ctx.lineWidth=2;ctx.lineCap='round';ctx.shadowBlur=15;ctx.shadowColor='#FFD700';
        ctx.beginPath();ctx.moveTo(this.x,this.y);ctx.lineTo(this.x-this.dx*(this.len/this.spd),this.y-this.dy*(this.len/this.spd));ctx.stroke();ctx.restore();
    }
}
function initAll(){stars=Array.from({length:100},(_,i)=>new Star(i<100));comets=[new Comet()];}
function drawConst(){
    for(let i=0;i<stars.length;i++){
        for(let j=i+1;j<stars.length;j++){
            const d=Math.hypot(stars[i].x-stars[j].x,stars[i].y-stars[j].y);
            if(d<108){ctx.strokeStyle=`rgba(139,0,255,${(1-d/108)*.07})`;ctx.lineWidth=.5;ctx.beginPath();ctx.moveTo(stars[i].x,stars[i].y);ctx.lineTo(stars[j].x,stars[j].y);ctx.stroke();}
        }
        if(mouse.x!==null){
            const d=Math.hypot(stars[i].x-mouse.x,stars[i].y-mouse.y);
            if(d<160){ctx.strokeStyle=`rgba(255,0,255,${(1-d/160)*.15})`;ctx.lineWidth=.6;ctx.beginPath();ctx.moveTo(stars[i].x,stars[i].y);ctx.lineTo(mouse.x,mouse.y);ctx.stroke();}
        }
    }
}
function tick(){
    ctx.clearRect(0,0,canvas.width,canvas.height);
    if(mouse.tx!==null){
        mouse.x=mouse.x===null?mouse.tx:mouse.x+(mouse.tx-mouse.x)*.1;
        mouse.y=mouse.y===null?mouse.ty:mouse.y+(mouse.ty-mouse.y)*.1;
    }else{mouse.x=null;mouse.y=null;}
    stars.forEach(s=>{s.update();s.draw();});
    comets.forEach(c=>{c.update();c.draw();});
    drawConst();
    requestAnimationFrame(tick);
}
window.addEventListener('resize',resize);
resize(); tick();

// ── PLACEHOLDERS ──────────────────────────────────────────────────
const PH_MAIN  = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='400' height='225'><rect width='100%25' height='100%25' fill='%23050507'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='monospace' font-size='9' fill='%235B21B6' font-weight='700' letter-spacing='2'>AGUARDANDO SINAL DE TRANSMISSAO</text></svg>";
const PH_FRAME = "data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='200' height='113'><rect width='100%25' height='100%25' fill='%23050507'/><text x='50%25' y='50%25' dominant-baseline='middle' text-anchor='middle' font-family='monospace' font-size='9' fill='%235B21B6' font-weight='700'>TIMELINE</text></svg>";
document.getElementById('main-thumb').src  = PH_MAIN;
document.getElementById('start-thumb').src = PH_FRAME;
document.getElementById('end-thumb').src   = PH_FRAME;

// ── TOGGLE HELPERS ────────────────────────────────────────────────
function togSync(inp, trk) {
    inp.addEventListener('change', () => inp.checked ? trk.classList.add('tog-on') : trk.classList.remove('tog-on'));
}
togSync(document.getElementById('audio-only-toggle'), document.getElementById('trk-audio'));
togSync(document.getElementById('whatsapp-toggle'),   document.getElementById('trk-wa'));
togSync(document.getElementById('cut-toggle'),        document.getElementById('trk-cut'));

// ── INIT ──────────────────────────────────────────────────────────
let videoDuration = 0;
window.addEventListener('pywebviewready', () => {
    pywebview.api.get_initial_data().then(res => {
        document.getElementById('dest-input').value = res.dest;
        if (!res.yt_dlp || !res.ffmpeg) {
            addLog('ERRO: yt-dlp ou ffmpeg nao encontrados. Execute setup.bat.', 'err');
            document.getElementById('download-btn').disabled = true;
            document.getElementById('verify-btn').disabled   = true;
        } else {
            addLog('[ok] Motor cosmico inicializado. Todos os sistemas operacionais.', 'ok');
        }
    });
});

// ── LOG ────────────────────────────────────────────────────────────
function addLog(text, tag='info') {
    const el  = document.getElementById('log-console');
    const div = document.createElement('div');
    div.className = tag==='ok' ? 'log-ok' : tag==='err' ? 'log-err' : text.startsWith('[EXEC]') ? 'log-cmd' : 'log-info';
    div.textContent = text;
    el.appendChild(div);
    el.scrollTop = el.scrollHeight;
}
window.addLog = addLog;

// ── PROGRESS ──────────────────────────────────────────────────────
function updateProgress(pct, text) {
    document.getElementById('progress-bar').style.width = pct + '%';
    const t = document.getElementById('progress-text');
    t.textContent = text.toUpperCase();
    t.style.color = pct>0&&pct<100 ? '#C084FC' : pct>=100 ? '#34D399' : 'var(--muted)';
}
window.updateProgress = updateProgress;

// ── ACTIONS ───────────────────────────────────────────────────────
function pasteClipboard() {
    pywebview.api.get_clipboard().then(t => { if(t) document.getElementById('url-input').value=t; });
}
function chooseDirectory() {
    pywebview.api.choose_directory().then(p => { if(p) document.getElementById('dest-input').value=p; });
}
function openDirectory() {
    pywebview.api.open_directory(document.getElementById('dest-input').value);
}

// ── VERIFY ────────────────────────────────────────────────────────
function verifyUrl() {
    const url = document.getElementById('url-input').value.trim();
    if(!url) return;
    const btn=document.getElementById('verify-btn'), lbl=document.getElementById('verify-label');
    btn.disabled=true; lbl.textContent='Conectando...';
    document.getElementById('video-title').textContent='Rastreando fluxo cosmico...';
    document.getElementById('video-meta').textContent ='Decodificando metadados...';

    pywebview.api.verify_url(url, document.getElementById('cookies-select').value)
    .then(res => {
        btn.disabled=false; lbl.textContent='VERIFICAR';
        if(res.error){
            document.getElementById('video-title').textContent='Erro ao verificar URL.';
            document.getElementById('video-meta').textContent =res.error;
            addLog('ERRO: '+res.error,'err'); return;
        }
        document.getElementById('video-title').textContent=res.title;
        document.getElementById('video-meta').textContent =`Canal: ${res.uploader}  |  ${res.duration_str}  |  ${res.views} views`;
        if(res.thumb) document.getElementById('main-thumb').src=res.thumb;
        videoDuration=res.duration;
        document.getElementById('start-slider').max=videoDuration;
        document.getElementById('end-slider').max  =videoDuration;
        document.getElementById('start-slider').value=0;
        document.getElementById('end-slider').value  =videoDuration;
        document.getElementById('start-input').value='00:00:00';
        document.getElementById('end-input').value  =res.duration_hms;
        addLog('[ok] Media capturada: '+res.title,'ok');
        if(document.getElementById('cut-toggle').checked){triggerPreview('start',0);triggerPreview('end',videoDuration);}
    });
}

// ── CUT TOGGLE ────────────────────────────────────────────────────
function toggleCut() {
    const ws=document.getElementById('cut-workspace');
    if(document.getElementById('cut-toggle').checked){
        ws.style.display='flex';
        if(videoDuration>0){triggerPreview('start',document.getElementById('start-slider').value);triggerPreview('end',document.getElementById('end-slider').value);}
    }else{ws.style.display='none';}
}

// ── SLIDER / INPUT LOGIC ──────────────────────────────────────────
function fmtHMS(s){
    s=Math.max(0,parseInt(s));
    return [Math.floor(s/3600),Math.floor((s%3600)/60),s%60].map(v=>String(v).padStart(2,'0')).join(':');
}
function parseHMS(t){
    const p=t.trim().split(':').map(Number);
    if(p.some(isNaN))return null;
    return p.length===1?p[0]:p.length===2?p[0]*60+p[1]:p[0]*3600+p[1]*60+p[2];
}
function onSliderChange(w,v){
    document.getElementById(w==='start'?'start-input':'end-input').value=fmtHMS(v);
    enforceOrder(w);triggerPreview(w,parseInt(v));
}
function onInputChange(w){
    const inp=document.getElementById(w==='start'?'start-input':'end-input');
    const sld=document.getElementById(w==='start'?'start-slider':'end-slider');
    let s=parseHMS(inp.value);if(s===null)return;
    if(videoDuration>0)s=Math.max(0,Math.min(s,videoDuration));
    sld.value=s;inp.value=fmtHMS(s);enforceOrder(w);triggerPreview(w,s);
}
function enforceOrder(changed){
    const sv=parseInt(document.getElementById('start-slider').value);
    const ev=parseInt(document.getElementById('end-slider').value);
    if(sv>ev){
        if(changed==='start'){document.getElementById('end-slider').value=sv;document.getElementById('end-input').value=fmtHMS(sv);}
        else{document.getElementById('start-slider').value=ev;document.getElementById('start-input').value=fmtHMS(ev);}
    }
}
const dbnc={start:null,end:null};
function triggerPreview(w,ts){
    clearTimeout(dbnc[w]);
    dbnc[w]=setTimeout(()=>{
        pywebview.api.get_frame_preview(w,ts).then(b64=>{if(b64)document.getElementById(w==='start'?'start-thumb':'end-thumb').src=b64;});
    },300);
}

// ── DOWNLOAD ──────────────────────────────────────────────────────
function startDownload(){
    const url=document.getElementById('url-input').value.trim();if(!url)return;
    document.getElementById('download-btn').disabled=true;
    document.getElementById('cancel-btn').disabled=false;
    const cutOn=document.getElementById('cut-toggle').checked;
    pywebview.api.start_download(
        url,
        document.getElementById('quality-select').value,
        document.getElementById('audio-only-toggle').checked,
        document.getElementById('whatsapp-toggle').checked,
        document.getElementById('cookies-select').value,
        cutOn?document.getElementById('start-input').value:'',
        cutOn?document.getElementById('end-input').value:'',
        document.getElementById('dest-input').value
    ).then(()=>{document.getElementById('download-btn').disabled=false;document.getElementById('cancel-btn').disabled=true;});
}
function cancelDownload(){
    pywebview.api.cancel_download().then(()=>{document.getElementById('download-btn').disabled=false;document.getElementById('cancel-btn').disabled=true;});
}
</script>
</body>
</html>"""


class LOWDownloaderAPI:
    def __init__(self, app: LOWDownloaderApp) -> None:
        self.app = app

    def get_initial_data(self) -> dict:
        return {
            "dest": str(self.app.dest_dir),
            "yt_dlp": self.app.yt_dlp_cmd is not None,
            "ffmpeg": self.app.ffmpeg_path is not None,
        }

    def get_clipboard(self) -> str:
        return get_windows_clipboard()

    def choose_directory(self) -> str:
        active_win = webview.active_window()
        if not active_win:
            return ""
        folders = active_win.create_file_dialog(webview.FOLDER_DIALOG)
        if folders and len(folders) > 0:
            self.app.dest_dir = Path(folders[0])
            return folders[0]
        return ""

    def open_directory(self, path: str) -> None:
        if path:
            p = Path(path)
            p.mkdir(parents=True, exist_ok=True)
            os.startfile(str(p))

    def verify_url(self, url: str, cookies_choice: str) -> dict:
        url = url.strip()
        if not url or not self.app.yt_dlp_cmd:
            return {"error": "Instalação ausente do yt-dlp ou URL vazia."}

        cookies = self.app.cookies_arg_from_str(cookies_choice)
        cmd = f'{self.app.yt_dlp_cmd} -J --no-playlist --no-warnings --js-runtimes node --remote-components ejs:github {cookies} "{url}"'
        try:
            self.app.verify_seq += 1
            seq = self.app.verify_seq

            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                    timeout=60, encoding="utf-8", errors="replace",
                                    creationflags=CREATIONFLAGS)
            if seq != self.app.verify_seq:
                return {"error": "Nova requisição sobrepôs esta."}
            if result.returncode != 0:
                err = result.stderr.strip().splitlines()[-1] if result.stderr else "Falha de conexão com a CDN."
                return {"error": err}

            data = json.loads(result.stdout)
            duration = int(data.get("duration") or 0)
            self.app.video_duration = duration
            self.app.video_info = data
            title = data.get("title", "Título Indisponível")
            uploader = data.get("uploader") or data.get("channel") or "Desconhecido"
            duration_str = format_duration(duration) if duration else "Indeterminada"
            view_count = data.get("view_count")
            views = f"{view_count:,}".replace(",", ".") if view_count else "Desconhecidas"

            # Busca URL de stream (baixa latência) para previews
            self.app.fetch_stream_url(url, cookies_choice, seq)

            # Baixa e codifica thumbnail principal em Base64
            thumb_b64 = ""
            thumb_url = data.get("thumbnail")
            if thumb_url:
                try:
                    req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
                    with urllib.request.urlopen(req, timeout=15) as r:
                        raw_data = r.read()
                    encoded = base64.b64encode(raw_data).decode("utf-8")
                    thumb_b64 = f"data:image/jpeg;base64,{encoded}"
                except Exception:
                    pass

            return {
                "title": title,
                "uploader": uploader,
                "duration": duration,
                "duration_str": duration_str,
                "duration_hms": fmt_hms(duration),
                "views": views,
                "thumb": thumb_b64
            }

        except Exception as e:
            return {"error": f"Exceção do sistema: {str(e)}"}

    def get_frame_preview(self, which: str, timestamp: int) -> str:
        timestamp = max(0, int(float(timestamp)))
        if not self.app.m3u8_url or not self.app.ffmpeg_path:
            return ""
        out_path = CACHE_DIR / f"_preview_{which}.png"
        cmd = [
            self.app.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", self.app.m3u8_url,
            "-frames:v", "1",
            "-vf", f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,"
                   f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:color=black",
            "-y", "-loglevel", "error",
            str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=25, creationflags=CREATIONFLAGS)
            if out_path.exists() and out_path.stat().st_size > 0:
                with open(out_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode("utf-8")
                return f"data:image/png;base64,{encoded}"
        except Exception:
            pass
        return ""

    def start_download(self, url: str, quality: str, audio_only: bool, whatsapp_optimize: bool,
                       cookies_choice: str, start_time: str, end_time: str, dest_dir: str) -> bool:
        
        dest = Path(dest_dir.strip() or str(DEFAULT_DOWNLOAD_DIR))
        dest.mkdir(parents=True, exist_ok=True)
        self.app.dest_dir = dest

        start_sec = parse_time_to_seconds(start_time)
        end_sec = parse_time_to_seconds(end_time)

        quality_map = {
            "Melhor (Source)": "bestvideo*+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]/best[height<=1080]/best",
            "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]/best[height<=720]/best",
            "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]/best[height<=480]/best",
            "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]/best[height<=360]/best",
            "Pior (rápido)": "worst",
        }
        fmt = quality_map.get(quality, "bestvideo*+bestaudio/best")
        outtmpl = str(dest / "%(uploader)s - %(title).120B [%(id)s].%(ext)s")

        cookies = self.app.cookies_arg_from_str(cookies_choice)

        parts = [
            self.app.yt_dlp_cmd,
            "--newline",
            "--no-playlist",
            "--no-mtime",
            "--restrict-filenames",
            "--js-runtimes node",
            "--remote-components ejs:github",
            cookies,
            f'--ffmpeg-location "{self.app.ffmpeg_path}"' if self.app.ffmpeg_path else "",
            f'-o "{outtmpl}"',
            '--print "after_move:LOWDOWNLOADER_FILE:%(filepath)s"',
        ]

        if audio_only:
            parts += ["-x", "--audio-format mp3", "--audio-quality 0"]
        else:
            parts += [f'-f "{fmt}"', "--merge-output-format mp4"]

        if start_sec is not None or end_sec is not None:
            s = fmt_hms(start_sec) if start_sec is not None else "0"
            e = fmt_hms(end_sec) if end_sec is not None else "inf"
            parts += [f'--download-sections "*{s}-{e}"', "--force-keyframes-at-cuts"]

        parts.append(f'"{url}"')
        cmdline = " ".join(p for p in parts if p)

        self.app.add_log(f"[EXEC] {cmdline}", "info")
        self.app.update_progress(0, "Iniciando download...")
        self.app.final_file = None

        threading.Thread(
            target=self.app.download_worker, 
            args=(cmdline, dest, whatsapp_optimize, audio_only), 
            daemon=True
        ).start()
        return True

    def cancel_download(self) -> bool:
        self.app.cancel_download()
        return True


class LOWDownloaderApp:
    def __init__(self) -> None:
        self.yt_dlp_cmd: str | None = find_yt_dlp()
        self.ffmpeg_path: str | None = find_ffmpeg()
        
        self.dest_dir = DEFAULT_DOWNLOAD_DIR
        self.video_info: dict | None = None
        self.video_duration: int = 0
        self.m3u8_url: str | None = None
        self.verify_seq: int = 0
        self.final_file: Path | None = None
        self._proc: subprocess.Popen | None = None

    def cookies_arg_from_str(self, choice: str) -> str:
        choice = choice.strip().lower()
        if not choice or choice == "nenhum":
            return ""
        if "cookies.txt" in choice:
            cookies_file = APP_DIR / "cookies.txt"
            if cookies_file.exists():
                return f'--cookies "{str(cookies_file)}"'
            else:
                self.add_log("[!] Arquivo 'cookies.txt' nao encontrado na pasta do programa.", "err")
                return ""
        return f"--cookies-from-browser {choice}"

    def fetch_stream_url(self, url: str, cookies_choice: str, seq: int) -> None:
        cookies = self.cookies_arg_from_str(cookies_choice)
        def worker():
            cmd = (f'{self.yt_dlp_cmd} -f "worst[height>=360]/worst" -g '
                   f'--no-playlist --no-warnings --js-runtimes node --remote-components ejs:github {cookies} "{url}"')
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                        timeout=30, encoding="utf-8", errors="replace",
                                        creationflags=CREATIONFLAGS)
                if seq != self.verify_seq:
                    return
                if result.returncode == 0:
                    self.m3u8_url = result.stdout.strip().split("\n")[0]
                    self.add_log("[ok] Fluxo dinâmico de rede indexado. Prévias carregadas.", "ok")
                else:
                    self.add_log("[!] Fluxo dinâmico indisponível. Prévias podem apresentar lentidão.", "err")
            except Exception:
                pass
        threading.Thread(target=worker, daemon=True).start()

    def add_log(self, text: str, tag: str = "info") -> None:
        win = webview.active_window()
        if win:
            win.evaluate_js(f"window.addLog({json.dumps(text)}, {json.dumps(tag)})")

    def update_progress(self, pct: float, text: str) -> None:
        win = webview.active_window()
        if win:
            win.evaluate_js(f"window.updateProgress({pct}, {json.dumps(text)})")

    def download_worker(self, cmdline: str, dest: Path, whatsapp_optimize: bool, audio_only: bool) -> None:
        try:
            self._proc = subprocess.Popen(
                cmdline, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=CREATIONFLAGS,
            )
            progress_re = re.compile(r"\[download\]\s+([\d.]+)%")
            for line in self._proc.stdout:
                line = line.rstrip()
                if not line:
                    continue
                if line.startswith("LOWDOWNLOADER_FILE:"):
                    self.final_file = Path(line[len("LOWDOWNLOADER_FILE:"):])
                    continue
                m = progress_re.search(line)
                if m:
                    pct = float(m.group(1))
                    self.update_progress(pct, line)
                else:
                    self.update_progress(self.get_progress_value(), line[:110])
                if any(t in line for t in ("ERROR", "WARNING", "[Merger]", "[ExtractAudio]",
                                           "Destination:", "has already been downloaded")):
                    self.add_log(line, "err" if "ERROR" in line else "info")
            
            rc = self._proc.wait()
            self.download_done(rc == 0, dest, whatsapp_optimize, audio_only)
        except Exception as e:
            self.add_log(f"[ERRO CRÍTICO DE INTERFACE]: {e}", "err")
            self.download_done(False, dest, whatsapp_optimize, audio_only)

    def get_progress_value(self) -> float:
        win = webview.active_window()
        if win:
            val = win.evaluate_js("document.getElementById('progress-bar').style.width")
            if val:
                try:
                    return float(val.replace("%", ""))
                except ValueError:
                    pass
        return 0.0

    def download_done(self, ok: bool, dest: Path, whatsapp_optimize: bool, audio_only: bool) -> None:
        self._proc = None
        if not ok:
            self.update_progress(0, "Operação malsucedida.")
            self.add_log("[🚨] Download interrompido ou falho.", "err")
            self.reset_ui_buttons()
            return

        self.update_progress(100, "Download Concluído.")
        self.add_log("[ok] Download finalizado com sucesso.", "ok")

        do_whatsapp = (whatsapp_optimize and not audio_only 
                       and self.final_file is not None and self.final_file.exists())
        
        if do_whatsapp:
            self.start_whatsapp_encode(self.final_file)
        else:
            self.reset_ui_buttons()
            if self.final_file:
                self.update_progress(100, f"Salvo: {self.final_file.name}")
            else:
                self.update_progress(100, f"Salvo com sucesso em: {dest}")

    def start_whatsapp_encode(self, src: Path) -> None:
        if not self.ffmpeg_path:
            self.add_log("[!] ffmpeg não localizado — conversão WhatsApp cancelada.", "err")
            self.reset_ui_buttons()
            return
        out = src.with_name(src.stem + "_whatsapp.mp4")
        self.update_progress(0, "Otimizando codificação de pixel p/ WhatsApp...")
        self.add_log(f"[..] Iniciando re-encode H.264 Main + AAC -> {out.name}", "info")
        threading.Thread(target=self.whatsapp_encode_worker, args=(src, out), daemon=True).start()

    def whatsapp_encode_worker(self, src: Path, out: Path) -> None:
        total_sec = float(self.video_duration) if self.video_duration > 0 else 0.0
        if total_sec == 0.0:
            try:
                r = subprocess.run(
                    [self.ffmpeg_path, "-i", str(src)],
                    capture_output=True, text=True, encoding="utf-8", errors="replace",
                    creationflags=CREATIONFLAGS,
                )
                m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr or "")
                if m:
                    total_sec = int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
            except Exception:
                pass

        cmd = [
            self.ffmpeg_path,
            "-y",
            "-i", str(src),
            "-c:v", "libx264",
            "-profile:v", "main",
            "-level", "4.0",
            "-preset", "medium",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-vf",
            "scale='min(1280,iw)':'min(720,ih)':force_original_aspect_ratio=decrease,"
            "scale=trunc(iw/2)*2:trunc(ih/2)*2,fps=fps='min(30,source_fps)'",
            "-c:a", "aac",
            "-b:a", "128k",
            "-ac", "2",
            "-ar", "44100",
            "-movflags", "+faststart",
            "-progress", "pipe:1",
            "-nostats",
            "-loglevel", "error",
            str(out),
        ]
        try:
            self._proc = subprocess.Popen(
                cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=CREATIONFLAGS,
            )
            for line in self._proc.stdout:
                line = line.strip()
                if not line:
                    continue
                if line.startswith("out_time_us="):
                    try:
                        us = int(line.split("=", 1)[1])
                        if total_sec > 0:
                            pct = min(99.0, (us / 1_000_000) / total_sec * 100)
                            self.update_progress(pct, f"Otimizando p/ WhatsApp: {pct:.1f}%")
                    except ValueError:
                        pass
                elif line.startswith("progress="):
                    if line.endswith("=end"):
                        break
            rc = self._proc.wait()
            self.whatsapp_done(rc == 0, src, out)
        except Exception as e:
            self.add_log(f"[ERRO DE ENCODE]: {e}", "err")
            self.whatsapp_done(False, src, out)

    def whatsapp_done(self, ok: bool, src: Path, out: Path) -> None:
        self.reset_ui_buttons()
        self._proc = None
        if ok and out.exists() and out.stat().st_size > 0:
            self.update_progress(100, f"Otimizado: {out.name}")
            size_mb = out.stat().st_size / (1024 * 1024)
            self.add_log(f"[ok] Otimização WhatsApp Concluída: {out.name} ({size_mb:.1f} MB)", "ok")
        else:
            self.update_progress(0, "Conversão WhatsApp falhou.")
            self.add_log("[err] Falha crítica de re-encoding do ffmpeg.", "err")

    def cancel_download(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self.add_log("[!] Operação cancelada de forma imediata pelo usuário.", "err")
            except Exception:
                pass
        self.reset_ui_buttons()

    def reset_ui_buttons(self) -> None:
        win = webview.active_window()
        if win:
            win.evaluate_js("document.getElementById('download-btn').disabled = false;")
            win.evaluate_js("document.getElementById('cancel-btn').disabled = true;")


def get_logo_html() -> str:
    logo_path = Path(__file__).parent / "lowdownloader_logo.png"
    if logo_path.exists():
        try:
            with open(logo_path, "rb") as f:
                encoded = base64.b64encode(f.read()).decode("utf-8")
            return f'<img src="data:image/png;base64,{encoded}" style="width:32px;height:32px;object-fit:contain;position:relative;z-index:2;">'
        except Exception:
            pass
    return """<svg width="21" height="21" fill="none" stroke="rgba(196,181,253,1)" stroke-width="2.2" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round"
                          d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5M16.5 12L12 16.5m0 0L7.5 12M12 16.5V3"/>
                </svg>"""


def main() -> None:
    # Cria pasta downloads no primeiro carregamento
    DEFAULT_DOWNLOAD_DIR.mkdir(parents=True, exist_ok=True)
    
    logo_html = get_logo_html()
    dynamic_html = HTML_CONTENT.replace("{{LOGO_IMAGE}}", logo_html)
    
    app = LOWDownloaderApp()
    api = LOWDownloaderAPI(app)

    # Abre a janela nativa acelerada por hardware (Microsoft Edge WebView2 no Windows)
    window = webview.create_window(
        "LOWDownloader Pro",
        html=dynamic_html,
        js_api=api,
        width=1180,
        height=840,
        resizable=True,
        min_size=(1040, 740),
        background_color="#050507"
    )
    
    # Destrói arquivos temporários de preview ao fechar
    def on_closed():
        try:
            for f in CACHE_DIR.glob("_preview_*.png"):
                f.unlink()
        except Exception:
            pass

    window.events.closed += on_closed
    
    # Define o ícone da aplicação se o arquivo .ico existir
    ico_path = Path(__file__).parent / "lowdownloader_logo.ico"
    ico_str = str(ico_path) if ico_path.exists() else None
    webview.start(icon=ico_str)


if __name__ == "__main__":
    main()
