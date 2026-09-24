"""
Keyword rules that map a district's ODOP product to a seed idea slug.

Rules are (slug, regex); first match on the product name wins. Industrial
products with no small-founder equivalent (cement, pharma, coal, IT…) stay
unmapped: the district still gets its ODOP card in the quiz, just no idea boost.
An empty slug marks those on purpose. Manual fixes go in data/odop/overrides.csv.
"""

RULES = [
    # Heavy industry — intentionally unmapped.
    ("",                             r"chemical|pharma|cement|coal|mica|quartz|mineral|refractory|steel and|tmt|aluminium|esdm|it/ites|software|rubber|plastic|resin|fullers|ceramic tiles"),
    # Crafts first — names like "Banana Fiber Products" or "Wooden Toys" must not hit food rules.
    ("toys-and-games-brand",         r"toy"),
    ("furniture-workshop",           r"furniture|teak"),
    ("handloom-textiles-brand",      r"chikan|zardo|zari"),
    ("jewellery-brand",              r"jewel|jewll|gems|filigree|tarakashi|thewa|bangle|bead|pearl|agate|bindi|tikuli"),
    ("pottery-studio",               r"terracotta|pottery|ceramic product"),
    ("stone-and-marble-products",    r"granite|marble|sandstone|kota stone|cut stone|stale stone|stone (based|product|work)|yellow stone"),
    ("handcrafted-home-decor",       r"craft|carving|carved|wood|brass|bell metal|dokra|dhokra|bidar|copper|metal craft|ghungroo|painting|patachitra|pattachitra|sohrai|aipan|tarkashi|tarkash|lacquer|wall hanging|mask|firozabad|glass|handicraft|horn|musical|dholak|veena|flute|decorative|golden grass|sabai|kinhal|zinc utensils|brass utensils|metal utensils"),
    ("crockery-and-kitchenware-store", r"stainless steel|kitchen ware|kitchenware"),
    ("eco-friendly-products-brand",  r"bamboo|cane &|moonj|sital pati|wicker|areca leaf|arecanut leaf|sal leaf|banana fib|natural fib|jute|coir|handmade paper|wheat stalk|nettle|sonamukhi"),
    ("footwear-brand",               r"footwear|shoes"),
    ("leather-goods-workshop",       r"leather"),
    ("sports-goods-brand",           r"sports"),
    ("d2c-apparel-brand",            r"ready.?made|readymade|apparel|garment|hosiery|jean|denim|jacket|bags & garments|crochet"),
    ("handloom-textiles-brand",      r"handloom|saree|silk|shawl|pashmina|ikat|ikkat|kalamkari|bandhani|print|embroider|zari|zardo|chikan|phulkari|applique|kasheeda|kosa|tasar|kota doria|chanderi|carpet|dari|durries|towel|bedsheet|furnishing|made ups|textile|powerloom|yarn|cotton products|gauze|chamba rumal|bawan booti|risha|wangkhei|phanek|chanbi|woollen|patta|bomkai|khambhaliya|bhujodi|lambani|gollabama"),
    ("light-engineering-unit",       r"engineering|auto ?compon|automobile|auto parts|machine tool|machiner|foundry|forged|fastner|fastener|metal casting|lock|motor pumps|tractor|rim and axle|diesel engine|implements|farm equipment|scientific equipment|sanitary fittings|mining"),
    ("paper-bag-unit",               r"packaging|corrugated"),
    ("local-tour-guide",             r"tourism|sightseeing"),

    # Food and agriculture
    ("seafood-processing",           r"marine|fish|shrimp|prawn|seafood"),
    ("poultry-farm",                 r"kadaknath|poultry"),
    ("dairy-farm",                   r"milk|dairy|ghee"),
    ("mushroom-farming",             r"mushroom"),
    ("nursery-and-plants",           r"floricult|orchid|flower"),
    ("personal-care-brand",          r"perfume|aromatic plant|lemon grass|mentha|menthol|lavender|agarwood|oil - agar|seabuckthorn"),
    ("nutrition-supplements-brand",  r"ayurvedic|herbal|biopharma"),
    ("beverage-brand",               r"\btea\b|coffee|feni"),
    ("honey-and-organic-produce",    r"honey|jaggery|sugarcane|cane sugar|minor forest|mahua|chirounji|tamarind|lac products|\blac\b"),
    ("pickle-and-papad-brand",       r"pickle"),
    ("sweet-shop",                   r"mithai|bal mithai|confectionery|marcha chura"),
    ("home-bakery",                  r"bakery|biscuit"),
    ("healthy-snacks-brand",         r"namkeen|nagali|makhana|foxnut|millet|kodo|kutki|ragi|buck ?wheat|peanut|groundnut"),
    ("cold-pressed-oil-mill",        r"\boil\b|mustard|edible oil|vegetable oil|cotton seed"),
    ("spice-processing-unit",        r"turmeric|haladi|ginger|chill|chili|mircha|jholokia|cardamom|garlic|coriander|cilantro|hing|asafoetida|saffron|spice|pan meethi"),
    ("fruit-and-vegetable-processing", r"mango|banana|pineapple|orange|mandarin|kinnow|citrus|kiwi|apple|apricot|guava|papaya|litchi|tomato|onion|potato|vegetable|amla|aamla|gooseberry|jackfruit|dragon|strawberr|grape|raisin|watermelon|custard|lemon|chikoo|sapota|peas|fruit"),
    ("agro-processing-unit",         r"rice|paddy|pulses|dal|daal|gram|kholar|kidney beans|maize|corn|soya|wheat|cashew|arecanut|areca nut|coconut|walnut|pecan|dry fruits|agro|agri|agricultural|food processing|food products|cotton|de-oiled|fmcg"),
]
