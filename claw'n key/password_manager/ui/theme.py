"""
theme.py
Color tokens and theme helpers.

Themes:
  - Dark:         galaxy (deep purples and blues)
  - Light Blue:   soft sky blues — default light theme
  - Light Pink:   soft blush pastels
  - Light Purple: soft lavender
"""

import flet as ft


# ---------- Dark (galaxy) ----------

DARK = {
    "bg":         "#0f0f1e",
    "bg_elev":    "#1a1a2e",
    "surface":    "#16213e",
    "surface_2":  "#1f2a4a",
    "primary":    "#9d4edd",
    "primary_2":  "#c77dff",
    "accent":     "#7b2cbf",
    "text":       "#e7e7ef",
    "text_muted": "#9090a8",
    "border":     "#2d4f7d",
    "danger":     "#ff6b7a",
}

# ---------- Light Blue (default light) ----------

LIGHT_BLUE = {
    "bg":         "#f0f6ff",
    "bg_elev":    "#ffffff",
    "surface":    "#deeeff",
    "surface_2":  "#cce4ff",
    "primary":    "#4a90d9",
    "primary_2":  "#72aee8",
    "accent":     "#2d6db5",
    "text":       "#1a2a3d",
    "text_muted": "#5a7a9a",
    "border":     "#b0d0f0",
    "danger":     "#c05070",
}

# ---------- Light Pink ----------

LIGHT_PINK = {
    "bg":         "#fff5f8",
    "bg_elev":    "#ffffff",
    "surface":    "#ffe4ed",
    "surface_2":  "#ffd0e0",
    "primary":    "#e8789a",
    "primary_2":  "#f0a0b8",
    "accent":     "#d4607e",
    "text":       "#3d2530",
    "text_muted": "#a07080",
    "border":     "#f5c0d0",
    "danger":     "#c05070",
}

# ---------- Light Purple ----------

LIGHT_PURPLE = {
    "bg":         "#f8f0ff",
    "bg_elev":    "#ffffff",
    "surface":    "#eedeff",
    "surface_2":  "#e2ccff",
    "primary":    "#8b5cf6",
    "primary_2":  "#a78bfa",
    "accent":     "#7c3aed",
    "text":       "#2d1b4e",
    "text_muted": "#7c6a9a",
    "border":     "#d4b8f0",
    "danger":     "#c05070",
}

# Backward compat alias
LIGHT = LIGHT_BLUE


# ---------- Strength colors (tuned per theme) ----------

STRENGTH_COLORS = {
    "dark": {
        "Bad":      ("#ff6b7a", "#3d1520"),
        "Not Good": ("#ffc48a", "#3d2815"),
        "Good":     ("#9affb5", "#153d28"),
        "Great":    ("#c49aff", "#2b1e4a"),
    },
    "light_blue": {
        "Bad":      ("#c44054", "#fde4e8"),
        "Not Good": ("#b87518", "#fdf0dd"),
        "Good":     ("#2e8050", "#e1f5ea"),
        "Great":    ("#4a90d9", "#deeeff"),
    },
    "light_pink": {
        "Bad":      ("#c44054", "#fde4e8"),
        "Not Good": ("#b87518", "#fdf0dd"),
        "Good":     ("#2e8050", "#e1f5ea"),
        "Great":    ("#e8789a", "#ffe4ed"),
    },
    "light_purple": {
        "Bad":      ("#c44054", "#fde4e8"),
        "Not Good": ("#b87518", "#fdf0dd"),
        "Good":     ("#2e8050", "#e1f5ea"),
        "Great":    ("#8b5cf6", "#eedeff"),
    },
}


# ---------- Category tints ----------

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
    """Tracks current theme mode and light variant."""

    def __init__(self, mode: str = "dark", variant: str = "blue"):
        self.mode = mode        # "dark" or "light"
        self.variant = variant  # "blue", "pink", "purple" — only used when mode == "light"

    @property
    def c(self):
        if self.mode == "dark":
            return DARK
        if self.variant == "pink":
            return LIGHT_PINK
        if self.variant == "purple":
            return LIGHT_PURPLE
        return LIGHT_BLUE

    def _strength_key(self):
        if self.mode == "dark":
            return "dark"
        if self.variant == "pink":
            return "light_pink"
        if self.variant == "purple":
            return "light_purple"
        return "light_blue"

    def strength(self, label: str):
        return STRENGTH_COLORS[self._strength_key()].get(label, ("#9090a8", "#2d2d3e"))

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