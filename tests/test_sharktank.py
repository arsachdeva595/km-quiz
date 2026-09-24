import csv, json, sys, unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "pipeline"))
from import_shark_tank import map_pitch, display_name, domain
from sharktank_rules import RULES, APP_BUCKETS, APP_DEFAULT, HARDWARE_BUCKETS, HARDWARE_DEFAULT
from import_odop import map_product
from odop_rules import RULES as ODOP_RULES


class RulesTest(unittest.TestCase):
    def test_rule_slugs_exist_in_seed(self):
        with open(ROOT / "data" / "business_models.csv", encoding="utf-8") as f:
            slugs = {r["slug"] for r in csv.DictReader(f)}
        used = {s for s, _, _ in RULES if not s.startswith("@")}
        used |= {s for s, _ in APP_BUCKETS + HARDWARE_BUCKETS} | {APP_DEFAULT, HARDWARE_DEFAULT}
        used |= {s for s, _ in ODOP_RULES if s}
        self.assertEqual(used - slugs, set())

    def test_known_pitches(self):
        cases = {
            ("Frozen Momos", "Food and Beverage"): "frozen-and-ready-to-cook-foods",
            ("Kerala Banana Chips", "Food and Beverage"): "healthy-snacks-brand",
            ("Wheelchairs", "Manufacturing"): "medical-devices-startup",
            ("Smart Helmets", "Manufacturing"): "safety-and-security-devices",
            ("Plug and Fly Drones", "Manufacturing"): "deeptech-hardware",
            ("Premium headphones", "Lifestyle/Home"): "consumer-gadgets-brand",
            ("UPI based expense management", "Technology/Software"): "fintech-startup",
            ("EdTech App", "Children/Education"): "edtech-startup",
            ("Book Doctors Appointments Video Consultation", "Medical/Health"): "healthtech-startup",
            ("Digital nanny-hiring platform", "Medical/Health"): "services-marketplace-app",
            ("Affordable designer home decor", "Lifestyle/Home"): "handcrafted-home-decor",
            ("Abayas, naquabs and dupatta brand", "Beauty/Fashion"): "d2c-apparel-brand",
            ("Portable ECG Device", "Medical/Health"): "medical-devices-startup",
            ("Himalayan whiskey", "Liquor/Alcohol"): "beverage-brand",
            ("Renting e-bike for mobility in private spaces", "Vehicles/Electrical Vehicles"): "ev-charging-and-rental",
        }
        for (desc, industry), slug in cases.items():
            self.assertEqual(map_pitch(desc, industry)[0], slug, desc)

    def test_odop_products(self):
        cases = {
            "Channapatna Toys": "toys-and-games-brand",
            "Lucknow Chikan Craft & Lucknow Zardozi": "handloom-textiles-brand",
            "Kolhapur Jaggery (Sugarcane Products etc)": "honey-and-organic-produce",
            "Cane & Bamboo Handicrafts (Mats)": "handcrafted-home-decor",
            "Byadagi Chilies": "spice-processing-unit",
            "Alphonso Mangoes": "fruit-and-vegetable-processing",
            "Processed Prawn & Shrimp": "seafood-processing",
            "Moradabad Metal Craft": "handcrafted-home-decor",
            "Chemicals (Chemicals,Agro Chemicals, Pesticide, Pharmaceutical, API)": "",
        }
        for product, slug in cases.items():
            self.assertEqual(map_product(product), slug, product)

    def test_display_name(self):
        self.assertEqual(display_name("BluePineFoods"), "Blue Pine Foods")
        self.assertEqual(domain("https://www.boozup.net/"), "boozup.net")

    def test_overrides_use_valid_keys(self):
        pitches = json.loads((ROOT / "data" / "sharktank" / "pitches.json").read_text(encoding="utf-8"))
        keys = {p["key"] for p in pitches}
        with open(ROOT / "data" / "sharktank" / "overrides.csv", encoding="utf-8") as f:
            for r in csv.DictReader(f):
                self.assertIn(r["key"], keys)


class DerivedIdeasTest(unittest.TestCase):
    def test_no_duplicate_names_and_valid_overrides(self):
        from derive_ideas import norm_key
        with open(ROOT / "data" / "ideas_catalog.csv", encoding="utf-8") as f:
            names = [r["name"] for r in csv.DictReader(f)]
        with open(ROOT / "data" / "ideas_derived.csv", encoding="utf-8") as f:
            derived = list(csv.DictReader(f))
        names += [r["name"] for r in derived]
        keys = [norm_key(n) for n in names]
        self.assertEqual(len(keys), len(set(keys)))
        pitches = {p["key"] for p in json.loads((ROOT / "data" / "sharktank" / "pitches.json").read_text(encoding="utf-8"))}
        odop = {"odop:" + norm_key(d["product"]).replace(" ", "-")
                for d in json.loads((ROOT / "docs" / "data" / "odop.json").read_text(encoding="utf-8"))}
        with open(ROOT / "data" / "ideas_derived_overrides.csv", encoding="utf-8") as f:
            bad = [r["ref"] for r in csv.DictReader(f) if r["ref"] not in pitches | odop]
        self.assertEqual(bad, [], "overrides point at unknown pitches or ODOP products")


if __name__ == "__main__":
    unittest.main()
