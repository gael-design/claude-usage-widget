"""
Claude Usage Widget — "Pêtes un plomb" edition
Dark glassmorphism widget with arc gauges, 5 themes, and live data.
By GF - 2026
"""

import tkinter as tk
import json
import threading
import os
from datetime import datetime, timezone
from curl_cffi import requests as cffi_requests

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
REFRESH_MS = 5 * 60 * 1000
ORG_ID = ""

# ── Themes ───────────────────────────────────────────────────────────────────
THEMES = {
    "neon_volt": {
        "name": "Neon Volt",
        "bg": "#0d0d0d",
        "card_bg": "#1a1a2e",
        "card_border": "#2a2a4a",
        "text_primary": "#e0e0e0",
        "text_dim": "#666688",
        "text_accent": "#8888bb",
        "accent": "#d4ff00",
        "green": "#22c55e",
        "orange": "#ff8a00",
        "red": "#ef4444",
        "gauge_track": "#1e1e3a",
        "swatch": "#d4ff00",
    },
    "cyberpunk": {
        "name": "Cyberpunk",
        "bg": "#0a0a12",
        "card_bg": "#160a22",
        "card_border": "#3d1a5c",
        "text_primary": "#e8d5f5",
        "text_dim": "#7a5599",
        "text_accent": "#bb88dd",
        "accent": "#ff2d8a",
        "green": "#22c55e",
        "orange": "#ff8a00",
        "red": "#ff0055",
        "gauge_track": "#2a1040",
        "swatch": "#ff2d8a",
    },
    "matrix": {
        "name": "Matrix",
        "bg": "#000000",
        "card_bg": "#001a00",
        "card_border": "#003300",
        "text_primary": "#b0ffb0",
        "text_dim": "#337733",
        "text_accent": "#66cc66",
        "accent": "#00ff41",
        "green": "#00ff41",
        "orange": "#ffcc00",
        "red": "#ff3333",
        "gauge_track": "#0a1f0a",
        "swatch": "#00ff41",
    },
    "arctic": {
        "name": "Arctic",
        "bg": "#0a1628",
        "card_bg": "#0f2140",
        "card_border": "#1a3a66",
        "text_primary": "#c8ddf0",
        "text_dim": "#4477aa",
        "text_accent": "#77aacc",
        "accent": "#00e5ff",
        "green": "#22c55e",
        "orange": "#ffaa00",
        "red": "#ff4466",
        "gauge_track": "#122244",
        "swatch": "#00e5ff",
    },
    "inferno": {
        "name": "Inferno",
        "bg": "#0d0806",
        "card_bg": "#1a0f0a",
        "card_border": "#3d2211",
        "text_primary": "#f0d8c8",
        "text_dim": "#886644",
        "text_accent": "#cc8855",
        "accent": "#ff4500",
        "green": "#44cc44",
        "orange": "#ffaa00",
        "red": "#ff2200",
        "gauge_track": "#221100",
        "swatch": "#ff4500",
    },
}

THEME_ORDER = ["neon_volt", "cyberpunk", "matrix", "arctic", "inferno"]

# ── i18n ─────────────────────────────────────────────────────────────────────
LANGS = {
    "fr": {
        "days": ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."],
        "reset_done": "Réinitialisé",
        "reset_in": "Reset dans",
        "reset_prefix": "Reset",
        "session": "Session",
        "all_models": "Tous modèles",
        "sonnet": "Sonnet",
        "prepaid_credits": "CRÉDITS PRÉPAYÉS",
        "extra_usage": "USAGE SUPPLÉMENTAIRE",
        "disabled": "Désactivé",
        "auto_reload_on": "Rechargement auto activé",
        "auto_reload_off": "Rechargement auto désactivé",
        "updated_at": "Mis à jour à",
        "loading": "Chargement...",
        "error": "Erreur",
        "used": "utilisé",
        "setup_title": "Claude Widget — Configuration",
        "setup_welcome": (
            "Bienvenue !\n\n"
            "Pour fonctionner, le widget a besoin de deux infos "
            "depuis ton navigateur :\n\n"
            "1. sessionKey\n"
            "2. Organization ID\n\n"
            "Ouvre claude.ai dans Chrome, puis :\n"
            "  F12 → Application → Cookies → claude.ai\n\n"
            "Clique OK pour continuer."
        ),
        "setup_session_prompt": "Colle la valeur du cookie « sessionKey » :\n(commence par sk-ant-...)",
        "setup_org_prompt": "Colle la valeur du cookie « lastActiveOrg » :\n(format : xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
        "setup_error_key": "sessionKey requis. Le widget va se fermer.",
        "setup_error_org": "Org ID requis. Le widget va se fermer.",
        "setup_done": "Configuration sauvegardée dans config.json.\nLe widget va démarrer.",
    },
    "en": {
        "days": ["Mon.", "Tue.", "Wed.", "Thu.", "Fri.", "Sat.", "Sun."],
        "reset_done": "Reset",
        "reset_in": "Reset in",
        "reset_prefix": "Reset",
        "session": "Session",
        "all_models": "All models",
        "sonnet": "Sonnet",
        "prepaid_credits": "PREPAID CREDITS",
        "extra_usage": "EXTRA USAGE",
        "disabled": "Disabled",
        "auto_reload_on": "Auto-reload enabled",
        "auto_reload_off": "Auto-reload disabled",
        "updated_at": "Updated at",
        "loading": "Loading...",
        "error": "Error",
        "used": "used",
        "setup_title": "Claude Widget — Setup",
        "setup_welcome": (
            "Welcome!\n\n"
            "The widget needs two values from your browser:\n\n"
            "1. sessionKey\n"
            "2. Organization ID\n\n"
            "Open claude.ai in Chrome, then:\n"
            "  F12 → Application → Cookies → claude.ai\n\n"
            "Click OK to continue."
        ),
        "setup_session_prompt": "Paste the value of the « sessionKey » cookie:\n(starts with sk-ant-...)",
        "setup_org_prompt": "Paste the value of the « lastActiveOrg » cookie:\n(format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
        "setup_error_key": "sessionKey required. The widget will close.",
        "setup_error_org": "Org ID required. The widget will close.",
        "setup_done": "Configuration saved to config.json.\nThe widget will start.",
    },
    "es": {
        "days": ["lun.", "mar.", "mié.", "jue.", "vie.", "sáb.", "dom."],
        "reset_done": "Reiniciado",
        "reset_in": "Reset en",
        "reset_prefix": "Reset",
        "session": "Sesión",
        "all_models": "Todos modelos",
        "sonnet": "Sonnet",
        "prepaid_credits": "CRÉDITOS PREPAGO",
        "extra_usage": "USO ADICIONAL",
        "disabled": "Desactivado",
        "auto_reload_on": "Recarga automática activada",
        "auto_reload_off": "Recarga automática desactivada",
        "updated_at": "Actualizado a las",
        "loading": "Cargando...",
        "error": "Error",
        "used": "usado",
        "setup_title": "Claude Widget — Configuración",
        "setup_welcome": (
            "¡Bienvenido!\n\n"
            "El widget necesita dos datos de tu navegador:\n\n"
            "1. sessionKey\n"
            "2. Organization ID\n\n"
            "Abre claude.ai en Chrome, luego:\n"
            "  F12 → Application → Cookies → claude.ai\n\n"
            "Haz clic en OK para continuar."
        ),
        "setup_session_prompt": "Pega el valor de la cookie « sessionKey »:\n(empieza por sk-ant-...)",
        "setup_org_prompt": "Pega el valor de la cookie « lastActiveOrg »:\n(formato: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
        "setup_error_key": "sessionKey requerido. El widget se cerrará.",
        "setup_error_org": "Org ID requerido. El widget se cerrará.",
        "setup_done": "Configuración guardada en config.json.\nEl widget se iniciará.",
    },
    "de": {
        "days": ["Mo.", "Di.", "Mi.", "Do.", "Fr.", "Sa.", "So."],
        "reset_done": "Zurückgesetzt",
        "reset_in": "Reset in",
        "reset_prefix": "Reset",
        "session": "Sitzung",
        "all_models": "Alle Modelle",
        "sonnet": "Sonnet",
        "prepaid_credits": "PREPAID-GUTHABEN",
        "extra_usage": "ZUSÄTZLICHE NUTZUNG",
        "disabled": "Deaktiviert",
        "auto_reload_on": "Auto-Aufladung aktiviert",
        "auto_reload_off": "Auto-Aufladung deaktiviert",
        "updated_at": "Aktualisiert um",
        "loading": "Laden...",
        "error": "Fehler",
        "used": "genutzt",
        "setup_title": "Claude Widget — Einrichtung",
        "setup_welcome": (
            "Willkommen!\n\n"
            "Das Widget benötigt zwei Werte aus deinem Browser:\n\n"
            "1. sessionKey\n"
            "2. Organization ID\n\n"
            "Öffne claude.ai in Chrome, dann:\n"
            "  F12 → Application → Cookies → claude.ai\n\n"
            "Klicke OK um fortzufahren."
        ),
        "setup_session_prompt": "Füge den Wert des Cookies « sessionKey » ein:\n(beginnt mit sk-ant-...)",
        "setup_org_prompt": "Füge den Wert des Cookies « lastActiveOrg » ein:\n(Format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx)",
        "setup_error_key": "sessionKey erforderlich. Das Widget wird geschlossen.",
        "setup_error_org": "Org ID erforderlich. Das Widget wird geschlossen.",
        "setup_done": "Konfiguration in config.json gespeichert.\nDas Widget wird gestartet.",
    },
}


# ── Helpers ──────────────────────────────────────────────────────────────────
def _format_reset(iso_str: str, t: dict) -> str:
    try:
        reset_dt = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        total = int((reset_dt - now).total_seconds())
        if total <= 0:
            return t["reset_done"]
        if total < 3600:
            return f"{t['reset_in']} {total // 60}min"
        if total < 86400:
            h, m = divmod(total, 3600)
            return f"{t['reset_in']} {h}h{(m // 60):02d}"
        local_dt = reset_dt.astimezone()
        day = t["days"][local_dt.weekday()]
        return f"{t['reset_prefix']} {day} {local_dt.strftime('%H:%M')}"
    except Exception:
        return "--"


def _pct_color(pct, th):
    if pct < 50:
        return th["accent"]
    if pct < 75:
        return th["orange"]
    return th["red"]


# ── Arc Gauge ────────────────────────────────────────────────────────────────
class ArcGauge:
    def __init__(self, canvas, cx, cy, radius, thickness=8, track_color="#1e1e3a"):
        self.canvas = canvas
        self.cx, self.cy, self.r = cx, cy, radius
        self.thickness = thickness
        self._ids = []
        x0, y0 = cx - radius, cy - radius
        x1, y1 = cx + radius, cy + radius
        self._track = canvas.create_arc(
            x0, y0, x1, y1, start=225, extent=-270,
            style="arc", width=thickness, outline=track_color)

    def set_track_color(self, color):
        self.canvas.itemconfig(self._track, outline=color)

    def update(self, pct, label="", sub="", color="#ffffff",
               text_primary="#e0e0e0", text_dim="#666688"):
        pct = max(0, min(100, pct))
        extent = -270 * (pct / 100)
        x0, y0 = self.cx - self.r, self.cy - self.r
        x1, y1 = self.cx + self.r, self.cy + self.r

        for i in self._ids:
            self.canvas.delete(i)
        self._ids = [
            self.canvas.create_arc(
                x0, y0, x1, y1, start=225, extent=extent,
                style="arc", width=self.thickness, outline=color),
            self.canvas.create_text(
                self.cx, self.cy - 4,
                text=f"{int(pct)}%", fill=color, font=("Segoe UI", 14, "bold")),
            self.canvas.create_text(
                self.cx, self.cy + self.r + 14,
                text=label, fill=text_primary, font=("Segoe UI", 8)),
            self.canvas.create_text(
                self.cx, self.cy + self.r + 28,
                text=sub, fill=text_dim, font=("Segoe UI", 7)),
        ]


# ── Widget ───────────────────────────────────────────────────────────────────
class ClaudeWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.session_key = ""
        self.org_id = ORG_ID
        self.lang = "fr"
        self.theme_name = "neon_volt"
        self._after_id = None
        self._drag_data = {"x": 0, "y": 0}
        self._last_usage = None
        self._last_credits = None
        self._main_frame = None

        self.load_config()
        self.root.overrideredirect(True)
        self.root.geometry("340x530+40+40")
        self.root.attributes("-topmost", True)
        self._build_ui()
        self.start_refresh()
        self.root.mainloop()

    @property
    def th(self):
        return THEMES[self.theme_name]

    @property
    def _t(self):
        return LANGS[self.lang]

    # ── Build / rebuild UI ────────────────────────────────────────────────────
    def _build_ui(self):
        if self._main_frame:
            self._main_frame.destroy()

        th = self.th
        t = self._t
        self.root.configure(bg=th["bg"])

        self._main_frame = tk.Frame(self.root, bg=th["bg"])
        self._main_frame.pack(fill="both", expand=True)
        f = self._main_frame
        W = 340

        # ── Header ──
        header = tk.Frame(f, bg=th["bg"], height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)

        brain_cv = tk.Canvas(header, width=28, height=28, bg=th["bg"],
                             highlightthickness=0, bd=0)
        brain_cv.pack(side="left", padx=(14, 4), pady=6)
        brain_cv.bind("<Button-1>", self._start_drag)
        brain_cv.bind("<B1-Motion>", self._on_drag)
        self._draw_brain_icon(brain_cv, th["accent"])

        title = tk.Label(header, text="CLAUDE",
                         font=("Segoe UI", 11, "bold"), fg=th["accent"], bg=th["bg"])
        title.pack(side="left", pady=8)
        title.bind("<Button-1>", self._start_drag)
        title.bind("<B1-Motion>", self._on_drag)

        # Close
        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 10),
                             fg=th["text_dim"], bg=th["bg"], cursor="hand2")
        close_btn.pack(side="right", padx=14)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=th["red"]))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=th["text_dim"]))

        # Minimize
        min_btn = tk.Label(header, text="—", font=("Segoe UI", 10),
                           fg=th["text_dim"], bg=th["bg"], cursor="hand2")
        min_btn.pack(side="right", padx=4)
        min_btn.bind("<Button-1>", lambda e: self.root.iconify())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=th["text_primary"]))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=th["text_dim"]))

        # Theme button
        theme_btn = tk.Label(header, text="◆", font=("Segoe UI", 11),
                             fg=th["accent"], bg=th["bg"], cursor="hand2")
        theme_btn.pack(side="right", padx=4)
        theme_btn.bind("<Button-1>", lambda e: self._show_theme_picker())
        theme_btn.bind("<Enter>", lambda e: theme_btn.config(fg=th["text_primary"]))
        theme_btn.bind("<Leave>", lambda e: theme_btn.config(fg=th["accent"]))

        # Status
        self.status_dot = tk.Label(header, text="●", font=("Segoe UI", 8),
                                   fg=th["green"], bg=th["bg"])
        self.status_dot.pack(side="right", padx=(0, 8))
        tk.Label(header, text="LIVE", font=("Segoe UI", 7),
                 fg=th["text_dim"], bg=th["bg"]).pack(side="right")

        tk.Frame(f, bg=th["card_border"], height=1).pack(fill="x")

        # ── Gauges ──
        self.canvas = tk.Canvas(f, width=W, height=200,
                                bg=th["bg"], highlightthickness=0, bd=0)
        self.canvas.pack()

        gy, gr = 80, 40
        self.gauge_session = ArcGauge(self.canvas, 58, gy, gr, 7, th["gauge_track"])
        self.gauge_weekly = ArcGauge(self.canvas, W // 2, gy, gr, 7, th["gauge_track"])
        self.gauge_sonnet = ArcGauge(self.canvas, W - 58, gy, gr, 7, th["gauge_track"])

        tk.Frame(f, bg=th["card_border"], height=1).pack(fill="x", padx=20)

        # ── Credits ──
        cf = tk.Frame(f, bg=th["card_bg"], highlightbackground=th["card_border"],
                      highlightthickness=1, bd=0)
        cf.pack(fill="x", padx=16, pady=(14, 0))
        ci = tk.Frame(cf, bg=th["card_bg"])
        ci.pack(fill="x", padx=16, pady=12)

        tk.Label(ci, text=t["prepaid_credits"], font=("Segoe UI", 7, "bold"),
                 fg=th["text_dim"], bg=th["card_bg"], anchor="w").pack(anchor="w")

        self.credits_var = tk.StringVar(value="---.-- €")
        self.credits_label = tk.Label(ci, textvariable=self.credits_var,
                                      font=("Consolas", 22, "bold"), fg=th["accent"],
                                      bg=th["card_bg"], anchor="w")
        self.credits_label.pack(anchor="w", pady=(4, 0))

        self.credits_sub_var = tk.StringVar(value="")
        tk.Label(ci, textvariable=self.credits_sub_var, font=("Segoe UI", 8),
                 fg=th["text_dim"], bg=th["card_bg"], anchor="w").pack(anchor="w")

        # ── Extra usage ──
        ef = tk.Frame(f, bg=th["card_bg"], highlightbackground=th["card_border"],
                      highlightthickness=1, bd=0)
        ef.pack(fill="x", padx=16, pady=(8, 0))
        ei = tk.Frame(ef, bg=th["card_bg"])
        ei.pack(fill="x", padx=16, pady=10)

        tk.Label(ei, text=t["extra_usage"], font=("Segoe UI", 7, "bold"),
                 fg=th["text_dim"], bg=th["card_bg"], anchor="w").pack(anchor="w")

        self.extra_var = tk.StringVar(value=t["disabled"])
        tk.Label(ei, textvariable=self.extra_var, font=("Segoe UI", 9),
                 fg=th["text_accent"], bg=th["card_bg"], anchor="w"
                 ).pack(anchor="w", pady=(2, 0))

        self.extra_bar_canvas = tk.Canvas(ei, width=276, height=6,
                                          bg=th["gauge_track"], highlightthickness=0, bd=0)
        self.extra_bar_canvas.pack(anchor="w", pady=(4, 0))

        # ── Footer ──
        footer = tk.Frame(f, bg=th["bg"])
        footer.pack(fill="x", padx=16, pady=(12, 10))

        self.updated_var = tk.StringVar(value=t["loading"])
        tk.Label(footer, textvariable=self.updated_var, font=("Segoe UI", 7),
                 fg=th["text_dim"], bg=th["bg"], anchor="w").pack(side="left")

        tk.Label(footer, text="By GF — 2026 Claude Widget",
                 font=("Segoe UI", 7, "bold"), fg=th["accent"], bg=th["bg"],
                 anchor="e").pack(side="right")

        accent = th["accent"]
        dim = th["text_dim"]
        refresh_btn = tk.Label(footer, text="↺", font=("Segoe UI", 14),
                               fg=dim, bg=th["bg"], cursor="hand2")
        refresh_btn.pack(side="right", padx=(0, 8))
        refresh_btn.bind("<Button-1>", lambda e: self.manual_refresh())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg=accent))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg=dim))

        # Re-apply cached data if we have it (theme switch)
        if self._last_usage:
            self.update_ui(self._last_usage, self._last_credits, None)

    # ── Theme picker ──────────────────────────────────────────────────────────
    def _show_theme_picker(self):
        th = self.th
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)

        # Position next to widget
        x = self.root.winfo_x() + self.root.winfo_width() + 6
        y = self.root.winfo_y()
        popup.geometry(f"160x280+{x}+{y}")
        popup.configure(bg=th["bg"])

        # Border frame
        border = tk.Frame(popup, bg=th["card_border"])
        border.pack(fill="both", expand=True, padx=1, pady=1)
        inner = tk.Frame(border, bg=th["bg"])
        inner.pack(fill="both", expand=True, padx=0, pady=0)

        tk.Label(inner, text="THEME", font=("Segoe UI", 9, "bold"),
                 fg=th["text_dim"], bg=th["bg"]).pack(pady=(12, 8))

        for key in THEME_ORDER:
            t = THEMES[key]
            is_active = key == self.theme_name

            row = tk.Frame(inner, bg=th["bg"])
            row.pack(fill="x", padx=12, pady=3)

            # Color swatch
            swatch = tk.Canvas(row, width=16, height=16, bg=th["bg"],
                               highlightthickness=0, bd=0)
            swatch.pack(side="left", padx=(0, 8))
            swatch.create_rectangle(1, 1, 15, 15, fill=t["swatch"],
                                     outline=t["swatch"])

            # Name
            name_fg = th["text_primary"] if is_active else th["text_dim"]
            name_font = ("Segoe UI", 9, "bold") if is_active else ("Segoe UI", 9)
            lbl = tk.Label(row, text=t["name"], font=name_font,
                           fg=name_fg, bg=th["bg"], cursor="hand2", anchor="w")
            lbl.pack(side="left", fill="x")

            # Active indicator
            if is_active:
                tk.Label(row, text="●", font=("Segoe UI", 7),
                         fg=t["swatch"], bg=th["bg"]).pack(side="right")

            # Bind click
            _key = key

            def on_click(e, k=_key, p=popup):
                p.destroy()
                self._apply_theme(k)

            lbl.bind("<Button-1>", on_click)
            swatch.bind("<Button-1>", on_click)
            row.bind("<Button-1>", on_click)

        # Close on click outside
        popup.bind("<FocusOut>", lambda e: popup.destroy())
        popup.focus_set()

    def _apply_theme(self, theme_name):
        if theme_name == self.theme_name:
            return
        self.theme_name = theme_name
        self._save_config()
        self._build_ui()

    # ── Brain icon ────────────────────────────────────────────────────────────
    @staticmethod
    def _draw_brain_icon(cv, color):
        cv.create_oval(4, 2, 24, 26, outline=color, width=1.5)
        cv.create_arc(7, 6, 15, 16, start=0, extent=180, style="arc", outline=color, width=1.3)
        cv.create_arc(7, 10, 15, 20, start=180, extent=180, style="arc", outline=color, width=1.3)
        cv.create_arc(13, 6, 21, 16, start=0, extent=180, style="arc", outline=color, width=1.3)
        cv.create_arc(13, 10, 21, 20, start=180, extent=180, style="arc", outline=color, width=1.3)
        cv.create_line(14, 20, 14, 24, fill=color, width=1.3)

    # ── Drag ──────────────────────────────────────────────────────────────────
    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_data["x"])
        y = self.root.winfo_y() + (event.y - self._drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    # ── Config ────────────────────────────────────────────────────────────────
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as fh:
                    cfg = json.load(fh)
                    self.session_key = cfg.get("session_key", "")
                    self.org_id = cfg.get("org_id", ORG_ID)
                    self.lang = cfg.get("lang", "fr")
                    self.theme_name = cfg.get("theme", "neon_volt")
                    if self.lang not in LANGS:
                        self.lang = "fr"
                    if self.theme_name not in THEMES:
                        self.theme_name = "neon_volt"
            except Exception:
                pass

        if not self.session_key or self.session_key == "PASTE_YOUR_SESSIONKEY_HERE":
            self._first_run_setup()

    def _first_run_setup(self):
        from tkinter import messagebox, simpledialog

        accent = THEMES[self.theme_name]["accent"]

        lang_win = tk.Toplevel(self.root)
        lang_win.title("Language")
        lang_win.geometry("280x200")
        lang_win.resizable(False, False)
        lang_win.attributes("-topmost", True)
        lang_win.configure(bg="#1a1a2e")
        lang_win.grab_set()

        tk.Label(lang_win, text="Choose language",
                 font=("Segoe UI", 11, "bold"), fg=accent, bg="#1a1a2e"
                 ).pack(pady=(16, 12))

        selected = tk.StringVar(value="fr")
        flags = {"fr": "Français", "en": "English",
                 "es": "Español", "de": "Deutsch"}

        for code, label in flags.items():
            tk.Radiobutton(lang_win, text=label, variable=selected, value=code,
                           font=("Segoe UI", 10), fg="#e0e0e0", bg="#1a1a2e",
                           selectcolor="#2a2a4a", activebackground="#2a2a4a",
                           activeforeground=accent, indicatoron=True,
                           anchor="w").pack(fill="x", padx=30)

        confirmed = {"done": False}

        def on_ok():
            confirmed["done"] = True
            lang_win.destroy()

        tk.Button(lang_win, text="OK", command=on_ok,
                  font=("Segoe UI", 10, "bold"), fg="#0d0d0d", bg=accent,
                  relief="flat", cursor="hand2", width=10).pack(pady=(12, 0))

        lang_win.wait_window()
        if not confirmed["done"]:
            self.root.destroy()
            raise SystemExit

        self.lang = selected.get()
        t = LANGS[self.lang]

        messagebox.showinfo(t["setup_title"], t["setup_welcome"])

        key = simpledialog.askstring("sessionKey", t["setup_session_prompt"])
        if not key or not key.strip():
            messagebox.showerror(t["error"], t["setup_error_key"])
            self.root.destroy()
            raise SystemExit

        org = simpledialog.askstring("Organization ID", t["setup_org_prompt"],
                                     initialvalue=ORG_ID)
        if not org or not org.strip():
            messagebox.showerror(t["error"], t["setup_error_org"])
            self.root.destroy()
            raise SystemExit

        self.session_key = key.strip()
        self.org_id = org.strip()
        self._save_config()
        messagebox.showinfo("OK", t["setup_done"])

    def _save_config(self):
        with open(CONFIG_FILE, "w") as fh:
            json.dump({
                "session_key": self.session_key,
                "org_id": self.org_id,
                "lang": self.lang,
                "theme": self.theme_name,
            }, fh, indent=2)

    # ── Fetch ─────────────────────────────────────────────────────────────────
    def _api_get(self, url):
        cookies = {"sessionKey": self.session_key, "lastActiveOrg": self.org_id}
        headers = {"Accept": "application/json, */*",
                   "Referer": "https://claude.ai/settings/usage"}
        resp = cffi_requests.get(url, headers=headers, cookies=cookies,
                                 impersonate="chrome", timeout=15)
        return resp.json() if resp.status_code == 200 else None

    def fetch_all(self):
        if not self.session_key:
            return None, None, "sessionKey absent"
        try:
            usage = self._api_get(
                f"https://claude.ai/api/organizations/{self.org_id}/usage")
            credits = self._api_get(
                f"https://claude.ai/api/organizations/{self.org_id}/prepaid/credits")
            if usage is None:
                return None, None, "API usage inaccessible"
            return usage, credits, None
        except Exception as e:
            return None, None, str(e)

    # ── Update UI ─────────────────────────────────────────────────────────────
    def update_ui(self, usage, credits, error):
        t = self._t
        th = self.th

        if error:
            self.updated_var.set(f"{t['error']} : {error}")
            self.status_dot.config(fg=th["red"])
            return

        self._last_usage = usage
        self._last_credits = credits

        fh = usage.get("five_hour") or {}
        sd = usage.get("seven_day") or {}
        ss = usage.get("seven_day_sonnet") or {}

        for gauge, data, label in [
            (self.gauge_session, fh, t["session"]),
            (self.gauge_weekly, sd, t["all_models"]),
            (self.gauge_sonnet, ss, t["sonnet"]),
        ]:
            pct = data.get("utilization", 0) or 0
            gauge.update(pct, label, _format_reset(data.get("resets_at", ""), t),
                         color=_pct_color(pct, th),
                         text_primary=th["text_primary"], text_dim=th["text_dim"])

        if credits:
            amount = credits.get("amount", 0) / 100
            symbol = "€" if credits.get("currency", "EUR") == "EUR" else "$"
            color = th["accent"] if amount > 50 else th["orange"] if amount > 10 else th["red"]
            self.credits_var.set(f"{amount:,.2f} {symbol}".replace(",", " "))
            self.credits_label.config(fg=color)
            self.credits_sub_var.set(
                t["auto_reload_on"] if credits.get("auto_reload_settings")
                else t["auto_reload_off"])
        else:
            self.credits_var.set("N/A")
            self.credits_sub_var.set("")

        extra = usage.get("extra_usage") or {}
        if extra.get("is_enabled"):
            used = extra.get("used_credits") or 0
            limit = extra.get("monthly_limit") or 1
            pct = extra.get("utilization") or 0
            self.extra_var.set(
                f"{used / 100:.2f} € / {limit / 100:.0f} €  —  {pct:.0f}% {t['used']}")
            self._draw_extra_bar(pct)
        else:
            self.extra_var.set(t["disabled"])
            self._draw_extra_bar(0)

        self.status_dot.config(fg=th["green"])
        self.updated_var.set(f"{t['updated_at']} {datetime.now().strftime('%H:%M:%S')}")

    def _draw_extra_bar(self, pct):
        self.extra_bar_canvas.delete("fill")
        if pct > 0:
            w = int(276 * min(pct, 100) / 100)
            self.extra_bar_canvas.create_rectangle(
                0, 0, w, 6, fill=_pct_color(pct, self.th), outline="", tags="fill")

    # ── Refresh ───────────────────────────────────────────────────────────────
    def start_refresh(self):
        threading.Thread(target=self._do_refresh, daemon=True).start()

    def _do_refresh(self):
        usage, credits, error = self.fetch_all()
        self.root.after(0, lambda: self.update_ui(usage, credits, error))
        self._after_id = self.root.after(REFRESH_MS, self.start_refresh)

    def manual_refresh(self):
        if self._after_id:
            self.root.after_cancel(self._after_id)
        self.updated_var.set(self._t["loading"])
        self.status_dot.config(fg=self.th["orange"])
        self.start_refresh()


if __name__ == "__main__":
    ClaudeWidget()
