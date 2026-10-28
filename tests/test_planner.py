import copy
import math
import unittest

from coc_advisor.planner import analyze


def session():
    return {
        "schema_version": 1, "mode": "friendly", "town_hall": 13,
        "army_confirmed": True, "scene_confirmed": True,
        "center": {"x": .5, "y": .5},
        "army": [
            {"id": "a", "name": "Electro Dragon", "count": 7, "level": 4, "role": "main", "domain": "air"},
            {"id": "b", "name": "Balloon", "count": 5, "level": 9, "role": "funnel", "domain": "air"},
            {"id": "c", "name": "Archer", "count": 3, "level": 8, "role": "cleanup", "domain": "ground"},
            {"id": "d", "name": "Rage", "count": 2, "level": 6, "role": "spell", "domain": "both"},
        ],
        "annotations": [
            {"id": "th", "kind": "town_hall", "x": .45, "y": .45, "w": .1, "h": .1},
            {"id": "ad", "kind": "air_defense", "x": .7, "y": .42, "w": .06, "h": .06},
            {"id": "west", "kind": "deployment", "x": .06, "y": .3, "w": .09, "h": .4},
            {"id": "east", "kind": "deployment", "x": .85, "y": .3, "w": .09, "h": .4},
        ],
    }


class PlannerTests(unittest.TestCase):
    def test_ranks_air_entry_away_from_confirmed_air_defense(self):
        result = analyze(session())
        self.assertEqual(result["status"], "preview")
        self.assertEqual(result["candidates"][0]["zone_id"], "west")
        self.assertEqual(result["candidates"][0]["clock"], "9 o'clock")
        self.assertIsNone(result["success_probability"])

    def test_every_candidate_conserves_inventory_and_uses_only_its_zone(self):
        source = session()
        for plan in analyze(source)["candidates"]:
            counts = {u["id"]: 0 for u in source["army"]}
            zone = next(x for x in source["annotations"] if x["id"] == plan["zone_id"])
            for step in plan["steps"]:
                counts[step["unit_id"]] += step["count"]
                self.assertEqual(sum(p["count"] for p in step["positions"]), step["count"])
                for p in step["positions"]:
                    self.assertTrue(zone["x"] <= p["x"] <= zone["x"] + zone["w"])
                    self.assertTrue(zone["y"] <= p["y"] <= zone["y"] + zone["h"])
            for reserve in plan["reserves"]:
                counts[reserve["unit_id"]] += reserve["count"]
            self.assertEqual(counts, {u["id"]: u["count"] for u in source["army"]})
            self.assertEqual({r["unit_id"] for r in plan["reserves"]}, {"c", "d"})

    def test_missing_observations_abstain_with_actionable_reasons(self):
        data = session()
        data.update(center=None, army_confirmed=False, scene_confirmed=False)
        data["annotations"] = []
        result = analyze(data)
        self.assertEqual(result["status"], "needs_input")
        self.assertFalse(result["candidates"])
        self.assertGreaterEqual(len(result["issues"]), 5)

    def test_main_force_required(self):
        data = session()
        data["army"] = [u for u in data["army"] if u["role"] == "spell"]
        self.assertEqual(analyze(data)["status"], "needs_input")

    def test_rejects_invalid_numbers_and_out_of_image_regions(self):
        for value in [math.nan, math.inf, -.1, True, "0.3", 10**1000]:
            with self.subTest(value=value):
                data = session()
                data["annotations"][0]["x"] = value
                with self.assertRaises(ValueError):
                    analyze(data)
        data = session()
        data["annotations"][0].update(x=.95, w=.1)
        with self.assertRaises(ValueError):
            analyze(data)

    def test_rejects_bad_inventory_ids_enums_and_unconfirmed_scene(self):
        for edit in [lambda d: d["army"][0].update(count=-1),
                     lambda d: d["army"][0].update(count=1.5),
                     lambda d: d["army"][0].update(role="invented"),
                     lambda d: d["army"][1].update(id="a"),
                     lambda d: d.update(mode="unknown"),
                     lambda d: d.update(schema_version=2),
                     lambda d: d.update(army_confirmed="false")]:
            data = session()
            edit(data)
            with self.subTest(data=data), self.assertRaises(ValueError):
                analyze(data)

    def test_does_not_mutate_session(self):
        data = session()
        before = copy.deepcopy(data)
        analyze(data)
        self.assertEqual(data, before)

    def test_hero_is_single_and_single_unit_deploy_is_legal(self):
        data = session()
        data["army"] = [{"id": "h", "name": "King", "role": "hero", "domain": "ground", "count": 1, "level": 65},
                        {"id": "m", "name": "Golem", "role": "main", "domain": "ground", "count": 1, "level": 9}]
        result = analyze(data)
        self.assertEqual(len(result["candidates"][0]["steps"]), 2)
        data["army"][0]["count"] = 2
        with self.assertRaises(ValueError):
            analyze(data)


if __name__ == "__main__":
    unittest.main()
