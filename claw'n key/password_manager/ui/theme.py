"""
theme.py
Color tokens and theme helpers.

Two themes as per the brief:
  - Dark:  galaxy-ish (deep purples and blues)
  - Light: soft pastels (lavender, cream)

All components import from here so swapping themes is cheap.
"""

import flet as ft


# ---------- Dark (galaxy) ----------

DARK = {
    "bg":          "#0f0f1e",  # deep space
    "bg_elev":    "#1a1a2e",  # lifted surface
    "surface":    "#16213e",  # cards
    "surface_2":  "#1f2a4a",  # inputs
    "primary":    "#9d4edd",  # galactic purple
    "primary_2":  "#c77dff",  # highlight
    "accent":     "#7b2cbf",
    "text":       "#e7e7ef",
    "text_muted": "#9090a8",
    "border":     "#2d4f7d",
    "danger":     "#ff6b7a",
}

# ---------- Light (pastel) ----------

LIGHT = {
    "bg":          "#faf7ff",  # soft lavender white
    "bg_elev":    "#ffffff",
    "surface":    "#f3edfe",  # light lavender
    "surface_2":  "#ede4fc",
    "primary":    "#9d7ed1",  # muted pastel purple
    "primary_2":  "#b89fe0",
    "accent":     "#8566b8",
    "text":       "#2d2a3e",
    "text_muted": "#7b7890",
    "border":     "#e4dcf5",
    "danger":     "#d87282",
}


# ---------- Strength colors (tuned per mode) ----------

STRENGTH_COLORS = {
    "dark": {
        "Bad":      ("#ff6b7a", "#3d1520"),  # (fg, bg)
        "Not Good": ("#ffc48a", "#3d2815"),
        "Good":     ("#9affb5", "#153d28"),
        "Great":    ("#c49aff", "#2b1e4a"),
    },
    "light": {
        "Bad":      ("#c44054", "#fde4e8"),
        "Not Good": ("#b87518", "#fdf0dd"),
        "Good":     ("#2e8050", "#e1f5ea"),
        "Great":    ("#6a3fb5", "#ede0fc"),
    },
}

# ---------- Category tints (pure cosmetic, subtle) ----------

CATEGORY_COLORS = {
    "Personal":  "#9d4edd",
    "Work":      "#4ea5dd",
    "Finance":   "#68c58f",
    "Social":    "#f07ba6",
    "Streaming": "#ed8b4e",
    "Shopping":  "#e5c14a",
    "Other":     "#9090a8",
}


class ThemeManager:
    """Tracks current theme and exposes the active color map."""

    def __init__(self, mode: str = "dark"):
        self.mode = mode  # "dark" or "light"

    @property
    def c(self):
        return DARK if self.mode == "dark" else LIGHT

    def strength(self, label: str):
        return STRENGTH_COLORS[self.mode].get(label, ("#9090a8", "#2d2d3e"))

    def apply(self, page: ft.Page):
        page.bgcolor = self.c["bg"]
        page.theme_mode = (
            ft.ThemeMode.DARK if self.mode == "dark" else ft.ThemeMode.LIGHT
        )
        page.theme = ft.Theme(
            color_scheme_seed=self.c["primary"],
            use_material3=True,
        )

    def toggle(self):
        self.mode = "light" if self.mode == "dark" else "dark"
