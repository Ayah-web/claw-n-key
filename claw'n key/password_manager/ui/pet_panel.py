"""
pet_panel.py
Side panel showing pet stats, mood, and interaction options.
Integrates with the cat widget and pet state.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import show_snack
from backend.pet import PetState, FEED_OPTIONS, PLAY_OPTIONS


def build_pet_panel(page, pet: PetState, cat_widget, theme: ThemeManager):
    """Build the pet panel with stats, cat animation, and interaction buttons.

    Returns a ft.Container that can be placed in the vault layout.
    """

    # --- Stat bars ---

    def stat_bar(label, value, color, icon_name):
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Row(
                            [
                                ft.Icon(icon_name, color=color, size=14),
                                ft.Text(label, size=12, color=theme.c["text_muted"]),
                            ],
                            spacing=4,
                        ),
                        ft.Text(f"{int(value)}%", size=12,
                                weight=ft.FontWeight.W_600, color=theme.c["text"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ProgressBar(
                    value=max(0, min(1, value / 100.0)),
                    color=color,
                    bgcolor=theme.c["surface_2"],
                    bar_height=8,
                    border_radius=4,
                ),
            ],
            spacing=2,
        )

    hunger_bar = stat_bar("Hunger", pet.hunger, "#68c58f", ft.Icons.RESTAURANT)
    happiness_bar = stat_bar("Happiness", pet.happiness, "#f07ba6", ft.Icons.FAVORITE)
    energy_bar = stat_bar("Energy", pet.energy, "#4ea5dd", ft.Icons.BOLT)

    stats_column = ft.Column(
        [hunger_bar, happiness_bar, energy_bar],
        spacing=8,
    )

    # --- Points display ---

    points_display = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.STAR_ROUNDED, color="#e5c14a", size=18),
                ft.Text(
                    f"{pet.points} points",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=theme.c["text"],
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=theme.c["surface_2"],
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
    )

    # --- Mood display ---

    mood_emoji = {
        "happy": "\U0001f63a",
        "neutral": "\U0001f431",
        "sad": "\U0001f63f",
        "miserable": "\U0001f640",
    }

    mood_text = ft.Text(
        f"{mood_emoji.get(pet.mood, chr(0x1f431))} {pet.mood.title()}",
        size=13,
        color=theme.c["text_muted"],
        text_align=ft.TextAlign.CENTER,
    )

    # --- Pet name (editable) ---

    name_text = ft.Text(
        pet.pet_name,
        size=18,
        weight=ft.FontWeight.BOLD,
        color=theme.c["text"],
        text_align=ft.TextAlign.CENTER,
    )

    def on_name_click(_):
        name_field = ft.TextField(
            value=pet.pet_name,
            text_size=14,
            border_radius=8,
            bgcolor=theme.c["surface_2"],
            border_color=theme.c["border"],
            focused_border_color=theme.c["primary"],
            content_padding=ft.padding.symmetric(horizontal=10, vertical=6),
        )

        def save_name(_):
            new_name = name_field.value.strip()
            if new_name:
                pet.pet_name = new_name
                pet.save()
                name_text.value = new_name
                cat_widget.say(f"I'm {new_name} now!", 3.0)
            dialog.open = False
            page.update()

        dialog = ft.AlertDialog(
            title=ft.Text("Rename your cat", size=16),
            content=name_field,
            actions=[
                ft.TextButton("Cancel",
                              on_click=lambda _: setattr(dialog, 'open', False) or page.update()),
                ft.FilledButton("Save", on_click=save_name),
            ],
        )
        page.overlay.append(dialog)
        dialog.open = True
        page.update()

    name_row = ft.Container(
        content=ft.Row(
            [
                name_text,
                ft.Icon(ft.Icons.EDIT, size=14, color=theme.c["text_muted"]),
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        on_click=on_name_click,
        tooltip="Click to rename",
    )

    # --- Pet button (free action) ---

    def on_pet_click(_):
        ok, msg = pet.pet_cat()
        if ok:
            show_snack(page, f"\U0001f43e {msg}")
            cat_widget.trigger_pet()
        else:
            show_snack(page, f"\u23f3 {msg}", error=False)
        refresh_panel()

    pet_button = ft.Container(
        content=ft.Row(
            [
                ft.Icon(ft.Icons.PETS, color=theme.c["primary"], size=20),
                ft.Text("Pet", size=13, weight=ft.FontWeight.W_600,
                        color=theme.c["primary"]),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=10,
        padding=ft.padding.symmetric(horizontal=16, vertical=8),
        on_click=on_pet_click,
        tooltip="Free! Pet your cat (30s cooldown)",
        ink=True,
    )

    # --- Feed buttons ---

    def make_feed_button(food_name):
        opt = FEED_OPTIONS[food_name]
        cost = opt["cost"]

        def on_feed(_):
            ok, msg = pet.feed(food_name)
            if ok:
                show_snack(page, f"\U0001f431 {msg}")
                cat_widget.trigger_happy()
            else:
                show_snack(page, f"\u274c {msg}", error=True)
            refresh_panel()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(food_name, size=11, weight=ft.FontWeight.W_600,
                            color=theme.c["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{cost}\u2605", size=10,
                            color=theme.c["text_muted"], text_align=ft.TextAlign.CENTER),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface_2"],
            border=ft.border.all(1, theme.c["border"]),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            on_click=on_feed,
            tooltip=f"+{opt['hunger']} hunger, +{opt['happiness']} happy, +{opt['energy']} energy",
            ink=True,
            expand=True,
        )

    feed_row = ft.Row(
        [make_feed_button(name) for name in FEED_OPTIONS],
        spacing=4,
    )

    # --- Play buttons ---

    def make_play_button(toy_name):
        opt = PLAY_OPTIONS[toy_name]
        cost = opt["cost"]

        def on_play(_):
            ok, msg = pet.play(toy_name)
            if ok:
                show_snack(page, f"\U0001f3be {msg}")
                cat_widget.trigger_play()
            else:
                show_snack(page, f"\u274c {msg}", error=True)
            refresh_panel()

        return ft.Container(
            content=ft.Column(
                [
                    ft.Text(toy_name, size=11, weight=ft.FontWeight.W_600,
                            color=theme.c["text"], text_align=ft.TextAlign.CENTER),
                    ft.Text(f"{cost}\u2605", size=10,
                            color=theme.c["text_muted"], text_align=ft.TextAlign.CENTER),
                ],
                spacing=2,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface_2"],
            border=ft.border.all(1, theme.c["border"]),
            border_radius=8,
            padding=ft.padding.symmetric(horizontal=8, vertical=6),
            on_click=on_play,
            tooltip=f"+{opt['happiness']} happy, {opt['energy']} energy, {opt['hunger']} hunger",
            ink=True,
            expand=True,
        )

    play_row = ft.Row(
        [make_play_button(name) for name in PLAY_OPTIONS],
        spacing=4,
    )

    # --- Lifetime stats ---

    def lifetime_stats():
        return ft.Container(
            content=ft.Column(
                [
                    ft.Text("Lifetime Stats", size=11, weight=ft.FontWeight.W_600,
                            color=theme.c["text_muted"]),
                    ft.Row([
                        ft.Text(f"\U0001f4dd {pet.total_entries_added} entries", size=10,
                                color=theme.c["text_muted"]),
                        ft.Text(f"\u2b50 {pet.total_points_earned} pts", size=10,
                                color=theme.c["text_muted"]),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        ft.Text(f"\U0001f372 {pet.times_fed}x fed", size=10,
                                color=theme.c["text_muted"]),
                        ft.Text(f"\U0001f3be {pet.times_played}x played", size=10,
                                color=theme.c["text_muted"]),
                    ], spacing=8, alignment=ft.MainAxisAlignment.CENTER),
                    ft.Row([
                        ft.Text(f"\U0001f43e {pet.times_petted}x petted", size=10,
                                color=theme.c["text_muted"]),
                    ], alignment=ft.MainAxisAlignment.CENTER),
                ],
                spacing=4,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            ),
            bgcolor=theme.c["surface_2"],
            border_radius=8,
            padding=8,
        )

    lifetime_container = lifetime_stats()

    # --- Section headers ---

    def section_header(icon, label):
        return ft.Row(
            [
                ft.Icon(icon, size=14, color=theme.c["text_muted"]),
                ft.Text(label, size=12, weight=ft.FontWeight.W_600,
                        color=theme.c["text_muted"]),
            ],
            spacing=4,
        )

    # --- Assemble panel ---

    panel_content = ft.Column(
        [
            name_row,
            cat_widget.container,
            mood_text,
            ft.Divider(color=theme.c["border"], height=1),
            stats_column,
            ft.Divider(color=theme.c["border"], height=1),
            points_display,
            pet_button,
            ft.Divider(color=theme.c["border"], height=1),
            section_header(ft.Icons.RESTAURANT, "Feed"),
            feed_row,
            ft.Divider(color=theme.c["border"], height=1),
            section_header(ft.Icons.SPORTS_ESPORTS, "Play"),
            play_row,
            ft.Divider(color=theme.c["border"], height=1),
            lifetime_container,
        ],
        spacing=8,
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
    )

    panel = ft.Container(
        content=panel_content,
        bgcolor=theme.c["surface"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=12,
        padding=14,
        width=280,
    )

    def refresh_panel():
        """Update all stats displays."""
        pet.apply_decay()
        cat_widget.set_mood_poses(pet.mood_poses)

        # Update stat bars
        stats_column.controls = [
            stat_bar("Hunger", pet.hunger, "#68c58f", ft.Icons.RESTAURANT),
            stat_bar("Happiness", pet.happiness, "#f07ba6", ft.Icons.FAVORITE),
            stat_bar("Energy", pet.energy, "#4ea5dd", ft.Icons.BOLT),
        ]

        # Update points
        points_display.content = ft.Row(
            [
                ft.Icon(ft.Icons.STAR_ROUNDED, color="#e5c14a", size=18),
                ft.Text(
                    f"{pet.points} points",
                    size=14,
                    weight=ft.FontWeight.W_600,
                    color=theme.c["text"],
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        # Update mood
        mood_text.value = f"{mood_emoji.get(pet.mood, chr(0x1f431))} {pet.mood.title()}"

        # Update name
        name_text.value = pet.pet_name

        # Update feed buttons
        feed_row.controls = [make_feed_button(name) for name in FEED_OPTIONS]

        # Update play buttons
        play_row.controls = [make_play_button(name) for name in PLAY_OPTIONS]

        # Update lifetime stats
        lifetime_container.content = lifetime_stats().content

        page.update()

    # Initial mood sync
    pet.apply_decay()
    cat_widget.set_mood_poses(pet.mood_poses)

    return panel, refresh_panel