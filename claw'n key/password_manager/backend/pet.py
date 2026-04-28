"""
pet.py
Virtual pet state: hunger, happiness, energy, XP, level, coins, inventory.
Persisted to a small JSON file alongside the vault database.

Points are earned by adding/updating passwords (stronger = more points).
Points can be spent to feed/play with the cat.
Coins are earned from strong passwords and level-ups.
XP drives the leveling system.
Item drops happen every 5 great passwords or when updating stale ones.
"""

import json
import os
import time
import random
import math

_PET_FILE = os.path.join(os.path.dirname(__file__), "..", "pet_save.json")
_PET_FILE = os.path.normpath(_PET_FILE)

# Stat decay rates (points lost per hour of real time)
_DECAY_PER_HOUR = {
    "hunger": 2.0,
    "happiness": 1.5,
    "energy": 1.0,
}

# Feeding costs and effects
FEED_OPTIONS = {
    "Kibble": {"cost": 2, "hunger": 15, "happiness": 3, "energy": 5},
    "Treat": {"cost": 5, "hunger": 8, "happiness": 15, "energy": 5},
    "Fancy Feast": {"cost": 10, "hunger": 25, "happiness": 25, "energy": 15},
}

# Play options: cost points, boost happiness and energy, slight hunger cost
PLAY_OPTIONS = {
    "Yarn Ball": {"cost": 3, "happiness": 15, "energy": -5, "hunger": -3},
    "Laser Pointer": {"cost": 5, "happiness": 25, "energy": -10, "hunger": -5},
    "Catnip Mouse": {"cost": 8, "happiness": 35, "energy": 10, "hunger": -2},
}

# Pet action: free, small happiness boost, cooldown tracked
PET_COOLDOWN_SECONDS = 30


# --- XP / Level curve ---

def xp_for_level(level: int) -> int:
    """XP needed to reach the given level."""
    return int(50 * (level ** 1.5))


# --- Item drop tables ---

ITEM_DROPS = {
    "common": [
        ("outfit", "Red Collar"),
        ("outfit", "Blue Bandana"),
        ("outfit", "Green Bow"),
        ("toy", "Yarn Ball"),
        ("toy", "Feather Wand"),
        ("food", "Tuna Treat"),
        ("food", "Milk Bowl"),
    ],
    "rare": [
        ("outfit", "Starry Cape"),
        ("outfit", "Crown"),
        ("outfit", "Wizard Hat"),
        ("toy", "Laser Pointer"),
        ("toy", "Catnip Mouse"),
    ],
    "legendary": [
        ("outfit", "Galaxy Cloak"),
        ("outfit", "Angel Wings"),
        ("outfit", "Top Hat & Monocle"),
    ],
}

RARITY_EMOJI = {
    "common": "\u2b50",
    "rare": "\U0001f48e",
    "legendary": "\U0001f451",
}


def roll_item_drop():
    """
    Roll for a random item.
    Returns (item_type, item_name, rarity) or None.
    Drop rates: 60% common, 25% rare, 10% legendary, 5% nothing.
    """
    roll = random.random()
    if roll < 0.05:
        return None
    elif roll < 0.65:
        rarity = "common"
    elif roll < 0.90:
        rarity = "rare"
    else:
        rarity = "legendary"
    item_type, item_name = random.choice(ITEM_DROPS[rarity])
    return (item_type, item_name, rarity)


# --- Mood thresholds ---

def get_mood(avg):
    if avg >= 75:
        return "happy"
    elif avg >= 50:
        return "neutral"
    elif avg >= 25:
        return "sad"
    else:
        return "miserable"


# Pose mapping based on mood
MOOD_POSES = {
    "happy": [
        "sitting.side.happy",
        "sitting.forward.happy",
        "laying.side.happy",
        "standing.side.happy",
    ],
    "neutral": [
        "sitting.side.neutral",
        "sitting.forward.neutral",
        "standing.side.neutral",
        "laying.side.neutral",
    ],
    "sad": [
        "sitting.side.aloof",
        "sitting.forward.sleepy",
        "laying.side.bored",
    ],
    "miserable": [
        "laying.side.annoyed",
        "sleeping.side.sploot",
    ],
}


class PetState:
    """Manages the virtual pet's stats and persistence."""

    def __init__(self):
        self.hunger = 50.0
        self.happiness = 50.0
        self.energy = 50.0
        self.points = 10
        self.coins = 0
        self.xp = 0
        self.level = 1
        self.total_points_earned = 0
        self.total_entries_added = 0
        self.last_update = time.time()
        self.last_pet_time = 0.0
        self.times_played = 0
        self.times_fed = 0
        self.times_petted = 0
        self.great_password_count = 0
        self.pet_name = "Whiskers"
        self.is_first_launch = True
        self.inventory = []
        self._load()

    def _default_data(self):
        return {
            "hunger": 50.0,
            "happiness": 50.0,
            "energy": 50.0,
            "points": 10,
            "coins": 0,
            "xp": 0,
            "level": 1,
            "total_points_earned": 0,
            "total_entries_added": 0,
            "last_update": time.time(),
            "last_pet_time": 0.0,
            "times_played": 0,
            "times_fed": 0,
            "times_petted": 0,
            "great_password_count": 0,
            "pet_name": "Whiskers",
            "is_first_launch": True,
            "inventory": [],
        }

    def _load(self):
        try:
            if os.path.exists(_PET_FILE):
                with open(_PET_FILE, "r") as f:
                    data = json.load(f)
                self.hunger = data.get("hunger", 50.0)
                self.happiness = data.get("happiness", 50.0)
                self.energy = data.get("energy", 50.0)
                self.points = data.get("points", 10)
                self.coins = data.get("coins", 0)
                self.xp = data.get("xp", 0)
                self.level = data.get("level", 1)
                self.total_points_earned = data.get("total_points_earned", 0)
                self.total_entries_added = data.get("total_entries_added", 0)
                self.last_update = data.get("last_update", time.time())
                self.last_pet_time = data.get("last_pet_time", 0.0)
                self.times_played = data.get("times_played", 0)
                self.times_fed = data.get("times_fed", 0)
                self.times_petted = data.get("times_petted", 0)
                self.great_password_count = data.get("great_password_count", 0)
                self.pet_name = data.get("pet_name", "Whiskers")
                self.is_first_launch = data.get("is_first_launch", True)
                self.inventory = data.get("inventory", [])
            else:
                self.is_first_launch = True
        except Exception as e:
            print(f"[Pet] Load failed: {e}")
            self.is_first_launch = True

    def save(self):
        try:
            data = {
                "hunger": round(self.hunger, 2),
                "happiness": round(self.happiness, 2),
                "energy": round(self.energy, 2),
                "points": self.points,
                "coins": self.coins,
                "xp": self.xp,
                "level": self.level,
                "total_points_earned": self.total_points_earned,
                "total_entries_added": self.total_entries_added,
                "last_update": self.last_update,
                "last_pet_time": self.last_pet_time,
                "times_played": self.times_played,
                "times_fed": self.times_fed,
                "times_petted": self.times_petted,
                "great_password_count": self.great_password_count,
                "pet_name": self.pet_name,
                "is_first_launch": self.is_first_launch,
                "inventory": self.inventory,
            }
            with open(_PET_FILE, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"[Pet] Save failed: {e}")

    def reset(self):
        """Reset pet to defaults (keeps is_first_launch=False)."""
        defaults = self._default_data()
        defaults["is_first_launch"] = False
        defaults["pet_name"] = self.pet_name  # keep name
        for k, v in defaults.items():
            setattr(self, k, v)
        self.save()

    def apply_decay(self):
        """Apply time-based stat decay since last update."""
        now = time.time()
        elapsed_hours = (now - self.last_update) / 3600.0
        if elapsed_hours < 0:
            elapsed_hours = 0

        for stat in ("hunger", "happiness", "energy"):
            current = getattr(self, stat)
            decay = _DECAY_PER_HOUR[stat] * elapsed_hours
            setattr(self, stat, max(0.0, current - decay))

        self.last_update = now
        self.save()

    def apply_stale_penalty(self, stale_count):
        """Lower happiness based on number of stale passwords."""
        if stale_count <= 0:
            return
        penalty = min(stale_count * 3, 20)
        self.happiness = max(0.0, self.happiness - penalty)
        self.save()

    # --- XP and Leveling ---

    def _check_level_up(self):
        """Check and apply level ups. Returns list of level-up events."""
        events = []
        while self.xp >= xp_for_level(self.level + 1):
            self.xp -= xp_for_level(self.level + 1)
            self.level += 1
            # Level up bonus
            bonus_coins = 10 + (self.level * 2)
            self.coins += bonus_coins
            self.happiness = min(100.0, self.happiness + 10)
            events.append({
                "new_level": self.level,
                "bonus_coins": bonus_coins,
            })
        return events

    def add_xp(self, amount):
        """Add XP and check for level ups. Returns level-up events."""
        self.xp += amount
        events = self._check_level_up()
        self.save()
        return events

    # --- Password rewards ---

    def award_points(self, points, strength_tier=0, reason=""):
        """
        Award points from password actions.
        strength_tier: 0=Bad, 1=Not Good, 2=Good, 3=Great
        Returns reward dict with coins, xp, level_ups, item_drop info.
        """
        if points <= 0:
            return {"coins_earned": 0, "xp_earned": 0, "level_ups": [], "item_drop": None}

        self.points += points
        self.total_points_earned += points
        self.total_entries_added += 1

        # Coins based on strength
        coins_earned = {0: 0, 1: 1, 2: 3, 3: 5}.get(strength_tier, 0)
        self.coins += coins_earned

        # XP based on points
        xp_earned = points * 2
        level_ups = self.add_xp(xp_earned)

        # Happiness based on strength
        happiness_delta = {0: -8, 1: -2, 2: 5, 3: 12}.get(strength_tier, 0)
        self.happiness = max(0.0, min(100.0, self.happiness + happiness_delta))

        # Track great passwords for item drops
        item_drop = None
        if strength_tier == 3:
            self.great_password_count += 1
            # Item drop every 5 great passwords
            if self.great_password_count % 5 == 0:
                item_drop = roll_item_drop()
                if item_drop:
                    self._add_to_inventory(item_drop)

        self.save()
        print(f"[Pet] +{points} pts, +{coins_earned} coins, +{xp_earned} XP ({reason})")

        return {
            "coins_earned": coins_earned,
            "xp_earned": xp_earned,
            "level_ups": level_ups,
            "item_drop": item_drop,
        }

    def award_stale_update_bonus(self):
        """Bonus rewards for updating a stale password."""
        bonus_coins = 5
        bonus_xp = 10
        self.coins += bonus_coins
        level_ups = self.add_xp(bonus_xp)
        self.happiness = min(100.0, self.happiness + 10)

        # Chance for item drop on stale update
        item_drop = roll_item_drop()
        if item_drop:
            self._add_to_inventory(item_drop)

        self.save()
        return {
            "bonus_coins": bonus_coins,
            "bonus_xp": bonus_xp,
            "level_ups": level_ups,
            "item_drop": item_drop,
        }

    def _add_to_inventory(self, item_tuple):
        """Add an item to the inventory."""
        item_type, item_name, rarity = item_tuple
        self.inventory.append({
            "type": item_type,
            "name": item_name,
            "rarity": rarity,
            "acquired_at": time.time(),
        })

    # --- Actions ---

    def feed(self, option_name):
        """Feed the cat. Returns (success, message)."""
        if option_name not in FEED_OPTIONS:
            return False, "Unknown food."
        opt = FEED_OPTIONS[option_name]
        if self.points < opt["cost"]:
            return False, f"Need {opt['cost']} points (you have {self.points})."
        self.points -= opt["cost"]
        self.hunger = min(100.0, self.hunger + opt["hunger"])
        self.happiness = min(100.0, self.happiness + opt["happiness"])
        self.energy = min(100.0, self.energy + opt["energy"])
        self.times_fed += 1
        self.save()
        return True, f"Fed {self.pet_name} {option_name}!"

    def play(self, option_name):
        """Play with the cat. Returns (success, message)."""
        if option_name not in PLAY_OPTIONS:
            return False, "Unknown toy."
        opt = PLAY_OPTIONS[option_name]
        if self.points < opt["cost"]:
            return False, f"Need {opt['cost']} points (you have {self.points})."
        if self.energy <= 5:
            return False, f"{self.pet_name} is too tired to play!"
        self.points -= opt["cost"]
        self.happiness = max(0.0, min(100.0, self.happiness + opt["happiness"]))
        self.energy = max(0.0, min(100.0, self.energy + opt["energy"]))
        self.hunger = max(0.0, min(100.0, self.hunger + opt["hunger"]))
        self.times_played += 1
        self.save()
        return True, f"Played with {self.pet_name} using {option_name}!"

    def pet_cat(self):
        """Pet the cat (free action with cooldown). Returns (success, message)."""
        now = time.time()
        elapsed = now - self.last_pet_time
        if elapsed < PET_COOLDOWN_SECONDS:
            remaining = int(PET_COOLDOWN_SECONDS - elapsed)
            return False, f"Wait {remaining}s to pet again~"
        self.last_pet_time = now
        self.happiness = min(100.0, self.happiness + 5)
        self.times_petted += 1
        self.save()
        return True, f"You petted {self.pet_name}!"

    # --- XP progress ---

    @property
    def xp_progress(self):
        """Returns (current_xp, xp_needed) for current level."""
        needed = xp_for_level(self.level + 1)
        return (self.xp, needed)

    @property
    def xp_percent(self):
        """Returns 0.0-1.0 progress to next level."""
        current, needed = self.xp_progress
        if needed <= 0:
            return 1.0
        return min(1.0, current / needed)

    # --- Inventory ---

    @property
    def inventory_count(self):
        return len(self.inventory)

    def get_inventory_by_rarity(self):
        """Returns inventory grouped by rarity."""
        result = {"common": [], "rare": [], "legendary": []}
        for item in self.inventory:
            rarity = item.get("rarity", "common")
            if rarity in result:
                result[rarity].append(item)
        return result

    # --- Mood ---

    @property
    def avg_stat(self):
        return (self.hunger + self.happiness + self.energy) / 3.0

    @property
    def mood(self):
        return get_mood(self.avg_stat)

    @property
    def mood_poses(self):
        return MOOD_POSES.get(self.mood, MOOD_POSES["neutral"])