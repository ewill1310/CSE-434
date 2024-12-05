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
NPCS = ["Goblin", "Orc", "Troll"]
DIRECTIONS = ['north', 'south', 'east', 'west']