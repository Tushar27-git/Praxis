"""Validated, offline entry sketches. No combat simulation or game control."""
import math
import time


MODES = {"friendly", "regular", "ranked", "war"}
ROLES = {"main", "funnel", "cleanup", "hero", "spell"}
DOMAINS = {"air", "ground", "both"}
# shortcut: illustrative relative exposure weights, not game DPS/range stats.
# Replace only after collecting real annotated outcomes and a validated model.
THREATS = {
    "town_hall": (3, 3), "air_defense": (4, 0), "air_sweeper": (2, 0),
    "cannon": (0, 2), "archer_tower": (2, 2), "wizard_tower": (2, 2),
    "inferno": (4, 4), "eagle": (4, 4), "scattershot": (4, 4),
    "xbow": (3, 3), "mortar": (0, 2), "bomb_tower": (0, 2),
    "clan_castle": (0, 0), "wall": (0, 0), "other": (1, 1),
}


def _number(value, label, low, high, integer=False):
    if type(value) not in (int, float) or (type(value) is float and not math.isfinite(value)):
        raise ValueError(f"{label} must be a finite number.")
    if integer and type(value) is not int:
        raise ValueError(f"{label} must be a whole number.")
    if not low <= value <= high:
        raise ValueError(f"{label} must be between {low} and {high}.")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip() or len(value) > 80:
        raise ValueError(f"{label} must contain 1-80 characters.")
    return value.strip()


def _validate(data):
    if not isinstance(data, dict):
        raise ValueError("Session must be a JSON object.")
    if type(data.get("schema_version")) is not int or data["schema_version"] != 1:
        raise ValueError("Unsupported session version. Use version 1.")
    if data.get("mode") not in MODES:
        raise ValueError("Choose Friendly, Regular, Ranked or War.")
    _number(data.get("town_hall"), "Town Hall", 1, 30, integer=True)
    for field in ("army_confirmed", "scene_confirmed"):
        if type(data.get(field)) is not bool:
            raise ValueError(f"{field} must be true or false.")
    center = data.get("center")
    if center is not None:
        if not isinstance(center, dict):
            raise ValueError("Base center must be a point.")
        for axis in ("x", "y"):
            _number(center.get(axis), f"Center {axis}", 0, 1)
    for field, limit in (("army", 60), ("annotations", 250)):
        items = data.get(field)
        if not isinstance(items, list) or len(items) > limit:
            raise ValueError(f"{field} must be a list of at most {limit} entries.")
        seen = set()
        for item in items:
            if not isinstance(item, dict):
                raise ValueError(f"Each {field} entry must be an object.")
            ident = _text(item.get("id"), "Entry ID")
            if ident in seen:
                raise ValueError(f"Duplicate {field} ID: {ident}.")
            seen.add(ident)
            if field == "army":
                _text(item.get("name"), "Unit name")
                _number(item.get("count"), "Quantity", 1, 1000, integer=True)
                _number(item.get("level"), "Unit level", 1, 200, integer=True)
                if item.get("role") not in ROLES or item.get("domain") not in DOMAINS:
                    raise ValueError("Choose a valid unit role and target domain.")
                if item["role"] == "hero" and item["count"] != 1:
                    raise ValueError("Each hero entry must have quantity 1.")
            else:
                if item.get("kind") not in THREATS and item.get("kind") != "deployment":
                    raise ValueError("Unknown building or area type.")
                for axis in ("x", "y"):
                    _number(item.get(axis), f"Region {axis}", 0, 1)
                for axis in ("w", "h"):
                    _number(item.get(axis), f"Region {axis}", .001, 1)
                if item["x"] + item["w"] > 1 + 1e-9 or item["y"] + item["h"] > 1 + 1e-9:
                    raise ValueError("Regions must fit entirely inside the screenshot.")


def _positions(zone, count, spots):
    spots = min(count, spots)
    horizontal = zone["w"] >= zone["h"]
    result = []
    for index in range(spots):
        fraction = .5 if spots == 1 else .2 + .6 * index / (spots - 1)
        result.append({
            "x": zone["x"] + zone["w"] * (fraction if horizontal else .5),
            "y": zone["y"] + zone["h"] * (.5 if horizontal else fraction),
            "count": count // spots + (1 if index < count % spots else 0),
        })
    return result


def analyze(data):
    started = time.perf_counter()
    _validate(data)
    issues = []
    if not data["army_confirmed"]:
        issues.append("Confirm the selected army and its current quantities.")
    if not data["scene_confirmed"]:
        issues.append("Confirm this is a scouting screenshot.")
    if data.get("center") is None:
        issues.append("Place the base center on the screenshot.")
    if not any(u["role"] == "main" for u in data["army"]):
        issues.append("Add at least one main-force troop entry.")
    halls = [a for a in data["annotations"] if a["kind"] == "town_hall"]
    zones = [a for a in data["annotations"] if a["kind"] == "deployment"]
    if len(halls) != 1:
        issues.append("Mark exactly one Town Hall.")
    if not zones:
        issues.append("Mark at least one area you have confirmed allows deployment.")
    unknowns = [
        "Manual annotations; automatic building detection is not connected.",
        "Entry cost is an illustrative geometry heuristic, not an outcome probability.",
        "Building levels, walls, troop pathing, damage and hidden defenses are not simulated.",
        "Spells, cleanup and hero abilities remain manual decisions.",
        "Scouting time and target replacement are not verified for this mode.",
    ]
    candidates = []
    if not issues:
        troops = [u for u in data["army"] if u["role"] in {"main", "funnel"}]
        total = sum(u["count"] for u in troops)
        air = sum(u["count"] * (1 if u["domain"] == "air" else .5 if u["domain"] == "both" else 0) for u in troops) / total
        town = halls[0]
        target = (town["x"] + town["w"] / 2, town["y"] + town["h"] / 2)
        for zone in zones:
            x, y = zone["x"] + zone["w"] / 2, zone["y"] + zone["h"] / 2
            cost = math.hypot(x - target[0], y - target[1]) * .4
            for obj in data["annotations"]:
                if obj["kind"] == "deployment":
                    continue
                wa, wg = THREATS[obj["kind"]]
                distance = math.hypot(x - obj["x"] - obj["w"] / 2, y - obj["y"] - obj["h"] / 2)
                cost += (wa * air + wg * (1 - air)) / (distance + .1) ** 2
            angle = math.degrees(math.atan2(x - data["center"]["x"], data["center"]["y"] - y)) % 360
            hour = int(math.floor(angle / 30 + .5)) % 12 or 12
            steps, reserves = [], []
            for role in ("funnel", "main", "hero", "spell", "cleanup"):
                for unit in (u for u in data["army"] if u["role"] == role):
                    item = {"unit_id": unit["id"], "name": unit["name"], "count": unit["count"], "role": role}
                    if role in {"spell", "cleanup"}:
                        reserves.append(item)
                    else:
                        trigger = {"funnel": "Review funnel placement manually first.", "main": "After confirming the funnel manually.", "hero": "After confirming the main-force deployment manually."}[role]
                        steps.append({**item, "positions": _positions(zone, unit["count"], 2 if role == "funnel" else 3 if role == "main" else 1), "trigger": trigger})
            candidates.append({"zone_id": zone["id"], "clock": f"{hour} o'clock", "entry": {"x": x, "y": y}, "cost": round(cost, 3), "steps": steps, "reserves": reserves})
        candidates.sort(key=lambda p: (p["cost"], p["zone_id"]))
    return {"status": "needs_input" if issues else "preview", "issues": issues, "candidates": candidates, "unknowns": unknowns, "success_probability": None, "planning_ms": round((time.perf_counter() - started) * 1000, 3)}
