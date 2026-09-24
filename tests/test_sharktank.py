import csv, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from import_shark_tank import map_pitch, display_name, domain
from sharktank_rules import RULES


class RulesTest(unittest.TestCase):
    def test_rule_slugs_exist_in_seed(self):
        with open(ROOT / "data" / "ideas_seed.csv", encoding="utf-8") as f:
            slugs = {r["slug"] for r in csv.DictReader(f)}
        self.assertEqual({s for s, _, _ in RULES} - slugs, set())

    def test_known_pitches(self):
        cases = {
            ("Frozen Momos", "Food and Beverage"): "frozen-and-ready-to-cook-foods",
            ("Kerala Banana Chips", "Food and Beverage"): "healthy-snacks-brand",
            ("Wheelchairs", "Manufacturing"): "hardware-product-startup",
            ("Affordable designer home decor", "Lifestyle/Home"): "handcrafted-home-decor",
            ("Abayas, naquabs and dupatta brand", "Beauty/Fashion"): "d2c-apparel-brand",
            ("Portable ECG Device", "Medical/Health"): "medical-devices-startup",
            ("Himalayan whiskey", "Liquor/Alcohol"): "beverage-brand",
            ("Renting e-bike for mobility in private spaces", "Vehicles/Electrical Vehicles"): "ev-charging-and-rental",
        }
        for (desc, industry), slug in cases.items():
            self.assertEqual(map_pitch(desc, industry)[0], slug, desc)

    def test_display_name(self):
        self.assertEqual(display_name("BluePineFoods"), "Blue Pine Foods")
        self.assertEqual(domain("https://www.boozup.net/"), "boozup.net")

    def test_overrides_use_valid_keys(self):
        pitches = json.loads((ROOT / "data" / "sharktank" / "pitches.json").read_text(encoding="utf-8"))
        keys = {p["key"] for p in pitches}
        with open(ROOT / "data" / "sharktank" / "overrides.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.assertIn(r["key"], keys)


if __name__ == "__main__":
    unittest.main()
