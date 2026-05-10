from __future__ import annotations

import csv
import re
import sqlite3
import sys
from pathlib import Path


DB_PATH = Path(r"C:\Collectables\Inventory\inventory.db")
DEFAULT_CSV_PATH = Path(r"C:\Users\ddepe\Downloads\AppSheet.ViewData.2026-04-10.csv")
UNMATCHED_REPORT_PATH = Path(r"C:\Collectables\Inventory\appsheet_inventory_unmatched.csv")
SOURCE_NAME = "AppSheet"

COMMON_TEXT_REPLACEMENTS = (
    (r"\blicenced\b", "licensed"),
    (r"\bclassifed\b", "classified"),
    (r"\bbeatlejuice\b", "beetlejuice"),
    (r"\bspangler\b", "spengler"),
    (r"\bzedmore\b", "zeddmore"),
    (r"\bmichaelangelo\b", "michelangelo"),
    (r"\bmichael angelo\b", "michelangelo"),
    (r"\bpricess\b", "princess"),
    (r"\bwierd\b", "weird"),
    (r"\bsuperheros\b", "super heroes"),
)

SOURCE_ROW_CORRECTIONS = {
    (
        "Sectaurs",
        "Vintage Sectaurs",
        "Sectaurs",
        "Commander Waspax and Winged",
    ): {
        "Item": "Commander Waspax and Wingid",
    },
    (
        "Sectaurs",
        "Vintage Sectaurs",
        "Sectaurs",
        "Skitto and Toxcid",
    ): {
        "Item": "Skito and Toxcid",
    },
    (
        "Star Wars",
        "Vintage Star Wars",
        "G",
        "Artoo-Detoo (R2-D2) (with Sensorscope)",
    ): {
        "Item": "R2-D2 With Sensorscope",
    },
    (
        "Star Wars",
        "Vintage Star Wars",
        "M",
        "Artoo-Detoo (R2-D2) with pop-up Lightsaber",
    ): {
        "Item": "R2-D2 With Pop-Up Lightsaber",
    },
    (
        "Micromen",
        "Micromen Command Series",
        "Micromen Command Series",
        "M182 Alice",
    ): {
        "Wave": "Lady Command",
    },
    (
        "Micromen",
        "Micromen Command Series",
        "Micromen Command Series",
        "M151 East",
    ): {
        "Wave": "Command 1",
    },
    (
        "PeeWee's Playhouse",
        "Vintage PeeWee",
        "PeeWee's Playhouse",
        "Talking PeeWee",
    ): {
        "Line": "Vintage Matchbox",
        "Wave": "Large Figures",
        "Item": "Pee-Wee Talking",
    },
    (
        "PeeWee's Playhouse",
        "Vintage PeeWee",
        "PeeWee's Playhouse",
        "Large Pterri",
    ): {
        "Line": "Vintage Matchbox",
        "Wave": "Large Figures",
        "Item": "Pterri",
    },
    (
        "PeeWee's Playhouse",
        "Vintage PeeWee",
        "PeeWee's Playhouse",
        "Large Chairry",
    ): {
        "Line": "Vintage Matchbox",
        "Wave": "Large Figures",
        "Item": "Chairry #3530",
    },
    (
        "M.U.S.C.L.E.",
        "Vintage M.U.S.C.L.E.",
        "Wave 1",
        "Hard Knockin' Rockin' Ring Wrestling Arena",
    ): {
        "Line": "M.U.S.C.L.E. Men",
        "Wave": "Accessories",
        "Item": "Hard Knockin' Rockin' Ring Wrestling Arena #2677",
    },
    (
        "Star Trek",
        "Star Trek",
        "Wave 1",
        "Captain Kirk",
    ): {
        "Line": "Star Trek 1974-1977",
    },
    (
        "Star Trek",
        "Star Trek",
        "Wave 1",
        "Doctor McCoy",
    ): {
        "Line": "Star Trek 1974-1977",
    },
    (
        "Star Trek",
        "Star Trek",
        "Wave 1",
        "Klingon",
    ): {
        "Line": "Star Trek 1974-1977",
    },
    (
        "Strawberry Shortcake",
        "Vintage Strawberry Shortcake",
        "Wave 5",
        "Party Pleasers: Mint Tulip with Marsh Mallard",
    ): {
        "Line": "Party Pleaser",
        "Wave": "",
        "Item": "Mint Tulip (with Marsh Mallard)",
    },
    (
        "Strawberry Shortcake",
        "Vintage Strawberry Shortcake",
        "Wave 5",
        "Party Pleasers: Apple Dumplin with TeaTime Turtle",
    ): {
        "Line": "Party Pleaser",
        "Wave": "",
        "Item": "Apple Dumplin (with TeaTime Turtle)",
    },
    (
        "Strawberry Shortcake",
        "Vintage Strawberry Shortcake",
        "Wave 5",
        "Party Pleasers: Angel Cake with Souffle Skunk",
    ): {
        "Line": "Party Pleaser",
        "Wave": "",
        "Item": "Angel Cake (with Souffle)",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Minis",
        "Cozy Heart Penguin - Mini",
    ): {
        "Line": "Vintage Care Bears - Mini PVC Figures",
        "Wave": "1985 Assortment",
        "Item": "Cozy Heart Penguin",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Professor Coldheart",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1984 Assortment",
        "Item": "Professor Cold Heart",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Lotsa Heart Elephant with Mighty Trunk",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Lotsa Heart Elephant",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Grams Bear with Lovin Basket",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1983 Assortment",
        "Item": "Grams Bear",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Gentleheart Lamb with Peek-a-boo Bell",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Gentle Heart Lamb",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Friend Bear with Friendly Sprinkler",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1982 Assortment",
        "Item": "Friend Bear",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Cozy Heart Penguin with Nice-Skates",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Cozy Heart Penguin",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Cloud Keeper with Fluffy Cloud Broom",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1984 Assortment",
        "Item": "The Cloud Keeper",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Brightheart Raccoon with Clever Candle",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Bright Heart Raccoon",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Braveheart Lion with Trusty Shield",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Brave Heart Lion",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Birthday Bear with Happy Birthday Banner",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1982 Assortment",
        "Item": "Birthday Bear",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Baby Tugs Bear with Big Digity Bucket",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1983 Assortment",
        "Item": "Baby Tugs",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Baby Hugs Bear with Sweet Lickity Lolipop",
    ): {
        "Line": "Vintage Care Bears - Poseable Figures",
        "Wave": "1983 Assortment",
        "Item": "Baby Hugs",
    },
    (
        "Care Bears",
        "Vintage Care Bears",
        "Wave 2",
        "Swiftheart Rabbit with Speedy Skateboard",
    ): {
        "Line": "Vintage Care Bears - Poseable Care Bear Cousins",
        "Wave": "1985 Assortment",
        "Item": "Swift Heart Rabbit",
    },
    (
        "Tron",
        "Tron",
        "Tron",
        "Flynn",
    ): {
        "Line": "Tomy Tron",
        "Wave": "Basic Series",
    },
    (
        "Tron",
        "Tron",
        "Tron",
        "Sark",
    ): {
        "Line": "Tomy Tron",
        "Wave": "Basic Series",
    },
    (
        "Tron",
        "Tron",
        "Tron",
        "Tron",
    ): {
        "Line": "Tomy Tron",
        "Wave": "Basic Series",
    },
    (
        "Tron",
        "Tron",
        "Tron",
        "Warrior",
    ): {
        "Line": "Tomy Tron",
        "Wave": "Basic Series",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Baboo",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Evil Space Aliens [8" Scale]',
        "Item": "Baboo #2210",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Blue Ranger",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Collectible Figures - Series 1",
        "Item": "Blue Ranger #2300",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Bones",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Evil Space Aliens [8" Scale]',
        "Item": "Bones #2210",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "King Sphinx",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Evil Space Aliens [8" Scale]',
        "Item": "King Sphinx #2210",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Pink Ranger",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Collectible Figures - Series 1",
        "Item": "Pink Ranger #2300",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Saba the Tiger Sabre",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Role Playing",
        "Item": "Saba (The Talking Tibger Saber) #2254",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 1",
        "Tyrannosaurus Battle Bike",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Battle Bikes",
        "Item": "Tyrannosaurus Rex Battle Bike & Red Ranger #2230",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Goo Fish",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Deluxe Evil Space Aliens [8" Scale] - Series 1',
        "Item": "Goo Fish #2217",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Guitardo",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Deluxe Evil Space Aliens [8" Scale] - Series 1',
        "Item": "Guitardo #2215",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Karate Kickin Trini",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Karate Action [8" Scale]',
        "Item": "Karate Choppin' Trini (Yellow Ranger) #2205",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Killer Bite Slippery Shark",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Evil Space Aliens - Series 1",
        "Item": "Killer Bite Slippery Shark #2336",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Pirantis Head",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Deluxe Evil Space Aliens [8" Scale] - Series 1',
        "Item": "Pirantis Head #2214",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Power Dome Morphin Playset",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Accessories",
        "Item": "Power Dome Morphin Playset #2290",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Red Dragon Thunderzord",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Zords",
        "Item": "Red Dragon ThunderZord #2225",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Socadillo",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": 'Deluxe Evil Space Aliens [8" Scale] - Series 1',
        "Item": "Socadillo #2216",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 2",
        "Tor the Shuttlezord",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Zords",
        "Item": "Tor the ShuttleZord #2242",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 3",
        "Evil Light Lord Zed",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Evil Space Aliens - Series 2",
        "Item": "Evil Light Lord Zedd #2337",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 3",
        "Head Butting Robo Goat",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Evil Space Aliens - Series 2",
        "Item": "Head Butting Robogoat #2342",
    },
    (
        "Power Rangers",
        "Mighty Morphin Power Rangers",
        "Wave 3",
        "Snapping Chest Flytrap",
    ): {
        "Line": "Mighty Morphin Power Rangers",
        "Wave": "Evil Space Aliens - Series 2",
        "Item": "Snapping Chest Invenusable Fly Trap #2341",
    },
    (
        "Real Ghostbusters",
        "Hasbro Retro Ghostbusters",
        "Wave 1",
        "Stay-Puft Marshmallow Man",
    ): {
        "Line": "Hasbro Retro Ghostbusters",
        "Wave": "Classic Retro",
        "Item": "Stay Puft",
    },
    (
        "Real Ghostbusters",
        "Hasbro Retro Ghostbusters",
        "Wave 1",
        "Winston Zedmore with Chomper Ghost",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 1",
        "Item": "Winston Zeddmore (Chomper Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 2",
        "Bad-Too-The-Bone Ghost",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 2",
        "Item": "Bad-to-the-Bone Ghost",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 2",
        "Gooper Ghost-Sludge Bucket",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 2",
        "Item": "Sludge Bucket",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 3",
        "Firehouse",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 3",
        "Item": "Fire Station Headquarters",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 3",
        "Fright Feature Egon Spangler",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 3",
        "Item": "Egon Spengler (Soar Throat Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 3",
        "Fright Feature Peter Venkman",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 3",
        "Item": "Peter Venkman (Gruesome Twosome Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 3",
        "Fright Feature Ray Stantz",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 3",
        "Item": "Ray Stantz (Jail Jaw Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 3",
        "Fright Feature Winston Zedmore",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 3",
        "Item": "Winston Zeddmore (Scream Roller Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 4",
        "Fright Feature: Janine Melnitz",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 4",
        "Item": "Janine Melnitz (Tickler Ghost)",
    },
    (
        "Real Ghostbusters",
        "Vintage Real Ghostbusters",
        "Wave 4",
        "Haunted Human: Ex-Cop",
    ): {
        "Line": "Vintage Real Ghostbusters",
        "Wave": "Wave 4",
        "Item": "X-Cop",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "Green Goblin",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "Human Torch",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "Invisible Girl",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "Mr. Fantastic",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "Spiderman",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "World's Greatest Super Heros",
        "World's Greatest Superheros",
        "World's Greatest Super Heros",
        "The Thing",
    ): {
        "Property": "Marvel Comics",
        "Line": "WGSH - Marvel",
    },
    (
        "Power Lords",
        "Vintage Power Lords",
        "Vintage",
        "Adam Power",
    ): {
        "Line": "Basic Series",
        "Wave": "Basic Series",
    },
    (
        "Power Lords",
        "Vintage Power Lords",
        "Vintage",
        "Ggripptogg",
    ): {
        "Line": "Basic Series",
        "Wave": "Basic Series",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Good Knight (34)",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "1984 Series",
        "Item": "Good Knight",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Creepy (56)",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "1985 Series",
        "Item": "Creepy",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Creepy Mail Away Exclusive",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "Mail-Order",
        "Item": "Creepy",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Water Walk (32)",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "1984 Series",
        "Item": "Water Walk",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Road Ranger (18)",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "1984 Series",
        "Item": "Road Ranger",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Path Finder (29)",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "1983 Series",
        "Item": "Path Finder",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Monsterous",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "Monsterous",
        "Item": "Monsterous Gift Set (Photo Box)",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Puzzler",
    ): {
        "Line": "Vintage Go Bots",
        "Wave": "Puzzler Go-Bots",
        "Item": "Puzzler Gift Set (Photo Box)",
    },
    (
        "Go Bots",
        "Vintage Go Bots",
        "Vintage",
        "Staks Transport (blue)",
    ): {
        "Line": "Super Go Bots",
        "Wave": "Super Go Bots",
        "Item": "Staks",
    },
    (
        "Go Bots",
        "Rock Lords",
        "Rock Lords",
        "Boulder",
    ): {
        "Line": "Rock Lords",
        "Wave": "Heroic Rock Lords",
        "Item": "Boulder (Corner Shoulder)",
    },
    (
        "Go Bots",
        "Rock Lords",
        "Wave 1 (Japanese Only)",
        "Rock Commander",
    ): {
        "Line": "Machine Robo",
        "Wave": "Wave 1 (Japanese Only)",
        "Item": "Rock Commander",
    },
    (
        "Go Bots",
        "Super Go Bots",
        "Super Go Bots",
        "Super Destroyer",
    ): {
        "Item": "Destroyer",
    },
    (
        "Go Bots",
        "Super Go Bots",
        "Super Go Bots",
        "Super Baron Von Joy",
    ): {
        "Item": "Baron von Joy",
    },
}

PROPERTY_TO_FRANCHISE = {
    "advanceddungeonsanddragons": ["Advanced Dungeons and Dragons"],
    "ateam": ["A-Team"],
    "bikermicefrommars": ["Biker Mice From Mars"],
    "blackstar": ["Blackstar"],
    "bravestarr": ["BraveStarr"],
    "buckyohare": ["Bucky O'Hare"],
    "captainplanet": ["Captain Planet"],
    "captainpower": ["Captain Power"],
    "carebears": ["Care Bears"],
    "centurions": ["Centurions"],
    "computerwarriors": ["Computer Warriors"],
    "copsncrooks": ["C.O.P.S. 'n' Crooks"],
    "crystar": ["Crystar"],
    "darkwingduck": ["Darkwing Duck"],
    "defendersoftheearth": ["Defenders of the Earth"],
    "foodfighters": ["Food Fighters"],
    "gijoe": ["G.I. Joe"],
    "gobots": ["GoBots"],
    "goldengirl": ["Golden Girl"],
    "goldlightan": ["Gold Lightan"],
    "greatestamericanhero": ["Greatest American Hero"],
    "ghostbusters": ["Ghostbusters"],
    "realghostbusters": ["Ghostbusters"],
    "inhumanoids": ["Inhumanoids"],
    "jem": ["Jem"],
    "karatekid": ["Karate Kid"],
    "mask": ["M.A.S.K."],
    "madballs": ["Madballs"],
    "mastersoftheuniverse": ["Masters of the Universe"],
    "megodolls": ["Mego Dolls"],
    "micromen": ["Microman"],
    "microman": ["Microman"],
    "micronauts": ["Micronauts"],
    "peeweesplayhouse": ["Pee-Wee's Playhouse"],
    "piratesofdarkwater": ["Pirates of Dark Water"],
    "policeacademy": ["Police Academy"],
    "powerlords": ["Power Lords"],
    "powerrangers": ["Power Rangers"],
    "pulsar": ["Pulsar"],
    "ringraiders": ["Ring Raiders"],
    "robotech": ["Robotech"],
    "sectaurs": ["Sectaurs"],
    "silverhawks": ["SilverHawks"],
    "starwars": ["Star Wars"],
    "starriors": ["Starriors"],
    "strawberryshortcake": ["Strawberry Shortcake"],
    "supernaturals": ["Super Naturals"],
    "swampthing": ["Swamp Thing"],
    "teenagemuntantninjaturtles": ["Teenage Mutant Ninja Turtles"],
    "teenagemutantninjaturtles": ["Teenage Mutant Ninja Turtles"],
    "thundercats": ["ThunderCats"],
    "transformers": ["Transformers"],
    "tron": ["Tron"],
    "visionaries": ["Visionaries"],
    "voltron": ["Voltron"],
    "xmen": ["X-Men"],
}

LINE_ALIASES = {
    "ateam3334inchline": ["A-Team 3 3/4\" Scale"],
    "ateam6inchline": ["A-Team 6\" Scale"],
    "advanceddungeonsanddragons": ["Advanced Dungeons and Dragons (LJN)"],
    "blackstar": ["Vintage Blackstar"],
    "bravestarr": ["Vintage BraveStarr"],
    "computerwarriors": ["Computer Warriors Basic Series", "Computer Warriors Vintage Figures"],
    "vintagecops": ["COPS 'N Crooks Vehicles and Driver Sets", "C.O.P.S. 'n' Crooks"],
    "vintagecarebears": [
        "Vintage Care Bears - Poseable Figures",
        "Vintage Care Bears - Poseable Care Bear Cousins",
        "Vintage Care Bears - Mini PVC Figures",
    ],
    "vintagegijoe": ["A Real American Hero"],
    "vintagebikermice": ["Vintage Biker Mice From Mars"],
    "classifed": ["Classified Series"],
    "g1transformers": ["Generation 1", "G1 Transformers"],
    "vintagerealghostbusters": ["Vintage The Real Ghostbusters", "Vintage Real Ghostbusters"],
    "vintagegobots": ["Go-Bots"],
    "silverhawks": ["Vintage SilverHawks", "Licensed Products"],
    "supernaturals": ["Forces of Good", "Forces of Evil", "Ghosts", "Accessories"],
    "vintagebeatlejuice": ["Beetlejuice"],
    "vintagebuckohare": ["Bucky O'Hare"],
    "vintagecops": ["C.O.P.S. 'n' Crooks"],
    "vintagejem": ["Vintage Jem"],
    "micromencommandseries": ["Microman Command Series", "Microman Lady Command"],
    "vintagepeewee": ["Pee-Wee's Playhouse"],
    "vintagepowerlords": ["Vintage Power Lords"],
    "vintagestarwars": [
        "Vintage Kenner Star Wars",
        "Vintage Kenner The Empire Strikes Back",
        "Vintage Kenner Return Of The Jedi",
        "Vintage Kenner The Power Of The Force",
        "Vintage Kenner Star Wars Vehicles and Playsets",
        "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
        "Vintage Kenner Return Of The Jedi Vehicles and Playsets",
        "Vintage Kenner The Power Of The Force Vehicles and Playsets",
    ],
}

ITEM_ALIASES = {
    "adammaitland": ["adammaitlan"],
    "badguyscobra": ["cobra"],
    "badguyspython": ["python"],
    "badguysrattler": ["rattler"],
    "badguysviper": ["viper"],
    "billandtedsjamsession": ["wildstallynsjamsession"],
    "beetlejuice12inch": ["beetlejuicespinninghead"],
    "creapycruiser": ["creepycruiser"],
    "explodingbeetlejuice": ["beetlejuiceexploding"],
    "ghengiskhan": ["genghiskhan"],
    "johnhannibalsmith": ["hannibal"],
    "3030roboticstallion": ["thirtythirtyroboticstallion"],
    "babyhugsbearwithsweetlickitylolipop": ["babyhugswithsweetlicketylollipop"],
    "babytugsbearwithbigdigitybucket": ["babytugswithbigdiggitybucket"],
    "braveheartlionwithtrustyshield": ["braveheartlionwithtrustyshield"],
    "brightheartraccoonwithclevercandle": ["brightheartraccoonwithclevercandle"],
    "bookwithindexxfigure": ["invasionofthevirusesevilrocketbase"],
    "cloudkeeperwithfluffycloudbroom": ["thecloudkeeperwithfluffycloudbroom"],
    "cozyheartpenguinmini": ["cozyheartpenguin"],
    "cozyheartpenguinwithniceskates": ["cozyheartpenguinwithniceskates"],
    "cobrahissrepro": ["cobrahiss"],
    "14stormshadowarcticmissionamazon": ["14stormshadowarcticmission"],
    "15destroprofitdirectorfan": ["15destroprofitdirector"],
    "drivercobrahiss": ["cobrahissdriver"],
    "iguanas": ["iguanus"],
    "laserlightklonecloudcat": ["laserlightklone", "klonecloudcat"],
    "laserlightmuton": ["laserlightmeuton"],
    "gentleheartlambwithpeekaboobell": ["gentleheartlambwithpeekaboobell"],
    "highwayintercepterwithroadblock": ["highwayinterceptorwithroadblock"],
    "jemjerica": ["jemjerrica"],
    "glitterandgoldjemjerica": ["glitterngoldjemjerrica"],
    "flashlightwithskannarfigure": ["beamerflashcraft"],
    "lenticularsheriffsbadge": ["sheriffsbadge"],
    "lotsaheartelephantwithmightytrunk": ["lotsaheartelephantwithmightytrunk"],
    "pencilsharpenerwithminusfigure": ["leadheadtechnojet"],
    "pepsicanwithgriddfigure": ["pepsicanhyperhoverjet"],
    "professorcoldheart": ["professorcoldheartwithfrozenmeaniemug", "professorcoldheart"],
    "doctorblight": ["drblight"],
    "shipwreckbeetlejuice": ["beetlejuiceshipwreck"],
    "slyther": ["slythor"],
    "tbobandscotttracker": ["tbobscotttrakker"],
    "razerback": ["razorback"],
    "zooli": ["zoolie"],
    "swateugenetackleberry": ["eugenetackleberryswat"],
    "flunghi": ["flunghicrazykarategearorangebelt", "flunghicrazykarategearyellowbelt"],
    "undercovercareymahoney": ["careymahoneyundercover"],
    "snackattackhouse": ["housesnackattack"],
    "skyglidenzed": ["zedskygliden"],
    "sydotthesupreme": ["sydot"],
    "bluegrassultrasonicsuit": ["bluegrasswithultrasonicsuit"],
    "vamppaw": ["vamppa"],
    "berbilbell": ["berbilbellecompanions"],
    "berbilburt": ["berbilbertcompanions"],
    "catslayer": ["catslair"],
    "topspinner": ["topspinnerberserkers"],
    "rambam": ["rambamberserkers"],
    "soccertrophywithnullfigure": ["soccermvpradarover"],
    "shishkebabbeetlejuice": ["beetlejuiceshishkebab"],
    "showtimebeetlejuice": ["beetlejuiceshowtime"],
    "soldiersofforture4pack": ["soldiersoffortune"],
    "spinheadbeetlejuice": ["beetlejuicespinhead"],
    "superbendablemodo": ["modopainted", "modounpainted"],
    "superbendablethrottle": ["throttlepainted", "throttleunpainted"],
    "superbendablevinnie": ["vinniepainted", "vinnieunpainted"],
    "templetonpeck": ["face"],
    "elkhorngooddwarffighter": ["elkhorn"],
    "monstarwithskyshadow": ["monstarwithskyshadow", "monstarwithskyshadow"],
    "quicksilverwithtallyhawk": ["quicksilverwithtallyhawk"],
    "swiftheartrabbitwithspeedyskateboard": ["swiftheartrabbitwithspeedyskateboard"],
    "vamprepro": ["vamp"],
    "warlockdragongreenandyellow": ["warlockdragongreenyellow"],
    "buzzsawwithshredator": ["buzzsawwithshredator"],
    "mumbojumbowithairshock": ["mumbojumbowithairshock"],
    "windhammerwithtuningfork": ["windhammerwithtuningfork"],
    "copperkidwithmayday": ["copperkiddwithmayday"],
}

STAR_WARS_WAVE_TO_PRODUCT_LINES = {
    "a": ["Vintage Kenner Star Wars"],
    "b": ["Vintage Kenner Star Wars", "Vintage Kenner Star Wars Vehicles and Playsets"],
    "c": ["Vintage Kenner The Empire Strikes Back"],
    "d": ["Vintage Kenner The Empire Strikes Back", "Vintage Kenner The Empire Strikes Back Vehicles and Playsets"],
    "e": ["Vintage Kenner The Empire Strikes Back"],
    "f": ["Vintage Kenner Return Of The Jedi"],
    "g": ["Vintage Kenner Return Of The Jedi"],
    "i": ["Vintage Kenner Return Of The Jedi"],
    "j": ["Vintage Kenner Return Of The Jedi"],
    "k": ["Vintage Kenner Return Of The Jedi"],
    "l": ["Vintage Kenner Return Of The Jedi"],
    "m": ["Vintage Kenner The Power Of The Force", "Vintage Kenner Return Of The Jedi"],
    "n": ["Vintage Kenner The Power Of The Force"],
}

REAL_GHOSTBUSTERS_WAVE_TO_CATALOG_WAVE = {
    "wave1": ["Series 1", "Accessories"],
    "wave2": ["Series 2"],
    "wave3": ["Fright Features", "Vehicles"],
    "wave4": ["Series 3"],
    "wave5": ["Monsters", "Screaming Heroes"],
    "wave6": ["Finger Pop Fiends", "Hand Puppets"],
    "wave7": ["Super Fright Features"],
    "wave8": ["Power Pack Heroes", "Gobblin Goblins"],
    "wave9": ["Slimed Heroes", "Vehicles"],
    "wave10": ["Ecto Glow Heroes"],
}

STAR_WARS_VINTAGE_FIGURE_PRODUCT_LINE_BY_WAVE = {
    "a": "Vintage Kenner Star Wars",
    "b": "Vintage Kenner Star Wars",
    "c": "Vintage Kenner The Empire Strikes Back",
    "d": "Vintage Kenner The Empire Strikes Back",
    "e": "Vintage Kenner The Empire Strikes Back",
    "f": "Vintage Kenner The Empire Strikes Back",
    "g": "Vintage Kenner The Empire Strikes Back",
    "h": "Vintage Kenner The Empire Strikes Back",
    "i": "Vintage Kenner The Empire Strikes Back",
    "j": "Vintage Kenner Return Of The Jedi",
    "k": "Vintage Kenner Return Of The Jedi",
    "l": "Vintage Kenner Return Of The Jedi",
    "m": "Vintage Kenner The Power Of The Force",
    "n": "Vintage Kenner The Power Of The Force",
}

STAR_WARS_VINTAGE_VEHICLE_PRODUCT_LINE_BY_WAVE = {
    "a": "Vintage Kenner Star Wars Vehicles and Playsets",
    "b": "Vintage Kenner Star Wars Vehicles and Playsets",
    "c": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "d": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "e": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "f": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "g": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "h": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "i": "Vintage Kenner The Empire Strikes Back Vehicles and Playsets",
    "j": "Vintage Kenner Return Of The Jedi Vehicles and Playsets",
    "k": "Vintage Kenner Return Of The Jedi Vehicles and Playsets",
    "l": "Vintage Kenner Return Of The Jedi Vehicles and Playsets",
    "m": "Vintage Kenner The Power Of The Force Vehicles and Playsets",
    "n": "Vintage Kenner The Power Of The Force Vehicles and Playsets",
}

STAR_WARS_SPECIAL_ITEM_ALIASES = {
    "princessleia": ["princessleiaorganastarwars"],
    "lukeskywalker": ["lukeskywalkerstarwars"],
    "hansolo": ["hansolostarwars"],
    "deathsquadcommander": ["deathsquadcommanderstarwars"],
    "darthvader": ["darthvaderstarwars"],
    "chewbacca": ["chewbaccastarwars"],
    "stormtrooper": ["stormtrooperstarwars"],
    "walrusman": ["pondababawalrusman"],
    "snaggletooth": ["snaggletoothstarwars"],
    "r5d4": ["r5d4starwars"],
    "powerdroid": ["gonkdroidpowerdroid"],
    "hammerhead": ["momawnadonhammerhead"],
    "4lom": ["4lomzuckuss"],
    "zuckuss": ["zuckuss4lom"],
    "lobot": ["lobotlandosaid"],
    "bossakbountyhunter": ["bosskbountyhunter"],
    "fx7": ["fx7medicaldroid"],
    "hansolocarbonitechamber": ["hansoloincarbonitechamber"],
    "leiaorganabespingown": ["princessleiaorganabespingown"],
    "leiahothoutfit": ["princessleiaorganahothoutfit"],
    "rebelsoldierhothbattlegear": ["hothrebeltrooperrebelsoldierhothbattlegear"],
    "imperialstormtrooperhothbattlegear": ["snowtrooperimperialstormtrooperhothbattlegear"],
    "twinpodcloudcarpilot": ["cloudcarpilottwinpod"],
    "imperialtiefighterpilot": ["tiefighterpilottheempirestrikesback"],
    "yoda": ["yodathejedimaster"],
    "21b": ["21btwoonebee"],
    "bespinsecurityguard": ["bespinsecurityguardtheempirestrikesback"],
    "atatcommander": ["atatcommandertheempirestrikesback"],
    "rebelcommander": ["rebelcommandertheempirestrikesback"],
    "imperialcommander": ["imperialcommandertheempirestrikesback"],
    "ugnaught": ["ugnaughttheempirestrikesback"],
    "ig88": ["ig88bountyhunter"],
    "weequay": ["weequayreturnofthejedi"],
    "generalmadine": ["generalmadinereturnofthejedi"],
    "gamorreanguard": ["gamorreanguardreturnofthejedi"],
    "chiefchirpa": ["chiefchirpareturnofthejedi"],
    "bikerscout": ["bikerscoutreturnofthejedi"],
    "squidhead": ["tesseksquidhead"],
    "rebelcommando": ["endorrebelsoldierreturnofthejedi"],
    "bwingpilot": ["bwingpilotreturnofthejedi"],
    "hansolotrenchcoat": ["hansolointrenchcoat"],
    "theemperor": ["palpatinedarthsidioustheemperor"],
    "pruneface": ["prunefaceorrimaarko"],
    "wicketwwarrick": ["wicketwicketwwarrick"],
    "lukeskywalkerjediknightoutfit": ["lukeskywalkerjediknightoutfit"],
    "princessleiaorganaboushhdisguise": ["princessleiaorganaboushhdisguise"],
    "imperialdignitary": ["imperialdignitaryreturnofthejedi"],
    "ev9d9": ["ev9d9returnofthejedi"],
    "awingpilot": ["awingpilotreturnofthejedi"],
    "anakinskywalker": ["anakinskywalkerreturnofthejedi"],
    "amanaman": ["amanamanreturnofthejedi"],
    "imperialgunner": ["deathstargunnerimperialgunner"],
    "barada": ["kithababarada"],
    "lukeskywalkerbattleponcho": ["lukeskywalkerinbattleponcho"],
    "paploo": ["paplooreturnofthejedi"],
    "lumat": ["lumatreturnofthejedi"],
    "warok": ["warokreturnofthejedi"],
    "romba": ["rombareturnofthejedi"],
    "yakface": ["yakfacesaeltmarae"],
    "artoodetoor2d2withsensorscope": ["r2d2withsensorscope"],
    "artoodetoor2d2withpopuplightsaber": ["r2d2withpopuplightsaber"],
    "hothiceplanet": ["hothiceplanetadventureset"],
    "rebelcommandcenteradventureset": ["rebelcommandcenter"],
    "xwingfighter": ["xwingfightervehiclemicrocollection", "xwingfighter"],
    "hothworldhothworld": ["hothworldmicrocollection"],
    "hothworldhothturretdefense": ["hothturretdefensemicrocollection"],
}

STAR_WARS_SPECIAL_PRODUCT_LINE_BY_ITEM = {
    "paploo": ("Vintage Kenner The Power Of The Force", "Power Of The Force assortment"),
    "lumat": ("Vintage Kenner The Power Of The Force", "Power Of The Force assortment"),
}


def normalize(text: str) -> str:
    text = (text or "").strip().lower()
    for pattern, replacement in COMMON_TEXT_REPLACEMENTS:
        text = re.sub(pattern, replacement, text)
    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def normalize_base_item_name(text: str) -> str:
    text = re.sub(r"\s*\([^)]*\)", "", text or "")
    return normalize(text)


def to_int(value: str) -> int:
    value = (value or "").strip()
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def truthy(value: str) -> bool:
    return (value or "").strip() in {"1", "true", "True", "yes", "Yes"}


def ensure_catalog_inventory_columns(connection: sqlite3.Connection) -> None:
    columns = {
        row[1] for row in connection.execute("PRAGMA table_info(catalog_items)")
    }
    required = {
        "owned": "INTEGER NOT NULL DEFAULT 0",
        "quantity_owned": "INTEGER NOT NULL DEFAULT 0",
        "complete_count": "INTEGER NOT NULL DEFAULT 0",
        "sealed_count": "INTEGER NOT NULL DEFAULT 0",
        "packaged_count": "INTEGER NOT NULL DEFAULT 0",
        "condition": "TEXT DEFAULT ''",
        "storage_location": "TEXT DEFAULT ''",
        "ownership_notes": "TEXT DEFAULT ''",
        "inventory_source_name": "TEXT DEFAULT ''",
        "inventory_updated_at": "TEXT DEFAULT ''",
    }
    for column_name, definition in required.items():
        if column_name not in columns:
            connection.execute(
                f"ALTER TABLE catalog_items ADD COLUMN {column_name} {definition}"
            )


def infer_catalog_condition(
    quantity_owned: int,
    complete_count: int,
    sealed_count: int,
    packaged_count: int,
) -> str:
    if quantity_owned <= 0:
        return ""
    if sealed_count >= quantity_owned:
        return "Sealed"
    if complete_count >= quantity_owned:
        return "Complete"
    if packaged_count >= quantity_owned:
        return "Packaged"
    return "Mixed"


def build_source_key(row: dict[str, str]) -> str:
    return " | ".join(
        [
            (row.get("Property") or "").strip(),
            (row.get("Line") or "").strip(),
            (row.get("Wave") or "").strip(),
            (row.get("Item") or "").strip(),
        ]
    )


def apply_source_row_corrections(row: dict[str, str]) -> dict[str, str]:
    corrected = dict(row)
    key = (
        (corrected.get("Property") or "").strip(),
        (corrected.get("Line") or "").strip(),
        (corrected.get("Wave") or "").strip(),
        (corrected.get("Item") or "").strip(),
    )
    for field, value in SOURCE_ROW_CORRECTIONS.get(key, {}).items():
        corrected[field] = value
    return corrected


def canonical_property_candidates(value: str) -> list[str]:
    value = (value or "").strip()
    candidates = [value]
    normalized = normalize(value)
    if normalized == "realghostbusters":
        candidates.append("The Real Ghostbusters")
    if normalized == "supernaturals":
        candidates.append("Super Naturals")
    if normalized == "gobots":
        candidates.append("Go-Bots")
    return list(dict.fromkeys(candidates))


def canonical_line_candidates(value: str) -> list[str]:
    value = (value or "").strip()
    normalized = normalize(value)
    candidates = [value]
    candidates.extend(LINE_ALIASES.get(normalized, []))
    if normalized.startswith("vintage"):
        candidates.append("")
    return list(dict.fromkeys(candidates))


def canonical_item_candidates(value: str) -> list[str]:
    value = (value or "").strip()
    candidates = [normalize(value)]
    if value.lower().startswith("driver-"):
        candidates.append(normalize(value[7:]))
    if ": " in value:
        suffix = value.split(": ", 1)[1]
        candidates.append(normalize(suffix))
    if " with " in value.lower():
        left = re.split(r"\s+with\s+", value, maxsplit=1, flags=re.I)[0]
        candidates.append(normalize(left))
    candidates.append(normalize(re.sub(r"\s*\(\d+\)\s*$", "", value)))
    if "see-threepio" in value.lower() or "c-3po" in value.lower():
        candidates.extend(["c3poseethreepio", "seethreepioc3po"])
    if "artoo-detoo" in value.lower() or "r2-d2" in value.lower():
        candidates.extend(["r2d2starwars", "artoodetoor2d2", "r2d2"])
    if "sand people" in value.lower():
        candidates.extend(["tuskenraidersandpeople"])
    if "ben (obi-wan) kenobi" in value.lower():
        candidates.extend(["obiwankenobiobiwanbenkenobi", "benobiwankenobi"])
    if "fright feature " in value.lower():
        candidates.append(normalize(value.replace("Fright Feature ", "Fright Features: ", 1)))
    if "screaming hero: " in value.lower():
        candidates.append(normalize(value.replace("Screaming Hero: ", "Screaming Heroes: ", 1)))
    if "ecto-glow hero: " in value.lower():
        candidates.append(normalize(value.replace("Ecto-Glow Hero: ", "Ecto Glow Heroes: ", 1)))
    if "monster: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.extend(
            [
                normalize(f"{base} Monster"),
                normalize(base),
            ]
        )
    if "haunted human: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.extend([normalize(f"{base} Ghost"), normalize(base)])
    if "gooper ghost: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.extend([normalize(base), normalize(f"{base} Gooper Ghost")])
    if "power pack heroes: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.append(normalize(base))
    if "slimed heroes: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.append(normalize(base))
    if "super fright features: " in value.lower():
        base = value.split(": ", 1)[1]
        candidates.append(normalize(base))
    candidates.extend(ITEM_ALIASES.get(normalize(value), []))
    return [candidate for candidate in dict.fromkeys(candidates) if candidate]


def star_wars_item_candidates(row: dict[str, str]) -> list[str]:
    item = (row.get("Item") or "").strip()
    normalized = normalize(item)
    candidates = [normalized]
    candidates.extend(STAR_WARS_SPECIAL_ITEM_ALIASES.get(normalized, []))
    if normalized and row.get("Line", "").strip() == "Vintage Star Wars":
        candidates.append(normalize(f"{item} Star Wars"))
        candidates.append(normalize(f"{item} Return Of The Jedi"))
        candidates.append(normalize(f"{item} The Empire Strikes Back"))
    return [candidate for candidate in dict.fromkeys(candidates) if candidate]


def candidate_franchises(property_value: str) -> list[str]:
    normalized = normalize(property_value)
    mapped = PROPERTY_TO_FRANCHISE.get(normalized, [])
    if mapped:
        return mapped
    raw = (property_value or "").strip()
    return [raw] if raw else []


def candidate_waves(row: dict[str, str]) -> list[str]:
    raw_wave = (row.get("Wave") or "").strip()
    normalized_property = normalize(row.get("Property", ""))
    normalized_line = normalize(row.get("Line", ""))
    normalized_wave = normalize(raw_wave)
    candidates = [raw_wave]

    if normalized_property == "advanceddungeonsanddragons":
        if normalized_wave == "mini":
            candidates.append("Miniature")
        if normalized_wave == "wave1":
            candidates.append("Basic Series")
    if normalized_property == "ateam" and normalized_wave == "wave1":
        candidates.append("1984")
    if normalized_property == "bikermicefrommars" and normalized_wave == "wave1":
        candidates.append("Super Bendables")
    if normalized_property == "blackstar":
        if normalized_wave == "wave1":
            candidates.append("Accessories")
        if normalized_wave in {"wave2", "wave3"}:
            candidates.append("Laser Lights")
    if normalized_property == "carebears":
        if normalized_wave == "minis":
            candidates.extend(["1985 Assortment", "1983 Assortment"])
    if normalized_property == "computerwarriors" and normalized_wave == "vintage":
        candidates.append("Wave 1")
    if normalized_property == "goldengirl":
        if normalized_wave == "goldengirl":
            candidates.append("Basic Series")
        if normalized_wave == "festivalspirit":
            candidates.append("Festival Spirit Outfits")
        if normalized_wave == "forestfantasy":
            candidates.append("Forest Fantasy Outfits")
        if normalized_wave == "eveningenchantment":
            candidates.append("Evening Enchantment Outfits")
    if normalized_property == "mask":
        if normalized_wave == "wave1":
            candidates.append("Series 1")
        if normalized_wave == "wave3":
            candidates.append("Racing Series")
    if normalized_property == "powerlords" and normalized_wave == "vintage":
        candidates.append("Basic Series")
    if normalized_property == "ringraiders" and normalized_wave == "wave1":
        candidates.append("Ring Raiders")
    if normalized_property == "silverhawks" and normalized_wave == "wave2":
        candidates.append("Basic Series")
    if normalized_property == "thundercats":
        if normalized_wave == "wave1":
            candidates.append("1")
        if normalized_wave == "wave2":
            candidates.append("2")
        if normalized_wave == "wave3":
            candidates.append("3")

    if normalized_line == "vintagestarwars" and normalized_wave in STAR_WARS_WAVE_TO_PRODUCT_LINES:
        candidates.extend(["Original carded figures", "Carded figures", "Power Of The Force assortment"])

    if normalized_property == "realghostbusters" and normalized_line == "vintagerealghostbusters":
        candidates.extend(REAL_GHOSTBUSTERS_WAVE_TO_CATALOG_WAVE.get(normalized_wave, []))

    return [candidate for candidate in dict.fromkeys(candidates)]


def candidate_line_wave_pairs(row: dict[str, str]) -> list[tuple[str, str]]:
    line_candidates = canonical_line_candidates(row.get("Line", ""))
    wave_candidates = candidate_waves(row)
    normalized_line = normalize(row.get("Line", ""))
    normalized_property = normalize(row.get("Property", ""))
    pairs: list[tuple[str, str]] = []

    if normalized_property == "starwars" and normalized_line == "vintagestarwars":
        wave_key = normalize(row.get("Wave", ""))
        category = normalize(row.get("Type", ""))
        item_key = normalize(row.get("Item", ""))
        if category in {"vehicle", "playset"}:
            product_line = STAR_WARS_VINTAGE_VEHICLE_PRODUCT_LINE_BY_WAVE.get(wave_key)
            if product_line:
                wave_label = "Vehicles and Playsets"
                if product_line == "Vintage Kenner The Power Of The Force Vehicles and Playsets":
                    wave_label = "1"
                return [(product_line, wave_label)]
        else:
            special_product_line = STAR_WARS_SPECIAL_PRODUCT_LINE_BY_ITEM.get(item_key)
            if special_product_line:
                return [special_product_line]
            product_line = STAR_WARS_VINTAGE_FIGURE_PRODUCT_LINE_BY_WAVE.get(wave_key)
            if product_line:
                if product_line == "Vintage Kenner Star Wars":
                    return [(product_line, "Original carded figures")]
                if product_line == "Vintage Kenner The Power Of The Force":
                    return [(product_line, "Power Of The Force assortment")]
                return [(product_line, "Carded figures")]

    if normalized_property == "starwars" and normalize(row.get("Line", "")) == "starwarsmicroseries":
        return [("Vintage Kenner Micro Collection", "Micro Collection")]

    for line_candidate in line_candidates:
        for wave_candidate in wave_candidates:
            pairs.append((line_candidate, wave_candidate))

    if normalized_line == "vintagestarwars":
        for product_line in STAR_WARS_WAVE_TO_PRODUCT_LINES.get(normalize(row.get("Wave", "")), []):
            pairs.append((product_line, "Original carded figures"))
            pairs.append((product_line, "Carded figures"))
            pairs.append((product_line, "Vehicles and Playsets"))
            pairs.append((product_line, "Power Of The Force assortment"))

    if normalized_property == "realghostbusters" and normalized_line == "vintagerealghostbusters":
        for wave_candidate in REAL_GHOSTBUSTERS_WAVE_TO_CATALOG_WAVE.get(normalize(row.get("Wave", "")), []):
            pairs.append(("Vintage The Real Ghostbusters", wave_candidate))
            pairs.append(("Vintage Real Ghostbusters", wave_candidate))

    if (
        normalized_property == "teenagemutantninjaturtles"
        and normalized_line == "mutantmayhem"
    ):
        for wave_candidate in wave_candidates:
            pairs.append(("Tales of the Teenage Mutant Ninja Turtles", wave_candidate))

    deduped: list[tuple[str, str]] = []
    seen = set()
    for pair in pairs:
        key = (pair[0], pair[1])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(pair)
    return deduped


def derive_condition(row: dict[str, str]) -> str:
    if truthy(row.get("Sealed", "")):
        return "Sealed"
    if truthy(row.get("Boxed", "")):
        return "Boxed"
    if truthy(row.get("Complete", "")):
        return "Complete"
    return "Unknown"


def build_series(row: dict[str, str]) -> str:
    property_name = (row.get("Property") or "").strip()
    product_line = (row.get("Line") or "").strip()
    if property_name and product_line:
        return f"{property_name} / {product_line}"
    return property_name or product_line


def build_notes(row: dict[str, str], match_strategy: str) -> str:
    parts = [
        "Imported from AppSheet inventory export.",
        f"Property: {(row.get('Property') or '').strip()}",
        f"Line: {(row.get('Line') or '').strip()}",
        f"Wave: {(row.get('Wave') or '').strip()}",
        f"OnHand: {to_int(row.get('OnHand', '0'))}",
        f"Complete: {(row.get('Complete') or '').strip() or '0'}",
        f"Sealed: {(row.get('Sealed') or '').strip() or '0'}",
        f"Boxed: {(row.get('Boxed') or '').strip() or '0'}",
        f"Match Strategy: {match_strategy}",
    ]
    return " ".join(parts)


def load_catalog_matchers(
    connection: sqlite3.Connection,
) -> tuple[
    dict[tuple[str, str, str, str], list[int]],
    dict[tuple[str, str, str, str], list[int]],
    dict[tuple[str, str, str], list[int]],
    dict[tuple[str, str, str], list[int]],
    dict[tuple[str, str], list[int]],
    dict[tuple[str, str], list[int]],
    dict[tuple[str, str], list[int]],
    dict[int, tuple[str, str, str, str, str]],
]:
    rows = connection.execute(
        """
        SELECT id, franchise, property_name, product_line, wave, item_name
        FROM catalog_items
        """
    ).fetchall()
    by_property_full: dict[tuple[str, str, str, str], list[int]] = {}
    by_franchise_full: dict[tuple[str, str, str, str], list[int]] = {}
    by_line_wave_item: dict[tuple[str, str, str], list[int]] = {}
    by_line_wave_base_item: dict[tuple[str, str, str], list[int]] = {}
    by_line_item: dict[tuple[str, str], list[int]] = {}
    by_property_item: dict[tuple[str, str], list[int]] = {}
    by_franchise_item: dict[tuple[str, str], list[int]] = {}
    row_signatures: dict[int, tuple[str, str, str, str, str]] = {}
    for row in rows:
        property_full = (
            normalize(row["property_name"]),
            normalize(row["product_line"]),
            normalize(row["wave"]),
            normalize(row["item_name"]),
        )
        franchise_full = (
            normalize(row["franchise"]),
            normalize(row["product_line"]),
            normalize(row["wave"]),
            normalize(row["item_name"]),
        )
        line_wave_item = (
            normalize(row["product_line"]),
            normalize(row["wave"]),
            normalize(row["item_name"]),
        )
        line_wave_base_item = (
            normalize(row["product_line"]),
            normalize(row["wave"]),
            normalize_base_item_name(row["item_name"]),
        )
        line_item = (
            normalize(row["product_line"]),
            normalize(row["item_name"]),
        )
        property_item = (
            normalize(row["property_name"]),
            normalize(row["item_name"]),
        )
        franchise_item = (
            normalize(row["franchise"]),
            normalize(row["item_name"]),
        )
        row_signatures[row["id"]] = (
            normalize(row["franchise"]),
            normalize(row["property_name"]),
            normalize(row["product_line"]),
            normalize(row["wave"]),
            normalize(row["item_name"]),
        )
        by_property_full.setdefault(property_full, []).append(row["id"])
        by_franchise_full.setdefault(franchise_full, []).append(row["id"])
        by_line_wave_item.setdefault(line_wave_item, []).append(row["id"])
        by_line_wave_base_item.setdefault(line_wave_base_item, []).append(row["id"])
        by_line_item.setdefault(line_item, []).append(row["id"])
        by_property_item.setdefault(property_item, []).append(row["id"])
        by_franchise_item.setdefault(franchise_item, []).append(row["id"])
    return (
        by_property_full,
        by_franchise_full,
        by_line_wave_item,
        by_line_wave_base_item,
        by_line_item,
        by_property_item,
        by_franchise_item,
        row_signatures,
    )


def resolve_match_ids(
    match_ids: list[int],
    row_signatures: dict[int, tuple[str, str, str, str, str]],
) -> int | None:
    if not match_ids:
        return None
    if len(match_ids) == 1:
        return match_ids[0]
    signatures = {row_signatures[match_id] for match_id in match_ids if match_id in row_signatures}
    if len(signatures) == 1:
        return match_ids[0]
    return None


def find_catalog_match(
    row: dict[str, str],
    by_property_full: dict[tuple[str, str, str, str], list[int]],
    by_franchise_full: dict[tuple[str, str, str, str], list[int]],
    by_line_wave_item: dict[tuple[str, str, str], list[int]],
    by_line_wave_base_item: dict[tuple[str, str, str], list[int]],
    by_line_item: dict[tuple[str, str], list[int]],
    by_property_item: dict[tuple[str, str], list[int]],
    by_franchise_item: dict[tuple[str, str], list[int]],
    row_signatures: dict[int, tuple[str, str, str, str, str]],
) -> tuple[int | None, str]:
    property_candidates = canonical_property_candidates(row.get("Property", ""))
    line_candidates = canonical_line_candidates(row.get("Line", ""))
    line_wave_pairs = candidate_line_wave_pairs(row)
    item_candidates = canonical_item_candidates(row.get("Item", ""))
    normalized_property = normalize(row.get("Property", ""))
    normalized_line = normalize(row.get("Line", ""))
    restrict_to_line_wave_match = normalized_property == "starwars" and normalized_line in {
        "vintagestarwars",
        "starwarsmicroseries",
    }
    if normalize(row.get("Property", "")) == "starwars":
        item_candidates.extend(star_wars_item_candidates(row))
        item_candidates = list(dict.fromkeys(item_candidates))
    franchise_candidates: list[str] = []
    for property_candidate in property_candidates:
        franchise_candidates.extend(candidate_franchises(property_candidate))
    franchise_candidates = list(dict.fromkeys(franchise_candidates))

    for property_candidate in property_candidates:
        for line_candidate, wave_candidate in line_wave_pairs:
            for item_candidate in item_candidates:
                key = (
                    normalize(property_candidate),
                    normalize(line_candidate),
                    normalize(wave_candidate),
                    item_candidate,
                )
                match_id = resolve_match_ids(by_property_full.get(key, []), row_signatures)
                if match_id is not None:
                    return match_id, "property+line+wave+item"

    for franchise_candidate in franchise_candidates:
        for line_candidate, wave_candidate in line_wave_pairs:
            for item_candidate in item_candidates:
                key = (
                    normalize(franchise_candidate),
                    normalize(line_candidate),
                    normalize(wave_candidate),
                    item_candidate,
                )
                match_id = resolve_match_ids(by_franchise_full.get(key, []), row_signatures)
                if match_id is not None:
                    return match_id, "franchise+line+wave+item"

    for line_candidate, wave_candidate in line_wave_pairs:
        for item_candidate in item_candidates:
            key = (normalize(line_candidate), normalize(wave_candidate), item_candidate)
            match_id = resolve_match_ids(by_line_wave_item.get(key, []), row_signatures)
            if match_id is not None:
                return match_id, "line+wave+item"

    for line_candidate, wave_candidate in line_wave_pairs:
        for item_candidate in item_candidates:
            key = (
                normalize(line_candidate),
                normalize(wave_candidate),
                normalize_base_item_name(item_candidate),
            )
            match_id = resolve_match_ids(by_line_wave_base_item.get(key, []), row_signatures)
            if match_id is not None:
                return match_id, "line+wave+base-item"

    if restrict_to_line_wave_match:
        return None, "unmatched"

    for line_candidate in line_candidates:
        if not line_candidate:
            continue
        for item_candidate in item_candidates:
            key = (normalize(line_candidate), item_candidate)
            match_id = resolve_match_ids(by_line_item.get(key, []), row_signatures)
            if match_id is not None:
                return match_id, "line+item"

    for property_candidate in property_candidates:
        for item_candidate in item_candidates:
            key = (normalize(property_candidate), item_candidate)
            match_id = resolve_match_ids(by_property_item.get(key, []), row_signatures)
            if match_id is not None:
                return match_id, "property+item"

    for franchise_candidate in franchise_candidates:
        for item_candidate in item_candidates:
            key = (normalize(franchise_candidate), item_candidate)
            match_id = resolve_match_ids(by_franchise_item.get(key, []), row_signatures)
            if match_id is not None:
                return match_id, "franchise+item"

    return None, "unmatched"


def main() -> int:
    csv_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_CSV_PATH
    if not csv_path.exists():
        print(f"CSV not found: {csv_path}")
        return 1

    with sqlite3.connect(DB_PATH) as connection:
        connection.row_factory = sqlite3.Row
        ensure_catalog_inventory_columns(connection)
        (
            by_property_full,
            by_franchise_full,
            by_line_wave_item,
            by_line_wave_base_item,
            by_line_item,
            by_property_item,
            by_franchise_item,
            row_signatures,
        ) = load_catalog_matchers(connection)

        with csv_path.open(newline="", encoding="utf-8-sig") as handle:
            reader = csv.DictReader(handle)
            rows = list(reader)

        connection.execute("DELETE FROM items WHERE source_name = ?", (SOURCE_NAME,))
        connection.execute(
            """
            UPDATE catalog_items
            SET owned = 0,
                quantity_owned = 0,
                complete_count = 0,
                sealed_count = 0,
                packaged_count = 0,
                condition = '',
                storage_location = '',
                ownership_notes = '',
                inventory_source_name = '',
                inventory_updated_at = ''
            WHERE inventory_source_name = ?
            """,
            (SOURCE_NAME,),
        )

        inserted = 0
        matched = 0
        unmatched_rows: list[dict[str, str]] = []
        matched_inventory: dict[int, dict[str, object]] = {}

        for row in rows:
            row = apply_source_row_corrections(row)
            quantity = to_int(row.get("OnHand", "0"))
            if quantity <= 0:
                continue

            catalog_item_id, match_strategy = find_catalog_match(
                row,
                by_property_full,
                by_franchise_full,
                by_line_wave_item,
                by_line_wave_base_item,
                by_line_item,
                by_property_item,
                by_franchise_item,
                row_signatures,
            )
            if catalog_item_id is not None:
                matched += 1
                summary = matched_inventory.setdefault(
                    catalog_item_id,
                    {
                        "quantity_owned": 0,
                        "complete_count": 0,
                        "sealed_count": 0,
                        "packaged_count": 0,
                        "ownership_notes": [],
                    },
                )
                summary["quantity_owned"] = int(summary["quantity_owned"]) + quantity
                if truthy(row.get("Complete", "")):
                    summary["complete_count"] = int(summary["complete_count"]) + quantity
                if truthy(row.get("Sealed", "")):
                    summary["sealed_count"] = int(summary["sealed_count"]) + quantity
                if truthy(row.get("Sealed", "")) or truthy(row.get("Boxed", "")):
                    summary["packaged_count"] = int(summary["packaged_count"]) + quantity
                summary["ownership_notes"].append(build_notes(row, match_strategy))
            else:
                unmatched_rows.append(
                    {
                        "Item": (row.get("Item") or "").strip(),
                        "Type": (row.get("Type") or "").strip(),
                        "Property": (row.get("Property") or "").strip(),
                        "Line": (row.get("Line") or "").strip(),
                        "Wave": (row.get("Wave") or "").strip(),
                        "OnHand": str(quantity),
                    }
                )

            connection.execute(
                """
                INSERT INTO items (
                    name,
                    series,
                    category,
                    item_number,
                    owned,
                    quantity,
                    condition,
                    storage_location,
                    source_name,
                    source_key,
                    catalog_item_id,
                    notes,
                    updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                """,
                (
                    (row.get("Item") or "").strip(),
                    build_series(row),
                    (row.get("Type") or "").strip(),
                    (row.get("Wave") or "").strip(),
                    1,
                    quantity,
                    derive_condition(row),
                    "",
                    SOURCE_NAME,
                    build_source_key(row),
                    catalog_item_id,
                    build_notes(row, match_strategy),
                ),
            )
            inserted += 1

        for catalog_item_id, summary in matched_inventory.items():
            quantity_owned = int(summary["quantity_owned"])
            complete_count = int(summary["complete_count"])
            sealed_count = int(summary["sealed_count"])
            packaged_count = int(summary["packaged_count"])
            ownership_notes = " | ".join(
                note
                for note in summary["ownership_notes"]
                if isinstance(note, str) and note.strip()
            )
            connection.execute(
                """
                UPDATE catalog_items
                SET owned = ?,
                    quantity_owned = ?,
                    complete_count = ?,
                    sealed_count = ?,
                    packaged_count = ?,
                    condition = ?,
                    ownership_notes = ?,
                    inventory_source_name = ?,
                    inventory_updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (
                    1 if quantity_owned > 0 else 0,
                    quantity_owned,
                    complete_count,
                    sealed_count,
                    packaged_count,
                    infer_catalog_condition(
                        quantity_owned,
                        complete_count,
                        sealed_count,
                        packaged_count,
                    ),
                    ownership_notes,
                    SOURCE_NAME,
                    catalog_item_id,
                ),
            )

        with UNMATCHED_REPORT_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=["Item", "Type", "Property", "Line", "Wave", "OnHand"],
            )
            writer.writeheader()
            writer.writerows(unmatched_rows)

        connection.commit()

    print(f"Imported {inserted} owned AppSheet rows into items.")
    print(f"Matched to catalog_items: {matched}")
    print(f"Unmatched report: {UNMATCHED_REPORT_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
