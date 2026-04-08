"""
Claude Usage Widget — "Pêtes un plomb" edition
Dark glassmorphism widget with arc gauges, neon yellow, and live data.
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

ORG_ID = "5621a0c7-7323-494e-b3b9-4cbcd7069f31"

JOURS_FR = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]

# ── Palette ──────────────────────────────────────────────────────────────────
BG = "#0d0d0d"
CARD_BG = "#1a1a2e"
CARD_BORDER = "#2a2a4a"
TEXT_PRIMARY = "#e0e0e0"
TEXT_DIM = "#666688"
TEXT_ACCENT = "#8888bb"
NEON = "#d4ff00"          # jaune fluo principal
NEON_DIM = "#3a4400"
GREEN = "#22c55e"
ORANGE = "#ff8a00"
RED = "#ef4444"
GAUGE_TRACK = "#1e1e3a"


def _format_reset(iso_str: str) -> str:
    try:
        reset_dt = datetime.fromisoformat(iso_str)
        now = datetime.now(timezone.utc)
        total = int((reset_dt - now).total_seconds())
        if total <= 0:
            return "Réinitialisé"
        if total < 3600:
            return f"Reset dans {total // 60}min"
        if total < 86400:
            h, m = divmod(total, 3600)
            return f"Reset dans {h}h{(m // 60):02d}"
        local_dt = reset_dt.astimezone()
        return f"Reset {JOURS_FR[local_dt.weekday()]} {local_dt.strftime('%H:%M')}"
    except Exception:
        return "--"


def _pct_color(pct):
    if pct < 50:
        return NEON
    if pct < 75:
        return ORANGE
    return RED


class ArcGauge:
    """Draws a single arc gauge on a canvas."""

    def __init__(self, canvas, cx, cy, radius, thickness=8):
        self.canvas = canvas
        self.cx = cx
        self.cy = cy
        self.r = radius
        self.thickness = thickness
        self._track_id = None
        self._arc_id = None
        self._text_id = None
        self._label_id = None
        self._sub_id = None
        self._draw_track()

    def _draw_track(self):
        x0, y0 = self.cx - self.r, self.cy - self.r
        x1, y1 = self.cx + self.r, self.cy + self.r
        self._track_id = self.canvas.create_arc(
            x0, y0, x1, y1, start=225, extent=-270,
            style="arc", width=self.thickness, outline=GAUGE_TRACK,
        )

    def update(self, pct, label="", sub="", color=None):
        pct = max(0, min(100, pct))
        color = color or _pct_color(pct)
        extent = -270 * (pct / 100)
        x0, y0 = self.cx - self.r, self.cy - self.r
        x1, y1 = self.cx + self.r, self.cy + self.r

        if self._arc_id:
            self.canvas.delete(self._arc_id)
        self._arc_id = self.canvas.create_arc(
            x0, y0, x1, y1, start=225, extent=extent,
            style="arc", width=self.thickness, outline=color,
        )

        if self._text_id:
            self.canvas.delete(self._text_id)
        self._text_id = self.canvas.create_text(
            self.cx, self.cy - 4,
            text=f"{int(pct)}%",
            fill=color, font=("Segoe UI", 14, "bold"),
        )

        if self._label_id:
            self.canvas.delete(self._label_id)
        self._label_id = self.canvas.create_text(
            self.cx, self.cy + self.r + 14,
            text=label, fill=TEXT_PRIMARY, font=("Segoe UI", 8),
        )

        if self._sub_id:
            self.canvas.delete(self._sub_id)
        self._sub_id = self.canvas.create_text(
            self.cx, self.cy + self.r + 28,
            text=sub, fill=TEXT_DIM, font=("Segoe UI", 7),
        )


class ClaudeWidget:
    def __init__(self):
        self.root = tk.Tk()
        self.session_key = ""
        self.org_id = ORG_ID
        self._after_id = None
        self._drag_data = {"x": 0, "y": 0}

        self.load_config()
        self.setup_window()
        self.setup_ui()
        self.start_refresh()
        self.root.mainloop()

    # ── Window (borderless) ──────────────────────────────────────────────────
    def setup_window(self):
        self.root.overrideredirect(True)  # Pas de barre de titre Windows
        self.root.geometry("340x530+40+40")
        self.root.attributes("-topmost", True)
        self.root.configure(bg=BG)

    def _start_drag(self, event):
        self._drag_data["x"] = event.x
        self._drag_data["y"] = event.y

    def _on_drag(self, event):
        x = self.root.winfo_x() + (event.x - self._drag_data["x"])
        y = self.root.winfo_y() + (event.y - self._drag_data["y"])
        self.root.geometry(f"+{x}+{y}")

    # ── UI ────────────────────────────────────────────────────────────────────
    def setup_ui(self):
        W = 340

        # ── Header (draggable) ──
        header = tk.Frame(self.root, bg=BG, height=44)
        header.pack(fill="x")
        header.pack_propagate(False)
        header.bind("<Button-1>", self._start_drag)
        header.bind("<B1-Motion>", self._on_drag)

        # Picto cerveau (dessiné sur canvas)
        brain_cv = tk.Canvas(header, width=28, height=28, bg=BG,
                             highlightthickness=0, bd=0)
        brain_cv.pack(side="left", padx=(14, 4), pady=6)
        brain_cv.bind("<Button-1>", self._start_drag)
        brain_cv.bind("<B1-Motion>", self._on_drag)
        self._draw_brain_icon(brain_cv)

        title_lbl = tk.Label(header, text="CLAUDE",
                             font=("Segoe UI", 11, "bold"), fg=NEON, bg=BG,
                             anchor="w")
        title_lbl.pack(side="left", pady=8)
        title_lbl.bind("<Button-1>", self._start_drag)
        title_lbl.bind("<B1-Motion>", self._on_drag)

        # Close button
        close_btn = tk.Label(header, text="✕", font=("Segoe UI", 10),
                             fg=TEXT_DIM, bg=BG, cursor="hand2")
        close_btn.pack(side="right", padx=14)
        close_btn.bind("<Button-1>", lambda e: self.root.destroy())
        close_btn.bind("<Enter>", lambda e: close_btn.config(fg=RED))
        close_btn.bind("<Leave>", lambda e: close_btn.config(fg=TEXT_DIM))

        # Minimize
        min_btn = tk.Label(header, text="—", font=("Segoe UI", 10),
                           fg=TEXT_DIM, bg=BG, cursor="hand2")
        min_btn.pack(side="right", padx=4)
        min_btn.bind("<Button-1>", lambda e: self.root.iconify())
        min_btn.bind("<Enter>", lambda e: min_btn.config(fg=TEXT_PRIMARY))
        min_btn.bind("<Leave>", lambda e: min_btn.config(fg=TEXT_DIM))

        # Status
        self.status_dot = tk.Label(header, text="●", font=("Segoe UI", 8),
                                   fg=GREEN, bg=BG)
        self.status_dot.pack(side="right", padx=(0, 8))
        tk.Label(header, text="LIVE", font=("Segoe UI", 7),
                 fg=TEXT_DIM, bg=BG).pack(side="right")

        # ── Separator ──
        tk.Frame(self.root, bg=CARD_BORDER, height=1).pack(fill="x")

        # ── Gauges canvas ──
        self.canvas = tk.Canvas(self.root, width=W, height=200,
                                bg=BG, highlightthickness=0, bd=0)
        self.canvas.pack()

        gauge_y = 80
        gauge_r = 40
        self.gauge_session = ArcGauge(self.canvas, 58, gauge_y, gauge_r, thickness=7)
        self.gauge_weekly = ArcGauge(self.canvas, W // 2, gauge_y, gauge_r, thickness=7)
        self.gauge_sonnet = ArcGauge(self.canvas, W - 58, gauge_y, gauge_r, thickness=7)

        # ── Separator ──
        tk.Frame(self.root, bg=CARD_BORDER, height=1).pack(fill="x", padx=20)

        # ── Credits card ──
        credits_frame = tk.Frame(self.root, bg=CARD_BG,
                                 highlightbackground=CARD_BORDER,
                                 highlightthickness=1, bd=0)
        credits_frame.pack(fill="x", padx=16, pady=(14, 0))

        credits_inner = tk.Frame(credits_frame, bg=CARD_BG)
        credits_inner.pack(fill="x", padx=16, pady=12)

        tk.Label(credits_inner, text="CRÉDITS PRÉPAYÉS",
                 font=("Segoe UI", 7, "bold"), fg=TEXT_DIM, bg=CARD_BG,
                 anchor="w").pack(anchor="w")

        self.credits_var = tk.StringVar(value="---.-- €")
        self.credits_label = tk.Label(credits_inner, textvariable=self.credits_var,
                                      font=("Consolas", 22, "bold"), fg=NEON,
                                      bg=CARD_BG, anchor="w")
        self.credits_label.pack(anchor="w", pady=(4, 0))

        self.credits_sub_var = tk.StringVar(value="")
        tk.Label(credits_inner, textvariable=self.credits_sub_var,
                 font=("Segoe UI", 8), fg=TEXT_DIM, bg=CARD_BG,
                 anchor="w").pack(anchor="w")

        # ── Extra usage card ──
        extra_frame = tk.Frame(self.root, bg=CARD_BG,
                               highlightbackground=CARD_BORDER,
                               highlightthickness=1, bd=0)
        extra_frame.pack(fill="x", padx=16, pady=(8, 0))

        extra_inner = tk.Frame(extra_frame, bg=CARD_BG)
        extra_inner.pack(fill="x", padx=16, pady=10)

        tk.Label(extra_inner, text="USAGE SUPPLÉMENTAIRE",
                 font=("Segoe UI", 7, "bold"), fg=TEXT_DIM, bg=CARD_BG,
                 anchor="w").pack(anchor="w")

        self.extra_var = tk.StringVar(value="Désactivé")
        tk.Label(extra_inner, textvariable=self.extra_var,
                 font=("Segoe UI", 9), fg=TEXT_ACCENT, bg=CARD_BG,
                 anchor="w").pack(anchor="w", pady=(2, 0))

        self.extra_bar_canvas = tk.Canvas(extra_inner, width=276, height=6,
                                          bg=GAUGE_TRACK, highlightthickness=0, bd=0)
        self.extra_bar_canvas.pack(anchor="w", pady=(4, 0))

        # ── Footer ──
        footer = tk.Frame(self.root, bg=BG)
        footer.pack(fill="x", padx=16, pady=(12, 10))

        self.updated_var = tk.StringVar(value="Chargement...")
        tk.Label(footer, textvariable=self.updated_var,
                 font=("Segoe UI", 7), fg=TEXT_DIM, bg=BG,
                 anchor="w").pack(side="left")

        # Signature
        tk.Label(footer, text="By GF — 2026 Claude Widget",
                 font=("Segoe UI", 7, "bold"), fg=NEON, bg=BG,
                 anchor="e").pack(side="right")

        # Refresh button (above footer, right side)
        refresh_btn = tk.Label(footer, text="↺", font=("Segoe UI", 14),
                               fg=TEXT_DIM, bg=BG, cursor="hand2")
        refresh_btn.pack(side="right", padx=(0, 8))
        refresh_btn.bind("<Button-1>", lambda e: self.manual_refresh())
        refresh_btn.bind("<Enter>", lambda e: refresh_btn.config(fg=NEON))
        refresh_btn.bind("<Leave>", lambda e: refresh_btn.config(fg=TEXT_DIM))

    # ── Brain icon ────────────────────────────────────────────────────────────
    @staticmethod
    def _draw_brain_icon(cv):
        """Draw a stylized head silhouette with brain inside."""
        c = NEON
        # Head outline (oval)
        cv.create_oval(4, 2, 24, 26, outline=c, width=1.5)
        # Brain left hemisphere
        cv.create_arc(7, 6, 15, 16, start=0, extent=180,
                      style="arc", outline=c, width=1.3)
        cv.create_arc(7, 10, 15, 20, start=180, extent=180,
                      style="arc", outline=c, width=1.3)
        # Brain right hemisphere
        cv.create_arc(13, 6, 21, 16, start=0, extent=180,
                      style="arc", outline=c, width=1.3)
        cv.create_arc(13, 10, 21, 20, start=180, extent=180,
                      style="arc", outline=c, width=1.3)
        # Brain stem
        cv.create_line(14, 20, 14, 24, fill=c, width=1.3)

    # ── Config ────────────────────────────────────────────────────────────────
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE) as fh:
                    cfg = json.load(fh)
                    self.session_key = cfg.get("session_key", "")
                    self.org_id = cfg.get("org_id", ORG_ID)
            except Exception:
                pass

    # ── Fetch ─────────────────────────────────────────────────────────────────
    def _api_get(self, url):
        cookies = {"sessionKey": self.session_key, "lastActiveOrg": self.org_id}
        headers = {"Accept": "application/json, */*",
                   "Referer": "https://claude.ai/settings/usage"}
        resp = cffi_requests.get(url, headers=headers, cookies=cookies,
                                 impersonate="chrome", timeout=15)
        if resp.status_code == 200:
            return resp.json()
        return None

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
        if error:
            self.updated_var.set(f"Erreur : {error}")
            self.status_dot.config(fg=RED)
            return

        fh = usage.get("five_hour") or {}
        sd = usage.get("seven_day") or {}
        ss = usage.get("seven_day_sonnet") or {}

        s_pct = fh.get("utilization", 0) or 0
        w_pct = sd.get("utilization", 0) or 0
        n_pct = ss.get("utilization", 0) or 0

        self.gauge_session.update(
            s_pct, "Session", _format_reset(fh.get("resets_at", "")),
            color=_pct_color(s_pct))
        self.gauge_weekly.update(
            w_pct, "Tous modèles", _format_reset(sd.get("resets_at", "")),
            color=_pct_color(w_pct))
        self.gauge_sonnet.update(
            n_pct, "Sonnet", _format_reset(ss.get("resets_at", "")),
            color=_pct_color(n_pct))

        # Credits
        if credits:
            amount = credits.get("amount", 0) / 100
            currency = credits.get("currency", "EUR")
            symbol = "€" if currency == "EUR" else "$"
            color = NEON if amount > 50 else ORANGE if amount > 10 else RED
            self.credits_var.set(f"{amount:,.2f} {symbol}".replace(",", " "))
            self.credits_label.config(fg=color)

            auto_reload = credits.get("auto_reload_settings")
            if auto_reload:
                self.credits_sub_var.set("Rechargement auto activé")
            else:
                self.credits_sub_var.set("Rechargement auto désactivé")
        else:
            self.credits_var.set("N/A")
            self.credits_sub_var.set("")

        # Extra usage
        extra = usage.get("extra_usage") or {}
        if extra.get("is_enabled"):
            used = extra.get("used_credits") or 0
            limit = extra.get("monthly_limit") or 1
            pct = extra.get("utilization") or 0
            self.extra_var.set(f"{used / 100:.2f} € / {limit / 100:.0f} €  —  {pct:.0f}%")
            self._draw_extra_bar(pct)
        else:
            self.extra_var.set("Désactivé")
            self._draw_extra_bar(0)

        self.status_dot.config(fg=GREEN)
        ts = datetime.now().strftime("%H:%M:%S")
        self.updated_var.set(f"Mis à jour à {ts}")

    def _draw_extra_bar(self, pct):
        self.extra_bar_canvas.delete("fill")
        if pct > 0:
            w = int(276 * min(pct, 100) / 100)
            color = _pct_color(pct)
            self.extra_bar_canvas.create_rectangle(
                0, 0, w, 6, fill=color, outline="", tags="fill")

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
        self.updated_var.set("Chargement...")
        self.status_dot.config(fg=ORANGE)
        self.start_refresh()


if __name__ == "__main__":
    ClaudeWidget()
