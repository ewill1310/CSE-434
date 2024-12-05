import random
import json
import os
from dotenv import load_dotenv
import openai

# Load environment variables from .env file and get the OpenAi API key
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

# Constants for game mechanics
STARTING_HP = 50
STARTING_XP = 0
XP_FOR_LEVEL_UP = 50
ITEMS = {"key": "A rusty key that opens a door.", "potion": "A healing potion that restores 10 HP."}
NPCS = ["Goblin", "Orc", "Troll", "Bandit", "Human", "Elf", "Dwarf", "Demon"]
DIRECTIONS = ['north', 'south', 'east', 'west']

# Utility Functions for game interactions

# Function to simulate a dice roll, for a given dice size (i.e. d6, d10)
def roll_dice(sides):
    return random.randint(1, sides)

# When starting the dungeon it picks a random title from the five provided
def generate_dungeon_name():
    return f"Dungeon of {random.choice(['Darkness', 'Despair', 'Abyss', 'Fate', 'Eternity'])}"

# Uses OpenAI API to genereate descriptions of rooms, limiting tokens to 100, to both save money and prevent giant descriptions
def get_location_description(location_name):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=f"Describe a fantasy dungeon room called {location_name}",
        max_tokens=100
    )
    return response.choices[0].text.strip()

# Each time a room is entered, generate new connected rooms, with up to 1-3 new rooms
def generate_new_rooms(current_room, existing_rooms):
    new_rooms = []
    directions = random.sample(DIRECTIONS, random.randint(1, 3))
    for direction in directions:
        new_room_name = f"{current_room}_{direction}"
        if new_room_name not in existing_rooms:
            existing_rooms.add(new_room_name)
            new_rooms.append(new_room_name)
    return new_rooms

# Game State
class GameState:
    def __init__(self):
        self.player_hp = STARTING_HP
        self.player_xp = STARTING_XP
        self.level = 1
        self.inventory = []
        self.dungeon_name = generate_dungeon_name()
        self.map = {"Entrance": []}
        self.visited_rooms = set()
        self.current_room = "Entrance"
        self.npcs = {"Entrance": random.choice(NPCS)}
        self.items = {"Entrance": random.sample(ITEMS.keys(), k=1)}
        self.chests = {}
        self.keys = {}
        self.spawn_keys_and_chests()
        self.spawn_npcs()

    # Spawn a key and chest in random rooms, ensuring equal numbers
    def spawn_keys_and_chests(self):
        rooms = list(self.map.keys())
        num_keys = random.randint(1, len(rooms) // 2)
        spawned_keys = random.sample(rooms, num_keys)
        spawned_chests = random.sample(rooms, num_keys)

        for i in range(num_keys):
            key_room = spawned_keys[i]
            chest_room = spawned_chests[i]
            while chest_room == key_room:
                chest_room = random.choice(rooms)
            self.keys[key_room] = "key"
            self.chests[chest_room] = "chest"

    # Randomly spawns NPCs in random rooms
    def spawn_npcs(self):
        for room in self.map.keys():
            if random.random() < 0.5:
                self.npcs[room] = random.choice(NPCS)
                self.items[room] = random.sample(ITEMS.keys(), k=1)

    # Save game state to a file
    def save_state(self):
        state = {
            "player_hp": self.player_hp,
            "player_xp": self.player_xp,
            "level": self.level,
            "inventory": self.inventory,
            "dungeon_name": self.dungeon_name,
            "map": self.map,
            "visited_rooms": list(self.visited_rooms),
            "current_room": self.current_room,
            "npcs": self.npcs,
            "items": self.items,
            "chests": self.chests,
            "keys": self.keys
        }
        with open("game_state.json", "w") as f:
            json.dump(state, f)

    # Load game state from a file
    def load_state(self):
        if os.path.exists("game_state.json"):
            with open("game_state.json", "r") as f:
                state = json.load(f)
                self.player_hp = state["player_hp"]
                self.player_xp = state["player_xp"]
                self.level = state["level"]
                self.inventory = state["inventory"]
                self.dungeon_name = state["dungeon_name"]
                self.map = state["map"]
                self.visited_rooms = set(state["visited_rooms"])
                self.current_room = state["current_room"]
                self.npcs = state["npcs"]
                self.items = state["items"]
                self.chests = state["chests"]
                self.keys = state["keys"]
        else:
            self.save_state()

    # Check if the player has enough XP to level up
    def check_level_up(self):
        if self.player_xp >= self.level * XP_FOR_LEVEL_UP:
            self.level += 1
            self.player_hp += 10
            print(f"Congratulations! You leveled up to level {self.level}!")
            print(f"Your HP is now {self.player_hp}.")
            return True
        return False

