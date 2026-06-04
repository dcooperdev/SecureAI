import tkinter as tk
from tkinter import font as tkfont
import sys
import logging
import threading
import webbrowser

from google import genai
from galt.core.config import save_api_key, save_llm_model, get_llm_model

# ── Color Palette ──────────────────────────────────────────────
BG_DEEP    = "#0D1117"
BG_CARD    = "#161B22"
BG_INPUT   = "#1C2333"
BG_BORDER  = "#30363D"
BG_HOVER   = "#21262D"

FG_WHITE   = "#E6EDF3"
FG_MUTED   = "#8B949E"
FG_ACCENT  = "#3FB950"   # green
FG_LINK    = "#58A6FF"   # blue
FG_ERROR   = "#F85149"   # red

BTN_GREEN  = "#238636"
BTN_GREEN_H= "#2EA043"
BTN_BORDER = "#3FB950"

AISTUDIO_URL = "https://aistudio.google.com/app/apikey"

# Available models — confirmed against the live Gemini API.
# (display_label, model_id, quota_hint)
MODELS = [
    ("Gemini 3.5 Flash ★",   "gemini-3.5-flash",        "Recommended · Latest gen · Free tier"),
    ("Gemini 3.1 Flash-Lite","gemini-3.1-flash-lite",   "Free tier · Highest quota · Lighter"),
    ("Gemini 3.0 Flash",     "gemini-3-flash-preview",  "Free tier · Preview"),
    ("Gemini 2.5 Flash",     "gemini-2.5-flash",        "Free tier · Stable"),
    ("Gemini 2.5 Flash-Lite","gemini-2.5-flash-lite",   "Free tier · High quota"),
    ("Gemini 2.0 Flash",     "gemini-2.0-flash",        "Free tier · Being deprecated"),
]


def validate_key(key: str) -> bool:
    """Live API validation — only called when the user submits."""
    if not key or len(key) < 20:
        return False
    try:
        client = genai.Client(api_key=key)
        next(iter(client.models.list(config={"page_size": 1})), None)
        return True
    except Exception as e:
        logging.warning(f"API Key validation failed: {e}")
        return False


class OnboardingWindow:
    """
    Modern, dark-themed onboarding dialog for first-run API key setup.
    Replaces the default Tkinter simpledialog with a fully custom UI.
    """

    STATES = ("idle", "validating", "success", "error")

    def __init__(self):
        self.result: bool = False
        self._anim_idx = 0
        self._anim_job = None
        self._state = "idle"

        # ── Root window ────────────────────────────────────────
        self.root = tk.Tk()
        self.root.title("Galt Security Agent — Setup")
        self.root.resizable(False, False)
        self.root.configure(bg=BG_DEEP)
        self.root.attributes("-topmost", True)

        self._center_window(520, 680)
        self._build_ui()

        self.root.protocol("WM_DELETE_WINDOW", self._on_cancel)

    # ── Layout ────────────────────────────────────────────────

    def _build_ui(self):
        # Outer padding frame
        outer = tk.Frame(self.root, bg=BG_DEEP)
        outer.pack(fill="both", expand=True, padx=1, pady=1)

        # Card frame
        card = tk.Frame(outer, bg=BG_CARD, bd=0)
        card.pack(fill="both", expand=True, padx=16, pady=16)

        self._build_header(card)
        self._build_divider(card)
        self._build_body(card)
        self._build_footer(card)

    def _build_header(self, parent):
        hdr = tk.Frame(parent, bg=BG_CARD)
        hdr.pack(fill="x", padx=28, pady=(28, 12))

        # Shield icon (Unicode, styled)
        shield = tk.Label(
            hdr, text="🛡", font=("Segoe UI Emoji", 32),
            bg=BG_CARD, fg=FG_ACCENT
        )
        shield.pack()

        tk.Label(
            hdr, text="Galt Security Agent",
            font=("Segoe UI", 17, "bold"),
            bg=BG_CARD, fg=FG_WHITE
        ).pack(pady=(6, 2))

        tk.Label(
            hdr, text="Initial setup — AI analysis requires a Gemini API key",
            font=("Segoe UI", 9),
            bg=BG_CARD, fg=FG_MUTED
        ).pack()

    def _build_divider(self, parent):
        tk.Frame(parent, bg=BG_BORDER, height=1).pack(fill="x", padx=28, pady=4)

    def _build_body(self, parent):
        body = tk.Frame(parent, bg=BG_CARD)
        body.pack(fill="x", padx=28, pady=(12, 8))

        # Label row
        lbl_row = tk.Frame(body, bg=BG_CARD)
        lbl_row.pack(fill="x", pady=(0, 6))

        tk.Label(
            lbl_row, text="Google Gemini API Key",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD, fg=FG_WHITE
        ).pack(side="left")

        # Link to get key
        link = tk.Label(
            lbl_row, text="Get a free key →",
            font=("Segoe UI", 9, "underline"),
            bg=BG_CARD, fg=FG_LINK, cursor="hand2"
        )
        link.pack(side="right")
        link.bind("<Button-1>", lambda e: webbrowser.open(AISTUDIO_URL))
        link.bind("<Enter>", lambda e: link.config(fg=FG_ACCENT))
        link.bind("<Leave>", lambda e: link.config(fg=FG_LINK))

        # Input frame (custom border)
        inp_border = tk.Frame(body, bg=BG_BORDER, bd=0)
        inp_border.pack(fill="x")

        inp_inner = tk.Frame(inp_border, bg=BG_INPUT, bd=0)
        inp_inner.pack(fill="x", padx=1, pady=1)

        self._key_var = tk.StringVar()
        self._key_var.trace_add("write", self._on_key_change)

        self._entry = tk.Entry(
            inp_inner,
            textvariable=self._key_var,
            show="•",
            font=("Consolas", 10),
            bg=BG_INPUT, fg=FG_WHITE,
            insertbackground=FG_WHITE,
            relief="flat", bd=6,
            width=38
        )
        self._entry.pack(side="left", fill="x", expand=True)
        self._entry.insert(0, "AIza...")
        self._entry.config(fg=FG_MUTED)
        self._entry.bind("<FocusIn>",  self._on_entry_focus_in)
        self._entry.bind("<FocusOut>", self._on_entry_focus_out)
        self._entry.bind("<Return>",   lambda e: self._submit())

        # Show/hide toggle
        self._show_key = False
        self._eye_btn = tk.Label(
            inp_inner, text="👁", font=("Segoe UI Emoji", 12),
            bg=BG_INPUT, fg=FG_MUTED, cursor="hand2", padx=8
        )
        self._eye_btn.pack(side="right")
        self._eye_btn.bind("<Button-1>", self._toggle_visibility)
        self._eye_btn.bind("<Enter>", lambda e: self._eye_btn.config(fg=FG_WHITE))
        self._eye_btn.bind("<Leave>", lambda e: self._eye_btn.config(fg=FG_MUTED))

        # Status / feedback label
        self._status_var = tk.StringVar(value="")
        self._status_lbl = tk.Label(
            body,
            textvariable=self._status_var,
            font=("Segoe UI", 8),
            bg=BG_CARD, fg=FG_MUTED
        )
        self._status_lbl.pack(anchor="w", pady=(6, 0))

        # ── Model Selector ──────────────────────────────────────
        tk.Frame(body, bg=BG_BORDER, height=1).pack(fill="x", pady=(14, 10))

        tk.Label(
            body, text="AI Model",
            font=("Segoe UI", 9, "bold"),
            bg=BG_CARD, fg=FG_WHITE
        ).pack(anchor="w")

        tk.Label(
            body,
            text="Select the Gemini model used for security analysis.",
            font=("Segoe UI", 8),
            bg=BG_CARD, fg=FG_MUTED
        ).pack(anchor="w", pady=(2, 8))

        # Radio-button style card list
        saved_model = get_llm_model()
        self._model_var = tk.StringVar(
            value=saved_model if any(m[1] == saved_model for m in MODELS) else MODELS[0][1]
        )

        for label, model_id, hint in MODELS:
            row = tk.Frame(body, bg=BG_INPUT, cursor="hand2")
            row.pack(fill="x", pady=2)

            # Radio bullet
            rb = tk.Radiobutton(
                row,
                variable=self._model_var,
                value=model_id,
                bg=BG_INPUT,
                activebackground=BG_HOVER,
                selectcolor=BG_INPUT,
                fg=FG_ACCENT,
                relief="flat",
                bd=0,
                cursor="hand2",
            )
            rb.pack(side="left", padx=(8, 0), pady=6)

            # Labels
            col = tk.Frame(row, bg=BG_INPUT)
            col.pack(side="left", padx=6, pady=6, fill="x", expand=True)

            tk.Label(
                col, text=label,
                font=("Segoe UI", 9, "bold"),
                bg=BG_INPUT, fg=FG_WHITE, anchor="w"
            ).pack(anchor="w")

            tk.Label(
                col, text=f"{model_id}  ·  {hint}",
                font=("Consolas", 7),
                bg=BG_INPUT, fg=FG_MUTED, anchor="w"
            ).pack(anchor="w")

            # Click on the whole row selects the model
            for widget in (row, col):
                widget.bind("<Button-1>", lambda e, m=model_id: self._model_var.set(m))

    def _build_footer(self, parent):
        foot = tk.Frame(parent, bg=BG_CARD)
        foot.pack(fill="x", padx=28, pady=(8, 24))

        # Validate button
        self._submit_btn = tk.Button(
            foot,
            text="Validate & Continue  →",
            font=("Segoe UI", 10, "bold"),
            bg=BTN_GREEN, fg=FG_WHITE,
            activebackground=BTN_GREEN_H, activeforeground=FG_WHITE,
            relief="flat", bd=0, padx=18, pady=9,
            cursor="hand2",
            command=self._submit
        )
        self._submit_btn.pack(fill="x", pady=(0, 10))
        self._submit_btn.bind("<Enter>", lambda e: self._submit_btn.config(bg=BTN_GREEN_H))
        self._submit_btn.bind("<Leave>", lambda e: self._submit_btn.config(bg=BTN_GREEN))

        # Skip link
        skip = tk.Label(
            foot,
            text="Skip — run in offline mode",
            font=("Segoe UI", 8, "underline"),
            bg=BG_CARD, fg=FG_MUTED, cursor="hand2"
        )
        skip.pack()
        skip.bind("<Button-1>", lambda e: self._on_cancel())
        skip.bind("<Enter>", lambda e: skip.config(fg=FG_WHITE))
        skip.bind("<Leave>", lambda e: skip.config(fg=FG_MUTED))

        tk.Label(
            foot,
            text="Your key is stored locally in ProgramData/GaltAI and never sent to our servers.",
            font=("Segoe UI", 7),
            bg=BG_CARD, fg="#484F58",
            wraplength=440
        ).pack(pady=(10, 0))

    # ── Logic ─────────────────────────────────────────────────

    def _on_entry_focus_in(self, _e):
        if self._entry.get() == "AIza...":
            self._entry.delete(0, "end")
            self._entry.config(fg=FG_WHITE)

    def _on_entry_focus_out(self, _e):
        if not self._entry.get():
            self._entry.insert(0, "AIza...")
            self._entry.config(fg=FG_MUTED)

    def _on_key_change(self, *_):
        if self._state in ("error", "success"):
            self._set_state("idle")

    def _toggle_visibility(self, _e=None):
        self._show_key = not self._show_key
        self._entry.config(show="" if self._show_key else "•")
        self._eye_btn.config(text="🙈" if self._show_key else "👁")

    def _submit(self):
        key = self._key_var.get().strip()

        if not key or key == "AIza...":
            self._set_state("error", "Please enter your API key.")
            self._entry.focus_set()
            return

        if len(key) < 20:
            self._set_state("error", "Key looks too short — double check it.")
            return

        self._set_state("validating")
        # Run validation off the main thread so the UI stays responsive
        threading.Thread(target=self._validate_thread, args=(key,), daemon=True).start()

    def _validate_thread(self, key: str):
        ok = validate_key(key)
        # Always schedule UI updates back on the main thread
        self.root.after(0, self._on_validation_done, key, ok)

    def _on_validation_done(self, key: str, ok: bool):
        if ok:
            self._set_state("success")
            save_api_key(key)
            save_llm_model(self._model_var.get())
            self.result = True
            self.root.after(900, self.root.destroy)
        else:
            self._set_state("error", "Invalid key or connection error. Check and retry.")

    def _on_cancel(self):
        self.result = False
        self.root.destroy()

    # ── State Machine ─────────────────────────────────────────

    def _set_state(self, state: str, message: str = ""):
        self._state = state
        self._stop_animation()

        if state == "idle":
            self._status_var.set(message)
            self._status_lbl.config(fg=FG_MUTED)
            self._submit_btn.config(state="normal", text="Validate & Continue  →", bg=BTN_GREEN)
            self._inp_set_border(BG_BORDER)

        elif state == "validating":
            self._submit_btn.config(state="disabled", text="Validating...", bg="#1B3A2D")
            self._inp_set_border("#58A6FF")
            self._start_animation()

        elif state == "success":
            self._status_var.set("✓  API key validated — launching Galt...")
            self._status_lbl.config(fg=FG_ACCENT)
            self._submit_btn.config(state="disabled", text="✓  Success", bg="#196127")
            self._inp_set_border(FG_ACCENT)

        elif state == "error":
            self._status_var.set(f"✕  {message}")
            self._status_lbl.config(fg=FG_ERROR)
            self._submit_btn.config(state="normal", text="Validate & Continue  →", bg=BTN_GREEN)
            self._inp_set_border(FG_ERROR)
            self._shake()

    def _inp_set_border(self, color: str):
        """Updates the 1-px border frame around the input."""
        try:
            self._entry.master.master.config(bg=color)
        except Exception:
            pass

    # ── Animations ────────────────────────────────────────────

    DOTS = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]

    def _start_animation(self):
        self._anim_idx = 0
        self._animate()

    def _animate(self):
        if self._state != "validating":
            return
        dot = self.DOTS[self._anim_idx % len(self.DOTS)]
        self._status_var.set(f"{dot}  Connecting to Gemini API...")
        self._status_lbl.config(fg=FG_LINK)
        self._anim_idx += 1
        self._anim_job = self.root.after(80, self._animate)

    def _stop_animation(self):
        if self._anim_job:
            self.root.after_cancel(self._anim_job)
            self._anim_job = None

    def _shake(self, count=6, delta=5):
        """Horizontal shake animation on validation error."""
        if count == 0:
            x, y = self._orig_x, self._orig_y
            self.root.geometry(f"+{x}+{y}")
            return
        direction = delta if count % 2 == 0 else -delta
        x = self._orig_x + direction
        self.root.geometry(f"+{x}+{self._orig_y}")
        self.root.after(40, lambda: self._shake(count - 1, delta))

    # ── Helpers ───────────────────────────────────────────────

    def _center_window(self, w: int, h: int):
        self.root.update_idletasks()
        sw = self.root.winfo_screenwidth()
        sh = self.root.winfo_screenheight()
        x = (sw - w) // 2
        y = (sh - h) // 2
        self._orig_x, self._orig_y = x, y
        self.root.geometry(f"{w}x{h}+{x}+{y}")

    def show(self) -> bool:
        self._entry.focus_set()
        self.root.mainloop()
        return self.result


# ── Public API ────────────────────────────────────────────────

def prompt_for_key_gui() -> bool:
    """
    Opens the modern onboarding window and returns True if a valid
    API key was entered and saved, False if cancelled.
    """
    try:
        win = OnboardingWindow()
        return win.show()
    except Exception as e:
        logging.error(f"Onboarding GUI failed: {e}")
        return prompt_for_key_console()


def prompt_for_key_console() -> bool:
    """
    Fallback: interactive CLI prompt for headless / daemon environments.
    """
    print("\n" + "=" * 50)
    print("  GALT SECURITY AGENT — SETUP REQUIRED")
    print("=" * 50)
    print("  No valid Google Gemini API key was detected.")
    print(f"  Get a free key at: {AISTUDIO_URL}\n")

    while True:
        try:
            key = input("  🔑 API Key (Ctrl+C to exit): ").strip()
            if not key:
                continue
            print("  Validating...", end="\r")
            if validate_key(key):
                print("  ✅ Valid — saving configuration...  ")
                save_api_key(key)
                return True
            else:
                print("  ❌ Invalid key or connection error. Try again.")
        except KeyboardInterrupt:
            print("\n  Setup cancelled.")
            return False
        except EOFError:
            return False


def prompt_for_key(force_cli: bool = False) -> bool:
    """
    Smart dispatcher: uses the GUI unless stdin is a real TTY or force_cli=True.
    """
    logging.info("Starting onboarding flow...")
    if force_cli or sys.stdin.isatty():
        return prompt_for_key_console()
    return prompt_for_key_gui()


if __name__ == "__main__":
    prompt_for_key_gui()
