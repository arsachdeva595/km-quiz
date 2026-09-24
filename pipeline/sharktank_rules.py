"""
Keyword rules that map a Shark Tank India pitch to a seed idea slug.

Each rule is (slug, regex, industries). Two slugs are placeholders that a
second pass resolves by what the founder actually does day to day (the tech
itself can be built by a co-founder or team):
  "@app"      → APP_BUCKETS      (EdTech, FinTech, B2B SaaS, …)
  "@hardware" → HARDWARE_BUCKETS (gadgets, safety devices, deep tech, …)
 The first rule that matches the pitch's
"Business Description" wins. `industries` limits a rule to those dataset
industries (None = any). Manual fixes go in data/sharktank/overrides.csv,
which beats every rule.
"""

TECH = {"Technology/Software"}
HEALTH = {"Medical/Health"}
AGRI = {"Agriculture"}
PETS = {"Animal/Pets"}
FOOD = {"Food and Beverage"}
FASHION = {"Beauty/Fashion"}
KIDS = {"Children/Education"}
VEHICLES = {"Vehicles/Electrical Vehicles"}
SPORTS = {"Fitness/Sports/Outdoors"}
LIQUOR = {"Liquor/Alcohol"}

RULES = [
    # ── Industry-first rules ────────────────────────────────────────────────
    ("beverage-brand",               r".", LIQUOR),
    ("pet-food-and-treats",          r"food|treat|feed|ice cream", PETS),
    ("agritech-devices",             r"livestock|cattle|ear tag", PETS),
    ("@hardware",                    r"gps|tracker|dna", PETS),
    ("pet-grooming",                 r".", PETS),
    ("farm-stay-agri-tourism",       r"tourism", AGRI),
    ("hydroponics-and-urban-farming", r"hydro?phonic|hydroponic", AGRI),
    ("b2b-marketplace",              r"e-commerce platform", AGRI),
    ("agritech-devices",             r".", AGRI),
    ("ev-charging-and-rental",       r"rent|leasing|subscription|sharing", VEHICLES),
    ("local-delivery-service",       r"taxi|shuttle", VEHICLES),
    ("@app",                         r"qr based", VEHICLES),
    ("@hardware",                    r"fuel caps|helmet|pillow|gyrocopter|aircraft|hydrogen", VEHICLES),
    ("ev-assembly",                  r".", VEHICLES),
    ("elder-care-service",           r"elder", HEALTH),
    ("nutrition-supplements-brand",  r"supplement|protein|tablet|shilajit|vitamin|magnesium|ayurved", HEALTH),
    ("nutrition-coaching",           r"weight|fasting|diet", HEALTH),
    ("personal-care-brand",          r"nasal strip|body adhesive|period panties|dental care brand|cannabis|cannibis", HEALTH),
    ("physio-and-massage",           r"pain management|rehabilitation", HEALTH),
    ("d2c-apparel-brand",            r"scrubs|apparel", HEALTH),
    ("medical-devices-startup",      r"device|machine|system|test|wearable|monitor|stethoscope|prosthetic|kit|wheelchair|ecg|eeg|headband|hearing|screening|diagnos|dialysis|cooling|uroflow|dental|orthotic|aid", HEALTH),
    ("@app",                         r".", HEALTH),
    ("kids-enrichment-classes",      r"course|school|classes|brain development|chess|music classes|teaching|therapy|therapeutic", KIDS),
    ("coaching-centre",              r"coaching|iit|jee", KIDS),
    ("toys-and-games-brand",         r"toy|doll|busy board|games|collectible", KIDS),
    ("publishing-and-comics",        r"comic|book", KIDS),
    ("d2c-apparel-brand",            r"kidswear|baby|furniture|makeup", KIDS),
    ("@hardware",                    r"device|gadget", KIDS),
    ("@app",                         r".", KIDS),
    ("sports-coaching-academy",      r"institute|academy|training|calisthenics|chess|sport for|recreation", SPORTS),
    ("sports-goods-brand",           r"bat|bowling|paddle|archery|shop|skateboard|gear|equipment|tools|sportswear|apparel|peripherals", SPORTS),
    ("capsule-and-budget-hotel",     r"pod hotel", SPORTS),
    ("nutrition-supplements-brand",  r"multivitamin|probiotic", SPORTS),
    ("nutrition-supplements-brand",  r"sea-buckthorn", FASHION),
    ("@hardware",                    r"sensor|ring", SPORTS),
    ("@app",                         r".", SPORTS),

    # Tech industry: apps, AI, platforms
    ("b2b-saas-startup",             r"software|automation|enterprise|optimization|character recognition|fees payment|builder|analytics|facade|fasade", TECH),
    ("b2b-marketplace",              r"marketplace|kirana|truck drivers|recruiters|design marketplace", TECH),
    ("video-editing-service",        r"animation|comics|content studio|dubbing|localisation|localization", TECH),
    ("translation-services",         r"translation", TECH),
    ("b2b-saas-startup",             r"manage plants", None),
    ("digital-agency",               r"advertisement|influencer|sales agent|beauty brands", TECH),
    ("website-development",          r"software development|websites", TECH),
    ("@hardware",                    r"robot|drone|aerial|underwater|wearable|virtual reality|4d", TECH),
    ("test-prep-online",             r"learning|courses|chess|edtech|interviews|career|school|classes|learn", TECH),
    ("@app",                         r".", TECH),

    # ── Generic rules (any industry) ─────────────────────────────────────────
    ("@hardware",                    r"machine|waterless|wheelchair|wearable|air purifier|cleaning device|massager|smart watch", None),
    ("personal-care-brand",          r"ayurved", FASHION),
    ("b2b-marketplace",              r"yarn|b2b|fabric sourcing", None),
    # Services and events
    ("funeral-services",             r"funeral|last rites|beyond life", None),
    ("event-planning",               r"surprise|proposal|event platform|celebration|private theatre", None),
    ("wedding-planning",             r"wedding planner|wedding hall|wedding ceremonial", None),
    ("event-catering",               r"catering", None),
    ("pooja-and-incense-products",   r"pooja|puja|daan|yajna|incense|temple|for gods|devotional|spiritual", None),
    ("florist-and-flower-delivery",  r"flowers?\b", None),
    ("custom-gifting-store",         r"gift", None),
    ("coworking-and-coliving",       r"co-?working|co-?living|working spaces|accomodation|student housing", None),
    ("capsule-and-budget-hotel",     r"napping pod|hotels for hours|pod hotel", None),
    ("gym",                          r"\bgym", None),
    ("home-cleaning-service",        r"helpers|homemakers|service request", None),
    ("local-delivery-service",       r"courier|parcel", None),
    ("photography-studio",           r"photography", None),
    ("boutique-tailoring",           r"tailor", None),
    ("insurance-agency",             r"insurance", None),
    ("legal-documentation",          r"dispute|despite resolution", None),
    ("real-estate-brokerage",        r"real estate|fractional", None),
    ("interior-design-studio",       r"interior|3d home|three-dimensional home|pre-?fabricated|construction", None),
    ("recycling-and-waste",          r"waste|scrap|recycl|compost|upcycl|plastic", None),
    ("eco-friendly-products-brand",  r"\beco|sustainab|bamboo|bioplastic|afforestation|climate|biodegrad|paper goods|handmade paper", None),
    ("solar-installation",           r"solar", None),
    ("clothing-rental",              r"rental|on rent|give on rent", None),

    # Food
    ("mushroom-farming",             r"mushroom", None),
    ("nursery-and-plants",           r"nursery", None),
    ("honey-and-organic-produce",    r"\bhoney\b|organic products|organic grocery|jaggery|jamun|organic spices", None),
    ("spice-processing-unit",        r"spice|\batta\b|flour|\baata\b", None),
    ("cold-pressed-oil-mill",        r"cold pressed|edible oil", None),
    ("dairy-farm",                   r"milk|a2|dairy|cheese|eggs", None),
    ("poultry-farm",                 r"chicken chips", None),
    ("frozen-and-ready-to-cook-foods", r"momo|frozen|ready to cook|jackfruit|instant curr|soup|ready-to-eat|soya chaap|plant based meat|plant-based meat|diy food|breakfast option|overnight oats", None),
    ("pickle-and-papad-brand",       r"pickle|chutney|sauce|relish|jam|marinade|fruit spread|mukhwas|mouth fresh", None),
    ("cafe",                         r"cafe|coffee and snacks", None),
    ("cloud-kitchen",                r"cloud.?kitchen|virtual restaurant|where's the food|homemade after delivery|homemade delicacies|delicacies", None),
    ("quick-service-food-outlet",    r"qsr|restaurant|food kart|food truck|maggi|pizza|kulche|parathas|cuisine|dining|pancake|kunafa", None),
    ("ice-cream-and-desserts-brand", r"ice.?cream|ice-?pops|gelato|dessert|kheer|cheesecake|waffles", None),
    ("healthy-snacks-brand",         r"snack|chips|nachos|nuts|dry fruits|popcorn|muesli|granola|energy bar|protein bar|bars\b|peanut butter|millet|superfood|super food|guilt|protein|diabetes|gluten|healthy|nutri|kamdhenu|puranpoli|ayurvedic enriched|wellness in the form", None),
    ("sweet-shop",                   r"sweet|mithai|candy|candies|lollipop|chocolate|confection|chewing gum", None),
    ("home-bakery",                  r"cake|bakery|cookie|bread", None),
    ("juice-and-shake-bar",          r"fruit juices|fruit salad|fresh fruits|salads|smoothie", None),
    ("beverage-brand",               r"coffee|espresso|cocktail|\btea\b|tea dip|matcha|kombucha|beverage|drink|juice|lemonade|shake|water|mixer|bubble tea|spirit|beer|mead", None),
    ("traditional-health-foods",     r"ayurved|herbal|vegan fermented|hemp|fermented", None),
    ("nutrition-coaching",           r"keto|diet", None),

    # Beauty and fashion
    ("sneaker-and-streetwear-resale", r"sneaker resale|sneaker collection|pre-owned|thrift|refurbished", None),
    ("online-thrift-store",          r"resale", None),
    ("beauty-salon",                 r"salon|skincare services|bra fitting", None),
    ("nail-studio",                  r"nail", None),
    ("jewellery-brand",              r"jewel|jewll|diamond|bangle|bindi|stones", None),
    ("handloom-textiles-brand",      r"handloom|saree|paithani|silk|handwoven|lucknow|jaipur|fabric retail|fabric sourcing|fabrics", None),
    ("footwear-brand",               r"shoe|footwear|sneaker|insole|loafer", None),
    ("bags-and-accessories-brand",   r"\bbags?\b|backpack|sling|clutch|handbag|luggage|suitcase|accessories|eyewear|eye wear|watches", None),
    ("optical-store",                r"eyewear|eye wear", None),
    ("handmade-soap-and-cosmetics",  r"soap|lipstick|crochet", None),
    ("personal-care-brand",          r"skin|\bhair|beauty|cosmetic|makeup|make-up|perfume|fragrance|attar|deo|toilet spray|intimate hygiene|urine bag|waterless bathing|oil|cigarette|cannabis|care products|toothpaste|toothbrush|diaper|home care|belly button", None),
    ("home-cleaning-products-brand", r"clean|detergent|undergarment wash|freshner|air purifier", None),
    ("d2c-apparel-brand",            r"wear|cloth|apparel|fashion|lifestyle products for women|dress|denim|streetwear|lingerie|swim|underwear|innerwear|shapewear|petticoat|sleeves|abaya|kurta|sarees|sikh|tactical|vest|maternity|textile", None),

    # Home, crafts, manufacturing
    ("toys-and-games-brand",         r"toy|games|balance bike|playing equipment|diy kits|satellites by kids|microscope|crayon", None),
    ("handcrafted-home-decor",       r"decor|handicraft|handcrafted|artisan|art & craft|art by|mural|neon|rug|clay|copper|brass|marble|handmade|hand-painted|design, aesthetics", None),
    ("crockery-and-kitchenware-store", r"stainless steel|kitchenware|dinnerware|plates|borosilicate|lunch box", None),
    ("furniture-workshop",           r"furniture|chair|mattress|kitchens", None),
    ("stationery-and-art-supplies",  r"stationery|journal|planner|paints", None),
    ("used-book-store",              r"books", None),
    ("sports-goods-brand",           r"cycling|bicycle|sports", None),
    ("home-painting-contractor",     r"wall building|surface textures|tiles", None),
    ("content-and-media-platform",   r"web series|movie|audio content|streaming", None),
    ("publishing-and-comics",        r"publishing", None),
    ("travel-agency",                r"travel", None),
    ("@app",                         r"\bapp\b|platform|dating|social|meetup|club|conversations|anger management|astrology|letter writing", None),
    ("@hardware",                    r"smart|device|detector|disposal|deterrence|machine|lock|invention|automatic|autonomous|portable|wearable|3d printing|drone|television|speaker|audio|headphone|jet spray|urinal|cradle|fan rod|drinking shield|storage|fire extinguisher|cooker|cooling|billing|lighting|dryer|stick|telescope|card|currency|packaging|chemical|contamination|pipelines|congestion|fuel|mosquito|material|mats|panels|restoration|construction|robot|attachment|ashtray|mirroring|sauna|glass", None),
]


# Second pass for "@app": first match on the description wins.
APP_BUCKETS = [
    ("fintech-startup",            r"credit|lending|stock|trading|expense|upi|payment|piggy|gold|money|financ|rewards|fractional|currency|calculator|transaction"),
    ("healthtech-startup",         r"health|doctor|pharmacy|pregnan|parenting|mental|wellness|ayurved|transplant|cancer|infertility|iui|vision|autism|fitness|weight|diagnos|emergency|genetic|dna|neuro|therap|disabilit|care\b"),
    ("edtech-startup",             r"learn|edtech|education|school|student|course|skill|teach|child|kids|scholarship|career|interview|chess|book|bullying|talent|teens"),
    ("gaming-and-esports",         r"gam|esport|metaverse|roblox|virtual reality|cricket game"),
    ("content-and-media-platform", r"content|audio|news|music|stream|comic|animation|astrology|influencer|image|creator|dubbing|localis|web series|movie|culture"),
    ("services-marketplace-app",   r"booking|hiring|nanny|salon|saloon|auto care|travel|itiner|housing|washroom|service|truck|kabaddi|wrestling|event|luxury|try-on|vehicle tag|security"),
    ("community-and-social-app",   r"social|community|dating|meetup|club|conversations|lgbt|network|sharing|anger|letter|activity"),
    ("b2b-saas-startup",           r"business|enterprise|software|automation|ai|sales|reminder|brands|kirana|b2b|msme|welfare|android|character"),
]
APP_DEFAULT = "community-and-social-app"

# Second pass for "@hardware".
HARDWARE_BUCKETS = [
    ("medical-devices-startup",     r"wheelchair|visually impaired|braille|massager|menstrual|anti-smoking"),
    ("safety-and-security-devices", r"helmet|lock|safety|security|fire|extinguisher|deterrence|suicid|fan rod|gps|tracker|disinfect|guardian|stick|mosquito|lpg|pollution"),
    ("deeptech-hardware",           r"robot|drone|aerial|underwater|aircraft|gyrocopter|hydrogen|satellite|3d printing|virtual reality|4d|sensor|iot|spatial|fuel caps|payment wearables|dna"),
    ("industrial-solutions",        r"pothole|contamination|pipeline|congestion|packaging|billing|chemical|construction|material|mats|panels|restoration|cooling|storage solutions|urinal|waterless|washing machine|tea glass|juice making|smart card|currency|detector|disposal"),
]
HARDWARE_DEFAULT = "consumer-gadgets-brand"
