"""
pet_panel.py
Side panel showing pet stats, mood, interaction options,
XP/level progress, points, and inventory.
"""

import flet as ft
from .theme import ThemeManager
from .widgets import show_snack
from backend.pet import (
    PetState, FEED_OPTIONS, PLAY_OPTIONS,
    xp_for_level, RARITY_EMOJI,
)


def build_pet_panel(page, pet: PetState, cat_widget, theme: ThemeManager):
    """Build the pet panel with stats, cat animation, and interaction buttons.

    Returns a ft.Container that can be placed in the vault layout.
    Also returns refresh_panel callback.
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

    # --- XP / Level bar ---

    def xp_bar():
        current_xp, needed_xp = pet.xp_progress
        return ft.Column(
            [
                ft.Row(
                    [
                        ft.Text(f"\U0001f3c6 Level {pet.level}", size=13,
                                weight=ft.FontWeight.BOLD,
                                color=theme.c["primary"]),
                        ft.Text(f"{current_xp}/{needed_xp} XP", size=11,
                                color=theme.c["text_muted"]),
                    ],
                    alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                ),
                ft.ProgressBar(
                    value=pet.xp_percent,
                    color=theme.c["primary"],
                    bgcolor=theme.c["surface_2"],
                    bar_height=6,
                    border_radius=3,
                ),
            ],
            spacing=2,
        )

    xp_container = xp_bar()

    # --- Points display ---

    def points_display():
        return ft.Row(
            [
                ft.Container(
                    content=ft.Row(
                        [
                            ft.Icon(ft.Icons.STAR_ROUNDED, color="#e5c14a", size=16),
                            ft.Text(f"{pet.points}", size=13,
                                    weight=ft.FontWeight.W_600,
                                    color=theme.c["text"]),
                        ],
                        spacing=4,
                    ),
                    bgcolor=theme.c["surface_2"],
                    border_radius=8,
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    tooltip="Points (spend on feed/play)",
                ),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )

    points_row = points_display()

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

    # --- Pet name ---

    name_text = ft.Text(
        pet.pet_name,
        size=18,
        weight=ft.FontWeight.BOLD,
        color=theme.c["text"],
        text_align=ft.TextAlign.CENTER,
    )

    name_row = ft.Container(
        content=ft.Row(
            [
                name_text,
            ],
            spacing=4,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
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

    # --- Inventory button ---

    def on_inventory_click(_):
        _show_inventory_dialog()

    def _show_inventory_dialog():
        from .widgets import open_dialog, close_dialog

        grouped = pet.get_inventory_by_rarity()

        def _item_row(item):
            emoji = RARITY_EMOJI.get(item["rarity"], "\u2b50")
            rarity_colors = {
                "common": theme.c["text_muted"],
                "rare": "#4ea5dd",
                "legendary": "#e5c14a",
            }
            return ft.Container(
                content=ft.Row(
                    [
                        ft.Text(emoji, size=14),
                        ft.Text(item["name"], size=12,
                                color=theme.c["text"],
                                weight=ft.FontWeight.W_600),
                        ft.Text(f"({item['type']})", size=10,
                                color=theme.c["text_muted"]),
                        ft.Container(expand=True),
                        ft.Text(item["rarity"].title(), size=10,
                                color=rarity_colors.get(item["rarity"],
                                                         theme.c["text_muted"]),
                                weight=ft.FontWeight.W_600),
                    ],
                    vertical_alignment=ft.CrossAxisAlignment.CENTER,
                ),
                bgcolor=theme.c["surface_2"],
                border=ft.border.all(1, theme.c["border"]),
                border_radius=6,
                padding=ft.padding.symmetric(horizontal=10, vertical=6),
            )

        items_list = ft.Column(spacing=4, scroll=ft.ScrollMode.AUTO, height=300)

        if not pet.inventory:
            items_list.controls.append(
                ft.Container(
                    content=ft.Column(
                        [
                            ft.Text("\U0001f4e6", size=32,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("No items yet!", size=14,
                                    color=theme.c["text_muted"],
                                    text_align=ft.TextAlign.CENTER),
                            ft.Text("Add 'Great' passwords to earn item drops!",
                                    size=12, color=theme.c["text_muted"],
                                    text_align=ft.TextAlign.CENTER),
                        ],
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=6,
                    ),
                    padding=30,
                )
            )
        else:
            # Show by rarity: legendary first
            for rarity in ["legendary", "rare", "common"]:
                items = grouped.get(rarity, [])
                if items:
                    items_list.controls.append(
                        ft.Text(
                            f"{RARITY_EMOJI.get(rarity, '')} {rarity.title()} ({len(items)})",
                            size=12, weight=ft.FontWeight.W_600,
                            color=theme.c["text_muted"],
                        )
                    )
                    for item in items:
                        items_list.controls.append(_item_row(item))

        # Summary
        summary = ft.Row(
            [
                ft.Text(f"\U0001f4e6 {pet.inventory_count} items", size=12,
                        color=theme.c["text_muted"]),
                ft.Container(expand=True),
                ft.Text(
                    f"\u2b50{len(grouped.get('common', []))} "
                    f"\U0001f48e{len(grouped.get('rare', []))} "
                    f"\U0001f451{len(grouped.get('legendary', []))}",
                    size=11, color=theme.c["text_muted"],
                ),
            ],
        )

        inv_dlg = ft.AlertDialog(
            modal=True,
            bgcolor=theme.c["surface"],
            title=ft.Row(
                [
                    ft.Text("\U0001f392", size=20),
                    ft.Text(f"{pet.pet_name}'s Inventory", color=theme.c["text"]),
                ],
                spacing=8,
            ),
            content=ft.Container(
                width=400,
                content=ft.Column(
                    [summary, ft.Divider(color=theme.c["border"], height=1), items_list],
                    spacing=8,
                    tight=True,
                ),
            ),
            actions=[
                ft.TextButton(
                    "Close",
                    on_click=lambda _: close_dialog(page, inv_dlg),
                ),
            ],
        )
        open_dialog(page, inv_dlg)

    inventory_btn = ft.Container(
        content=ft.Row(
            [
                ft.Text("\U0001f392", size=14),
                ft.Text(f"Inventory ({pet.inventory_count})", size=12,
                        color=theme.c["text"],
                        weight=ft.FontWeight.W_600),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        ),
        bgcolor=theme.c["surface_2"],
        border=ft.border.all(1, theme.c["border"]),
        border_radius=8,
        padding=ft.padding.symmetric(horizontal=12, vertical=6),
        on_click=on_inventory_click,
        ink=True,
    )

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
            xp_container,
            points_row,
            ft.Divider(color=theme.c["border"], height=1),
            stats_column,
            ft.Divider(color=theme.c["border"], height=1),
            pet_button,
            ft.Divider(color=theme.c["border"], height=1),
            section_header(ft.Icons.RESTAURANT, "Feed"),
            feed_row,
            ft.Divider(color=theme.c["border"], height=1),
            section_header(ft.Icons.SPORTS_ESPORTS, "Play"),
            play_row,
            ft.Divider(color=theme.c["border"], height=1),
            inventory_btn,
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

        # Update XP bar
        xp_container.controls = xp_bar().controls

        # Update points
        points_row.controls = points_display().controls

        # Update mood
        mood_text.value = f"{mood_emoji.get(pet.mood, chr(0x1f431))} {pet.mood.title()}"

        # Update name
        name_text.value = pet.pet_name

        # Update feed buttons
        feed_row.controls = [make_feed_button(name) for name in FEED_OPTIONS]

        # Update play buttons
        play_row.controls = [make_play_button(name) for name in PLAY_OPTIONS]

        # Update inventory button
        inventory_btn.content = ft.Row(
            [
                ft.Text("\U0001f392", size=14),
                ft.Text(f"Inventory ({pet.inventory_count})", size=12,
                        color=theme.c["text"],
                        weight=ft.FontWeight.W_600),
            ],
            spacing=6,
            alignment=ft.MainAxisAlignment.CENTER,
        )

        page.update()

    # Initial mood sync
    pet.apply_decay()
    cat_widget.set_mood_poses(pet.mood_poses)

    return panel, refresh_panel