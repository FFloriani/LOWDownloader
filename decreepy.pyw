"""Decreepy Downloader — GUI para baixar VODs e Clips da Twitch via yt-dlp."""
from __future__ import annotations

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
from tkinter import Tk, StringVar, BooleanVar, DoubleVar, filedialog, messagebox, END
from tkinter import ttk
import tkinter as tk

APP_DIR = Path(__file__).resolve().parent
BIN_DIR = APP_DIR / "bin"
CACHE_DIR = APP_DIR / ".cache"
DEFAULT_DOWNLOAD_DIR = APP_DIR / "downloads"

# Twitch roxo + tema escuro
COLOR_BG = "#0e0e10"
COLOR_PANEL = "#18181b"
COLOR_PANEL_2 = "#1f1f23"
COLOR_ACCENT = "#9147ff"
COLOR_ACCENT_HOVER = "#772ce8"
COLOR_TEXT = "#efeff1"
COLOR_TEXT_DIM = "#adadb8"
COLOR_BORDER = "#2d2d35"
COLOR_OK = "#00f593"
COLOR_ERR = "#ff5c5c"

THUMB_W, THUMB_H = 320, 180
MAIN_THUMB_W, MAIN_THUMB_H = 280, 158


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


CREATIONFLAGS = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0


class DecreepyApp:
    def __init__(self, root: Tk) -> None:
        self.root = root
        self.root.title("Decreepy Downloader")
        self.root.geometry("960x980")
        self.root.minsize(820, 700)
        self.root.configure(bg=COLOR_BG)

        self.yt_dlp_cmd: str | None = find_yt_dlp()
        self.ffmpeg_path: str | None = find_ffmpeg()

        # estado do vídeo
        self.video_info: dict | None = None
        self.video_duration: int = 0
        self.m3u8_url: str | None = None
        self._verify_seq: int = 0  # cancela verificações antigas

        # imagens (refs pra evitar GC do tk)
        self._main_thumb_image = None
        self._start_frame_image = None
        self._end_frame_image = None
        self._placeholder_main = None
        self._placeholder_frame = None

        # debounce/preview
        self._preview_jobs: dict[str, str] = {}
        self._preview_seq: dict[str, int] = {"start": 0, "end": 0}

        # vars de UI
        self.url_var = StringVar()
        self.quality_var = StringVar(value="Melhor (Source)")
        self.audio_only_var = BooleanVar(value=False)
        self.cut_var = BooleanVar(value=False)
        self.start_var = StringVar(value="00:00:00")
        self.end_var = StringVar(value="00:00:00")
        self.start_slider_var = DoubleVar(value=0)
        self.end_slider_var = DoubleVar(value=0)
        self.dest_var = StringVar(value=str(DEFAULT_DOWNLOAD_DIR))
        self.cookies_var = StringVar(value="Nenhum")
        self.whatsapp_var = BooleanVar(value=False)
        self._final_file: Path | None = None  # arquivo baixado, capturado do stdout
        self.info_var = StringVar(
            value="Cole a URL (Twitch, YouTube, Facebook, Twitter/X, etc.) e clique em Verificar.")

        self._proc: subprocess.Popen | None = None
        self._log_queue: queue.Queue[tuple[str, str]] = queue.Queue()
        self._download_thread: threading.Thread | None = None
        # flags pra evitar loops slider<->entry
        self._sync_lock: dict[str, bool] = {"start": False, "end": False}

        self._setup_styles()
        self._build_placeholders()
        self._build_ui()
        self._poll_log_queue()
        self._check_dependencies()

        CACHE_DIR.mkdir(exist_ok=True)
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    # ---------- estilo ----------
    def _setup_styles(self) -> None:
        style = ttk.Style()
        style.theme_use("clam")

        style.configure(".", background=COLOR_BG, foreground=COLOR_TEXT,
                        fieldbackground=COLOR_PANEL, bordercolor=COLOR_BORDER,
                        lightcolor=COLOR_BORDER, darkcolor=COLOR_BORDER)
        style.configure("TFrame", background=COLOR_BG)
        style.configure("Panel.TFrame", background=COLOR_PANEL)
        style.configure("TLabel", background=COLOR_BG, foreground=COLOR_TEXT, font=("Segoe UI", 10))
        style.configure("Panel.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT)
        style.configure("Title.TLabel", background=COLOR_BG, foreground=COLOR_TEXT,
                        font=("Segoe UI Semibold", 18))
        style.configure("Subtitle.TLabel", background=COLOR_BG, foreground=COLOR_TEXT_DIM,
                        font=("Segoe UI", 9))
        style.configure("Section.TLabel", background=COLOR_BG, foreground=COLOR_ACCENT,
                        font=("Segoe UI Semibold", 10))
        style.configure("Info.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT_DIM,
                        font=("Segoe UI", 9))
        style.configure("InfoStrong.TLabel", background=COLOR_PANEL, foreground=COLOR_TEXT,
                        font=("Segoe UI Semibold", 11))

        style.configure("TEntry", fieldbackground=COLOR_PANEL_2, foreground=COLOR_TEXT,
                        bordercolor=COLOR_BORDER, lightcolor=COLOR_BORDER,
                        darkcolor=COLOR_BORDER, insertcolor=COLOR_TEXT, padding=6)
        style.map("TEntry", bordercolor=[("focus", COLOR_ACCENT)],
                  lightcolor=[("focus", COLOR_ACCENT)])

        style.configure("TCombobox", fieldbackground=COLOR_PANEL_2, background=COLOR_PANEL_2,
                        foreground=COLOR_TEXT, bordercolor=COLOR_BORDER, arrowcolor=COLOR_TEXT,
                        padding=4)
        style.map("TCombobox", fieldbackground=[("readonly", COLOR_PANEL_2)],
                  selectbackground=[("readonly", COLOR_PANEL_2)],
                  selectforeground=[("readonly", COLOR_TEXT)])

        style.configure("TCheckbutton", background=COLOR_BG, foreground=COLOR_TEXT,
                        focuscolor=COLOR_BG)
        style.map("TCheckbutton", background=[("active", COLOR_BG)])

        style.configure("Accent.TButton", background=COLOR_ACCENT, foreground="#ffffff",
                        font=("Segoe UI Semibold", 11), padding=(18, 10),
                        bordercolor=COLOR_ACCENT, focuscolor=COLOR_ACCENT)
        style.map("Accent.TButton",
                  background=[("active", COLOR_ACCENT_HOVER), ("disabled", "#444")],
                  foreground=[("disabled", "#888")])

        style.configure("Secondary.TButton", background=COLOR_PANEL_2, foreground=COLOR_TEXT,
                        bordercolor=COLOR_BORDER, padding=(12, 6))
        style.map("Secondary.TButton",
                  background=[("active", COLOR_BORDER)])

        style.configure("Danger.TButton", background="#3a1f1f", foreground=COLOR_ERR,
                        bordercolor=COLOR_ERR, padding=(12, 6))
        style.map("Danger.TButton", background=[("active", "#552525")])

        style.configure("TProgressbar", background=COLOR_ACCENT, troughcolor=COLOR_PANEL_2,
                        bordercolor=COLOR_PANEL_2, lightcolor=COLOR_ACCENT,
                        darkcolor=COLOR_ACCENT)

        # scale (slider)
        style.configure("Decreepy.Horizontal.TScale", background=COLOR_BG,
                        troughcolor=COLOR_PANEL_2, bordercolor=COLOR_BORDER,
                        lightcolor=COLOR_ACCENT, darkcolor=COLOR_ACCENT)

    def _build_placeholders(self) -> None:
        from PIL import Image, ImageTk, ImageDraw
        # placeholder principal
        img = Image.new("RGB", (MAIN_THUMB_W, MAIN_THUMB_H), COLOR_PANEL_2)
        d = ImageDraw.Draw(img)
        d.text((MAIN_THUMB_W // 2 - 30, MAIN_THUMB_H // 2 - 6), "sem video", fill=COLOR_TEXT_DIM)
        self._placeholder_main = ImageTk.PhotoImage(img)
        # placeholder frame
        img2 = Image.new("RGB", (THUMB_W, THUMB_H), COLOR_PANEL_2)
        d2 = ImageDraw.Draw(img2)
        d2.text((THUMB_W // 2 - 50, THUMB_H // 2 - 6), "ajuste o tempo", fill=COLOR_TEXT_DIM)
        self._placeholder_frame = ImageTk.PhotoImage(img2)

    # ---------- UI ----------
    def _build_ui(self) -> None:
        outer = ttk.Frame(self.root, padding=(20, 16))
        outer.pack(fill="both", expand=True)

        # cabeçalho
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 12))
        ttk.Label(header, text="Decreepy Downloader", style="Title.TLabel").pack(anchor="w")
        ttk.Label(header,
                  text="Baixe Twitch, YouTube, Facebook, Twitter/X, Instagram, TikTok e mais — pronto pra edição.",
                  style="Subtitle.TLabel").pack(anchor="w")

        # URL
        ttk.Label(outer, text="URL (Twitch / YouTube / Facebook / Twitter/X / ...)",
                  style="Section.TLabel").pack(anchor="w")
        url_row = ttk.Frame(outer)
        url_row.pack(fill="x", pady=(4, 8))
        ttk.Entry(url_row, textvariable=self.url_var, font=("Segoe UI", 10)).pack(
            side="left", fill="x", expand=True)
        ttk.Button(url_row, text="Colar", style="Secondary.TButton",
                   command=self._paste_clipboard).pack(side="left", padx=(8, 0))
        ttk.Button(url_row, text="Verificar", style="Secondary.TButton",
                   command=self._verify_url).pack(side="left", padx=(6, 0))

        # painel info + thumb
        info_panel = ttk.Frame(outer, style="Panel.TFrame", padding=12)
        info_panel.pack(fill="x", pady=(0, 12))
        self.main_thumb_label = tk.Label(info_panel, image=self._placeholder_main,
                                         bg=COLOR_PANEL, bd=0)
        self.main_thumb_label.pack(side="left", padx=(0, 14))
        info_text = ttk.Frame(info_panel, style="Panel.TFrame")
        info_text.pack(side="left", fill="both", expand=True)
        self.info_title_label = ttk.Label(info_text, text="—", style="InfoStrong.TLabel",
                                          wraplength=580, justify="left")
        self.info_title_label.pack(anchor="w")
        self.info_meta_label = ttk.Label(info_text, textvariable=self.info_var,
                                         style="Info.TLabel", wraplength=580, justify="left")
        self.info_meta_label.pack(anchor="w", pady=(4, 0))

        # opções
        opts = ttk.Frame(outer)
        opts.pack(fill="x", pady=(0, 8))
        ttk.Label(opts, text="Qualidade", style="Section.TLabel").grid(row=0, column=0, sticky="w")
        quality_box = ttk.Combobox(opts, textvariable=self.quality_var, state="readonly",
                                   width=22,
                                   values=["Melhor (Source)", "1080p", "720p", "480p", "360p",
                                           "Pior (rápido)"])
        quality_box.grid(row=1, column=0, sticky="w", pady=(4, 0), padx=(0, 16))

        ttk.Label(opts, text="Formato", style="Section.TLabel").grid(row=0, column=1, sticky="w")
        ttk.Checkbutton(opts, text="Somente áudio (MP3)", variable=self.audio_only_var
                        ).grid(row=1, column=1, sticky="w", pady=(4, 0), padx=(0, 16))
        ttk.Checkbutton(opts, text="Otimizar p/ WhatsApp (gera *_whatsapp.mp4)",
                        variable=self.whatsapp_var
                        ).grid(row=2, column=1, sticky="w", pady=(2, 0), padx=(0, 16))

        ttk.Label(opts, text="Cookies do navegador",
                  style="Section.TLabel").grid(row=0, column=2, sticky="w")
        cookies_box = ttk.Combobox(opts, textvariable=self.cookies_var, state="readonly",
                                   width=14,
                                   values=["Nenhum", "Chrome", "Firefox", "Edge", "Brave",
                                           "Opera", "Vivaldi", "Chromium", "Safari"])
        cookies_box.grid(row=1, column=2, sticky="w", pady=(4, 0))
        ttk.Label(opts, text="(necessário p/ vídeos privados)",
                  style="Subtitle.TLabel").grid(row=2, column=2, sticky="w", pady=(2, 0))

        # corte
        cut_chk = ttk.Checkbutton(outer,
                                  text="Cortar um trecho específico (yt-dlp baixa só o pedaço)",
                                  variable=self.cut_var, command=self._toggle_cut)
        cut_chk.pack(anchor="w", pady=(8, 4))

        self.cut_frame = ttk.Frame(outer, style="Panel.TFrame", padding=12)

        # linha início
        start_row = ttk.Frame(self.cut_frame, style="Panel.TFrame")
        start_row.pack(fill="x", pady=(0, 6))
        ttk.Label(start_row, text="Início", style="Panel.TLabel", width=8).pack(side="left")
        self.start_entry = ttk.Entry(start_row, textvariable=self.start_var, width=10,
                                     font=("Consolas", 10))
        self.start_entry.pack(side="left", padx=(0, 8))
        self.start_entry.bind("<Return>", lambda e: self._on_entry_change("start"))
        self.start_entry.bind("<FocusOut>", lambda e: self._on_entry_change("start"))
        self.start_slider = ttk.Scale(start_row, from_=0, to=1,
                                      variable=self.start_slider_var, orient="horizontal",
                                      command=lambda v: self._on_slider_change("start", v))
        self.start_slider.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # preview início
        self.start_thumb_label = tk.Label(self.cut_frame, image=self._placeholder_frame,
                                          bg=COLOR_PANEL, bd=0)
        self.start_thumb_label.pack(anchor="w", pady=(0, 12))

        # linha fim
        end_row = ttk.Frame(self.cut_frame, style="Panel.TFrame")
        end_row.pack(fill="x", pady=(0, 6))
        ttk.Label(end_row, text="Fim", style="Panel.TLabel", width=8).pack(side="left")
        self.end_entry = ttk.Entry(end_row, textvariable=self.end_var, width=10,
                                   font=("Consolas", 10))
        self.end_entry.pack(side="left", padx=(0, 8))
        self.end_entry.bind("<Return>", lambda e: self._on_entry_change("end"))
        self.end_entry.bind("<FocusOut>", lambda e: self._on_entry_change("end"))
        self.end_slider = ttk.Scale(end_row, from_=0, to=1,
                                    variable=self.end_slider_var, orient="horizontal",
                                    command=lambda v: self._on_slider_change("end", v))
        self.end_slider.pack(side="left", fill="x", expand=True, padx=(4, 0))

        # preview fim
        self.end_thumb_label = tk.Label(self.cut_frame, image=self._placeholder_frame,
                                        bg=COLOR_PANEL, bd=0)
        self.end_thumb_label.pack(anchor="w")

        # destino
        self.dest_label = ttk.Label(outer, text="Pasta de destino", style="Section.TLabel")
        self.dest_label.pack(anchor="w", pady=(10, 0))
        dest_row = ttk.Frame(outer)
        dest_row.pack(fill="x", pady=(4, 10))
        ttk.Entry(dest_row, textvariable=self.dest_var).pack(side="left", fill="x", expand=True)
        ttk.Button(dest_row, text="Procurar...", style="Secondary.TButton",
                   command=self._choose_dest).pack(side="left", padx=(8, 0))
        ttk.Button(dest_row, text="Abrir pasta", style="Secondary.TButton",
                   command=self._open_dest).pack(side="left", padx=(6, 0))

        # ação
        action = ttk.Frame(outer)
        action.pack(fill="x", pady=(2, 6))
        self.download_btn = ttk.Button(action, text="BAIXAR", style="Accent.TButton",
                                       command=self._start_download)
        self.download_btn.pack(side="left")
        self.cancel_btn = ttk.Button(action, text="Cancelar", style="Danger.TButton",
                                     command=self._cancel_download, state="disabled")
        self.cancel_btn.pack(side="left", padx=(8, 0))

        # progresso
        self.progress = ttk.Progressbar(outer, mode="determinate", maximum=100)
        self.progress.pack(fill="x", pady=(8, 4))
        self.progress_label = ttk.Label(outer, text="Pronto.", style="Subtitle.TLabel")
        self.progress_label.pack(anchor="w")

        # log
        ttk.Label(outer, text="Log", style="Section.TLabel").pack(anchor="w", pady=(8, 4))
        log_frame = ttk.Frame(outer, style="Panel.TFrame")
        log_frame.pack(fill="both", expand=True)
        self.log_text = tk.Text(log_frame, height=6, bg=COLOR_PANEL, fg=COLOR_TEXT_DIM,
                                insertbackground=COLOR_TEXT, relief="flat", wrap="word",
                                font=("Consolas", 9), padx=10, pady=8)
        self.log_text.pack(side="left", fill="both", expand=True)
        self.log_text.tag_configure("ok", foreground=COLOR_OK)
        self.log_text.tag_configure("err", foreground=COLOR_ERR)
        self.log_text.tag_configure("info", foreground=COLOR_TEXT)
        scrollbar = ttk.Scrollbar(log_frame, command=self.log_text.yview)
        scrollbar.pack(side="right", fill="y")
        self.log_text.configure(yscrollcommand=scrollbar.set)

        self._toggle_cut()

    def _toggle_cut(self) -> None:
        if self.cut_var.get():
            self.cut_frame.pack(fill="x", pady=(0, 4), before=self.dest_label)
            # se já temos vídeo verificado, dispara previews
            if self.video_duration > 0 and self.m3u8_url:
                self._request_preview("start", int(self.start_slider_var.get()))
                self._request_preview("end", int(self.end_slider_var.get()))
        else:
            self.cut_frame.pack_forget()

    # ---------- helpers UI ----------
    def _paste_clipboard(self) -> None:
        try:
            text = self.root.clipboard_get().strip()
            if text:
                self.url_var.set(text)
        except tk.TclError:
            pass

    def _choose_dest(self) -> None:
        chosen = filedialog.askdirectory(initialdir=self.dest_var.get() or str(APP_DIR))
        if chosen:
            self.dest_var.set(chosen)

    def _open_dest(self) -> None:
        path = Path(self.dest_var.get())
        path.mkdir(parents=True, exist_ok=True)
        os.startfile(str(path))

    def _log(self, text: str, tag: str = "info") -> None:
        self._log_queue.put((text, tag))

    def _poll_log_queue(self) -> None:
        try:
            while True:
                text, tag = self._log_queue.get_nowait()
                self.log_text.insert(END, text + "\n", tag)
                self.log_text.see(END)
        except queue.Empty:
            pass
        self.root.after(80, self._poll_log_queue)

    # ---------- dependências ----------
    def _check_dependencies(self) -> None:
        missing = []
        if not self.yt_dlp_cmd:
            missing.append("yt-dlp")
        if not self.ffmpeg_path:
            missing.append("ffmpeg")
        if missing:
            self._log(f"[!] Dependências ausentes: {', '.join(missing)}", "err")
            self._log("    Rode 'setup.bat' primeiro para instalar.", "err")
            self.info_var.set("Dependências faltando. Execute setup.bat para instalar yt-dlp e ffmpeg.")
            self.download_btn.configure(state="disabled")
        else:
            self._log("[ok] yt-dlp e ffmpeg encontrados.", "ok")

    # ---------- cookies helper ----------
    def _cookies_arg(self) -> str:
        choice = self.cookies_var.get().strip().lower()
        if not choice or choice == "nenhum":
            return ""
        return f"--cookies-from-browser {choice}"

    # ---------- verificação ----------
    def _verify_url(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vazia", "Cole a URL da VOD ou Clip primeiro.")
            return
        if not self.yt_dlp_cmd:
            messagebox.showerror("yt-dlp ausente", "Rode setup.bat para instalar.")
            return
        self.info_var.set("Buscando informações... aguarde.")
        self.info_title_label.configure(text="—")
        self._verify_seq += 1
        seq = self._verify_seq
        threading.Thread(target=self._verify_worker, args=(url, seq), daemon=True).start()

    def _verify_worker(self, url: str, seq: int) -> None:
        cookies = self._cookies_arg()
        cmd = f'{self.yt_dlp_cmd} -J --no-playlist --no-warnings {cookies} "{url}"'
        try:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                    timeout=60, encoding="utf-8", errors="replace",
                                    creationflags=CREATIONFLAGS)
            if seq != self._verify_seq:
                return
            if result.returncode != 0:
                err = result.stderr.strip().splitlines()[-1] if result.stderr else "falha"
                self.root.after(0, lambda: self.info_var.set(f"Erro ao verificar: {err}"))
                self._log(result.stderr, "err")
                return
            data = json.loads(result.stdout)
            self.video_info = data
            duration = int(data.get("duration") or 0)
            self.video_duration = duration
            title = data.get("title", "?")
            uploader = data.get("uploader") or data.get("channel") or "?"
            duration_str = format_duration(duration) if duration else "?"
            view_count = data.get("view_count")
            views = f"{view_count:,}".replace(",", ".") if view_count else "?"
            meta = f"Canal: {uploader}  •  Duração: {duration_str}  •  Views: {views}"
            self.root.after(0, lambda: self._apply_video_info(title, meta, duration, data))
            self._log(f"[ok] Verificado: {title} ({duration_str})", "ok")

            # baixa thumb principal
            thumb_url = data.get("thumbnail")
            if thumb_url:
                self._fetch_main_thumb(thumb_url, seq)

            # pega URL m3u8 para extrair frames depois
            self._fetch_stream_url(url, seq)

        except subprocess.TimeoutExpired:
            self.root.after(0, lambda: self.info_var.set("Timeout ao verificar URL."))
        except json.JSONDecodeError:
            self.root.after(0, lambda: self.info_var.set("Resposta inválida do yt-dlp."))
        except Exception as e:
            self.root.after(0, lambda msg=str(e): self.info_var.set(f"Erro: {msg}"))

    def _apply_video_info(self, title: str, meta: str, duration: int, data: dict) -> None:
        self.info_title_label.configure(text=title)
        self.info_var.set(meta)
        # configura sliders
        if duration > 0:
            self.start_slider.configure(from_=0, to=duration)
            self.end_slider.configure(from_=0, to=duration)
            self.start_slider_var.set(0)
            self.end_slider_var.set(duration)
            self.start_var.set(fmt_hms(0))
            self.end_var.set(fmt_hms(duration))

    def _fetch_main_thumb(self, thumb_url: str, seq: int) -> None:
        def worker():
            try:
                req = urllib.request.Request(thumb_url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                if seq != self._verify_seq:
                    return
                from PIL import Image, ImageTk
                img = Image.open(io.BytesIO(data)).convert("RGB")
                img.thumbnail((MAIN_THUMB_W, MAIN_THUMB_H), Image.LANCZOS)
                self.root.after(0, self._set_main_thumb, img)
            except Exception as e:
                self._log(f"[!] Thumbnail falhou: {e}", "err")
        threading.Thread(target=worker, daemon=True).start()

    def _set_main_thumb(self, pil_img) -> None:
        from PIL import ImageTk
        self._main_thumb_image = ImageTk.PhotoImage(pil_img)
        self.main_thumb_label.configure(image=self._main_thumb_image)

    def _fetch_stream_url(self, url: str, seq: int) -> None:
        """Pega URL m3u8 (qualidade baixa) pra extrair frames sem baixar tudo."""
        cookies = self._cookies_arg()
        def worker():
            # qualidade baixa = extração rápida de frame
            cmd = (f'{self.yt_dlp_cmd} -f "worst[height>=360]/worst" -g '
                   f'--no-playlist --no-warnings {cookies} "{url}"')
            try:
                result = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                                        timeout=30, encoding="utf-8", errors="replace",
                                        creationflags=CREATIONFLAGS)
                if seq != self._verify_seq:
                    return
                if result.returncode == 0:
                    stream_url = result.stdout.strip().split("\n")[0]
                    self.m3u8_url = stream_url
                    self._log("[ok] Stream URL pronta para preview de frames.", "ok")
                    # se a checkbox de corte estiver ativa, dispara previews iniciais
                    if self.cut_var.get():
                        self.root.after(0, lambda: self._request_preview("start", 0))
                        self.root.after(0, lambda: self._request_preview("end", self.video_duration))
                else:
                    self._log("[!] Não foi possível obter stream URL (preview indisponível).", "err")
            except Exception as e:
                self._log(f"[!] Stream URL falhou: {e}", "err")
        threading.Thread(target=worker, daemon=True).start()

    # ---------- sliders <-> entries ----------
    def _on_slider_change(self, which: str, value) -> None:
        if self._sync_lock[which]:
            return
        seconds = int(float(value))
        var = self.start_var if which == "start" else self.end_var
        self._sync_lock[which] = True
        var.set(fmt_hms(seconds))
        self._sync_lock[which] = False
        self._enforce_order(which)
        self._request_preview(which, seconds)

    def _on_entry_change(self, which: str) -> None:
        if self._sync_lock[which]:
            return
        text_var = self.start_var if which == "start" else self.end_var
        slider_var = self.start_slider_var if which == "start" else self.end_slider_var
        seconds = parse_time_to_seconds(text_var.get())
        if seconds is None:
            return
        if self.video_duration > 0:
            seconds = max(0, min(seconds, self.video_duration))
        self._sync_lock[which] = True
        slider_var.set(seconds)
        text_var.set(fmt_hms(seconds))
        self._sync_lock[which] = False
        self._enforce_order(which)
        self._request_preview(which, seconds)

    def _enforce_order(self, just_changed: str) -> None:
        """Garante start <= end."""
        s = int(self.start_slider_var.get())
        e = int(self.end_slider_var.get())
        if s > e:
            if just_changed == "start":
                self._sync_lock["end"] = True
                self.end_slider_var.set(s)
                self.end_var.set(fmt_hms(s))
                self._sync_lock["end"] = False
            else:
                self._sync_lock["start"] = True
                self.start_slider_var.set(e)
                self.start_var.set(fmt_hms(e))
                self._sync_lock["start"] = False

    # ---------- preview de frame ----------
    def _request_preview(self, which: str, timestamp: int) -> None:
        if not self.cut_var.get() or not self.m3u8_url or not self.ffmpeg_path:
            return
        # cancela job anterior pendente
        prev = self._preview_jobs.get(which)
        if prev:
            try:
                self.root.after_cancel(prev)
            except Exception:
                pass
        # debounce 500ms
        job = self.root.after(500, lambda: self._dispatch_preview(which, timestamp))
        self._preview_jobs[which] = job

    def _dispatch_preview(self, which: str, timestamp: int) -> None:
        self._preview_seq[which] += 1
        seq = self._preview_seq[which]
        threading.Thread(target=self._extract_frame_worker,
                         args=(which, timestamp, seq), daemon=True).start()

    def _extract_frame_worker(self, which: str, timestamp: int, seq: int) -> None:
        if not self.m3u8_url or not self.ffmpeg_path:
            return
        out_path = CACHE_DIR / f"_preview_{which}.png"
        cmd = [
            self.ffmpeg_path,
            "-ss", str(max(0, timestamp)),
            "-i", self.m3u8_url,
            "-frames:v", "1",
            "-vf", f"scale={THUMB_W}:{THUMB_H}:force_original_aspect_ratio=decrease,"
                   f"pad={THUMB_W}:{THUMB_H}:(ow-iw)/2:(oh-ih)/2:color=black",
            "-y", "-loglevel", "error",
            str(out_path),
        ]
        try:
            subprocess.run(cmd, capture_output=True, timeout=45,
                           creationflags=CREATIONFLAGS)
        except subprocess.TimeoutExpired:
            self._log(f"[!] Preview timeout em {which}.", "err")
            return
        except Exception as e:
            self._log(f"[!] Preview erro: {e}", "err")
            return
        # se já houve outra requisição, descarta esta
        if seq != self._preview_seq[which]:
            return
        if out_path.exists() and out_path.stat().st_size > 0:
            self.root.after(0, self._update_preview_image, which, str(out_path))

    def _update_preview_image(self, which: str, path: str) -> None:
        try:
            from PIL import Image, ImageTk
            img = Image.open(path).convert("RGB")
            photo = ImageTk.PhotoImage(img)
            if which == "start":
                self._start_frame_image = photo
                self.start_thumb_label.configure(image=photo)
            else:
                self._end_frame_image = photo
                self.end_thumb_label.configure(image=photo)
        except Exception as e:
            self._log(f"[!] Carregar preview falhou: {e}", "err")

    # ---------- download ----------
    def _start_download(self) -> None:
        url = self.url_var.get().strip()
        if not url:
            messagebox.showwarning("URL vazia", "Cole a URL primeiro.")
            return
        if not self.yt_dlp_cmd:
            messagebox.showerror("yt-dlp ausente", "Rode setup.bat para instalar.")
            return

        dest = Path(self.dest_var.get().strip() or str(DEFAULT_DOWNLOAD_DIR))
        dest.mkdir(parents=True, exist_ok=True)

        start_sec = end_sec = None
        if self.cut_var.get():
            start_sec = parse_time_to_seconds(self.start_var.get())
            end_sec = parse_time_to_seconds(self.end_var.get())
            if self.start_var.get().strip() and start_sec is None:
                messagebox.showerror("Tempo inválido", "Início inválido. Use HH:MM:SS ou MM:SS.")
                return
            if self.end_var.get().strip() and end_sec is None:
                messagebox.showerror("Tempo inválido", "Fim inválido. Use HH:MM:SS ou MM:SS.")
                return
            if start_sec is not None and end_sec is not None and end_sec <= start_sec:
                messagebox.showerror("Intervalo inválido", "Fim deve ser maior que Início.")
                return

        quality_map = {
            "Melhor (Source)": "bestvideo*+bestaudio/best",
            "1080p": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
            "720p":  "bestvideo[height<=720]+bestaudio/best[height<=720]",
            "480p":  "bestvideo[height<=480]+bestaudio/best[height<=480]",
            "360p":  "bestvideo[height<=360]+bestaudio/best[height<=360]",
            "Pior (rápido)": "worst",
        }
        fmt = quality_map.get(self.quality_var.get(), "bestvideo*+bestaudio/best")

        outtmpl = str(dest / "%(uploader)s - %(title).120B [%(id)s].%(ext)s")

        parts = [
            self.yt_dlp_cmd,
            "--newline",
            "--no-playlist",
            "--no-mtime",
            "--restrict-filenames",
            self._cookies_arg(),
            f'--ffmpeg-location "{self.ffmpeg_path}"' if self.ffmpeg_path else "",
            f'-o "{outtmpl}"',
            # imprime o caminho final do arquivo apos download e merge
            '--print "after_move:DECREEPY_FILE:%(filepath)s"',
        ]

        if self.audio_only_var.get():
            parts += ["-x", "--audio-format mp3", "--audio-quality 0"]
        else:
            parts += [f'-f "{fmt}"', "--merge-output-format mp4"]

        if self.cut_var.get() and (start_sec is not None or end_sec is not None):
            s = fmt_hms(start_sec) if start_sec is not None else "0"
            e = fmt_hms(end_sec) if end_sec is not None else "inf"
            parts += [f'--download-sections "*{s}-{e}"', "--force-keyframes-at-cuts"]

        parts.append(f'"{url}"')
        cmdline = " ".join(p for p in parts if p)

        self._log(f"[run] {cmdline}", "info")
        self.progress["value"] = 0
        self.progress_label.configure(text="Iniciando...")
        self.download_btn.configure(state="disabled")
        self.cancel_btn.configure(state="normal")
        self._final_file = None

        self._download_thread = threading.Thread(
            target=self._download_worker, args=(cmdline, dest), daemon=True)
        self._download_thread.start()

    def _download_worker(self, cmdline: str, dest: Path) -> None:
        try:
            self.root.after(0, lambda: self.progress_label.configure(
                text="Conectando e preparando fragmentos... pode levar alguns segundos."))
            self._proc = subprocess.Popen(
                cmdline, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                text=True, encoding="utf-8", errors="replace", bufsize=1,
                creationflags=CREATIONFLAGS,
            )
            progress_re = re.compile(r"\[download\]\s+([\d.]+)%")
            for line in self._proc.stdout:  # type: ignore[union-attr]
                line = line.rstrip()
                if not line:
                    continue
                # captura caminho final via --print after_move
                if line.startswith("DECREEPY_FILE:"):
                    self._final_file = Path(line[len("DECREEPY_FILE:"):])
                    continue
                m = progress_re.search(line)
                if m:
                    pct = float(m.group(1))
                    self.root.after(0, self._update_progress, pct, line)
                else:
                    self.root.after(0, lambda l=line: self.progress_label.configure(text=l[:120]))
                if any(t in line for t in ("ERROR", "WARNING", "[Merger]", "[ExtractAudio]",
                                           "Destination:", "has already been downloaded")):
                    self._log(line, "err" if "ERROR" in line else "info")
            rc = self._proc.wait()
            self.root.after(0, self._download_done, rc == 0, dest)
        except Exception as e:
            self._log(f"[ex] {e}", "err")
            self.root.after(0, self._download_done, False, dest)

    def _update_progress(self, pct: float, line: str) -> None:
        self.progress["value"] = pct
        self.progress_label.configure(text=line[:120])

    def _download_done(self, ok: bool, dest: Path) -> None:
        self._proc = None
        if not ok:
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            self.progress_label.configure(text="Falhou — veja o log.")
            self._log("[err] Download falhou.", "err")
            return

        self.progress["value"] = 100
        self._log("[ok] Download concluído.", "ok")

        # se WhatsApp ativado e temos arquivo de vídeo (não MP3), reencoda
        do_whatsapp = (self.whatsapp_var.get()
                       and not self.audio_only_var.get()
                       and self._final_file is not None
                       and self._final_file.exists())
        if do_whatsapp:
            self._start_whatsapp_encode(self._final_file)
        else:
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            if self._final_file:
                self.progress_label.configure(
                    text=f"Concluído: {self._final_file.name}")
            else:
                self.progress_label.configure(text=f"Concluído. Salvo em: {dest}")

    # ---------- WhatsApp re-encode ----------
    def _start_whatsapp_encode(self, src: Path) -> None:
        if not self.ffmpeg_path:
            self._log("[!] ffmpeg ausente — pulando otimização WhatsApp.", "err")
            self.download_btn.configure(state="normal")
            self.cancel_btn.configure(state="disabled")
            return
        out = src.with_name(src.stem + "_whatsapp.mp4")
        self.progress["value"] = 0
        self.progress_label.configure(text="Otimizando para WhatsApp (re-encode H.264 + AAC)...")
        self._log(f"[..] WhatsApp encode -> {out.name}", "info")
        threading.Thread(target=self._whatsapp_encode_worker,
                         args=(src, out), daemon=True).start()

    def _whatsapp_encode_worker(self, src: Path, out: Path) -> None:
        # duração pra calcular % (usa ffprobe via ffmpeg -i parsing, mas mais fácil é self.video_duration)
        total_sec = self._whatsapp_duration_seconds(src)

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
            for line in self._proc.stdout:  # type: ignore[union-attr]
                line = line.strip()
                if not line:
                    continue
                # ffmpeg -progress imprime "out_time_us=12345678"
                if line.startswith("out_time_us="):
                    try:
                        us = int(line.split("=", 1)[1])
                        if total_sec > 0:
                            pct = min(99.0, (us / 1_000_000) / total_sec * 100)
                            self.root.after(0, self._update_progress, pct,
                                            f"WhatsApp encode: {pct:.1f}%")
                    except ValueError:
                        pass
                elif line.startswith("progress="):
                    if line.endswith("=end"):
                        break
                elif "Error" in line or "error" in line:
                    self._log(line, "err")
            rc = self._proc.wait()
            self.root.after(0, self._whatsapp_done, rc == 0, src, out)
        except Exception as e:
            self._log(f"[ex] WhatsApp encode: {e}", "err")
            self.root.after(0, self._whatsapp_done, False, src, out)

    def _whatsapp_duration_seconds(self, path: Path) -> float:
        # tenta self.video_duration (do verify) ou ffprobe via ffmpeg
        if self.video_duration > 0:
            return float(self.video_duration)
        try:
            r = subprocess.run(
                [self.ffmpeg_path, "-i", str(path)],
                capture_output=True, text=True, encoding="utf-8", errors="replace",
                creationflags=CREATIONFLAGS,
            )
            m = re.search(r"Duration:\s*(\d+):(\d+):(\d+\.\d+)", r.stderr or "")
            if m:
                return int(m.group(1)) * 3600 + int(m.group(2)) * 60 + float(m.group(3))
        except Exception:
            pass
        return 0.0

    def _whatsapp_done(self, ok: bool, src: Path, out: Path) -> None:
        self.download_btn.configure(state="normal")
        self.cancel_btn.configure(state="disabled")
        self._proc = None
        if ok and out.exists() and out.stat().st_size > 0:
            self.progress["value"] = 100
            size_mb = out.stat().st_size / (1024 * 1024)
            self.progress_label.configure(
                text=f"Pronto pra WhatsApp: {out.name} ({size_mb:.1f} MB)")
            self._log(f"[ok] WhatsApp encode concluído: {out.name} ({size_mb:.1f} MB)", "ok")
        else:
            self.progress_label.configure(text="Falha no encode WhatsApp — veja o log.")
            self._log("[err] WhatsApp encode falhou.", "err")

    def _cancel_download(self) -> None:
        if self._proc and self._proc.poll() is None:
            try:
                self._proc.terminate()
                self._log("[!] Cancelado pelo usuário.", "err")
            except Exception:
                pass

    def _on_close(self) -> None:
        # limpa cache de previews
        try:
            for f in CACHE_DIR.glob("_preview_*.png"):
                f.unlink()
        except Exception:
            pass
        self.root.destroy()


def main() -> None:
    root = Tk()
    DecreepyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()
