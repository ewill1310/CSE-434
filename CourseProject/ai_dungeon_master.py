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
