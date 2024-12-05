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
MAX_HP = 50
STARTING_XP = 0
XP_FOR_LEVEL_UP = 50
ITEMS = {"key": "A rusty key that opens a door.", "potion": "A healing potion that restores 20 HP.","trophy": "A token that shows of a bosses defeat"}
NPCS = ["Goblin", "Orc", "Troll", "Bandit", "Human", "Elf", "Dwarf", "Demon"]
DIRECTIONS = ['north', 'south', 'east', 'west']
BOSS_NAME = ["Dragon", "Lich King", "Goblin Queen", "High Elf", "Dwarf God", "Omega Troll", "Basalisk"]


# Utility Functions for game interactions

# Function to simulate a dice roll, for a given dice size (i.e. d6, d10)
def roll_dice(sides):
    return random.randint(1, sides)

# When starting the dungeon it picks a random title from the five provided
def generate_dungeon_name():
    return f"Dungeon of {random.choice(['Darkness', 'Despair', 'Abyss', 'Fate', 'Eternity'])}"

# Uses OpenAI API to genereate descriptions of rooms, limiting tokens to 100, to both save money and prevent giant descriptions
def get_location_description(location_name, game_state):
    prompt = f"You are a dungeon master describing a fantasy dungeon room. The room is named '{location_name}'. "
    prompt += "Include details such as monsters, items, and the atmosphere of the room. "
    
    # Adding specific details for the boss room or any room with items or NPCs
    if location_name == game_state.boss_room:
        prompt += f"The room is the {game_state.boss}'s lair, dark and foreboding. The air feels still and the room is ominous. The only enemy here is the boss."
    elif location_name in game_state.npcs:
        prompt += f"There is a {game_state.npcs[location_name]} lurking in this room."
    if location_name in game_state.items:
        prompt += f"You spot something valuable: a {game_state.items[location_name]}."

    try:
        response = openai.Completion.create(
            engine="text-davinci-003",
            prompt=prompt,
            max_tokens=100
        )
        description = response.choices[0].text.strip()
        return description
    except Exception as e:
        print(f"Error generating location description: {e}")
        return "The room is quiet and uneventful."

# Each time a room is entered, generate new connected rooms, with up to 1-3 new rooms
def generate_new_rooms(current_room, existing_rooms, game_state):
    new_rooms = []
    directions = random.sample(DIRECTIONS, random.randint(1, 3))
    for direction in directions:
        new_room_name = f"{current_room}_{direction}"
        if new_room_name not in existing_rooms:
            existing_rooms.add(new_room_name)
            new_rooms.append(new_room_name)
            
            # 1% chance the new room is the boss room
            if random.random() < 0.01:
                game_state.boss_room = new_room_name
                game_state.boss = random.choice(BOSS_NAME)
            
            # 50% chance of an NPC being in the room
            if random.random() < 0.5:
                game_state.npcs[new_room_name] = random.choice(NPCS)
            
            # 50% chance of a random item
            game_state.items[new_room_name] = game_state.items.get(new_room_name, [])
            if random.random() < 0.5:
                game_state.items[new_room_name].append(random.choice([key for key in ITEMS if key != "trophy"]))
            
    return new_rooms



# Game State
class GameState:
    # Setting up initial game state
    def __init__(self):
        self.player_hp = STARTING_HP
        self.player_xp = STARTING_XP
        self.max_hp = MAX_HP
        self.level = 1
        self.inventory = []
        self.dungeon_name = generate_dungeon_name()
        self.map = {"Entrance": []}
        self.visited_rooms = set()
        self.current_room = "Entrance"
        self.npcs = {"Entrance": random.choice(NPCS)}
        self.items = {"Entrance": random.sample([key for key in ITEMS if key != "trophy"], k=1)}
        self.chests = {}
        self.keys = {}
        self.boss = random.choice(BOSS_NAME)
        self.boss_room = ["boss_room"]

    # Save game state to a file
    def save_state(self):
        state = {
            "player_hp": self.player_hp,
            "player_xp": self.player_xp,
            "max_hp" : self.max_hp,
            "level": self.level,
            "inventory": self.inventory,
            "dungeon_name": self.dungeon_name,
            "map": self.map,
            "visited_rooms": list(self.visited_rooms),
            "current_room": self.current_room,
            "npcs": self.npcs,
            "items": self.items,
            "chests": self.chests,
            "keys": self.keys,
            "boss": self.boss,
            "boss_room": self.boss_room
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
                MAX_HP = state["max_hp"]
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
                self.boss = state["boss"]
                self.boss_room = state["boss_room"]
        else:
            self.save_state()

    # Check if the player has enough XP to level up
    def check_level_up(self):
        if self.player_xp >= self.level * XP_FOR_LEVEL_UP:
            self.level += 1
            self.player_hp += 10
            MAX_HP == MAX_HP + 10
            print(f"Congratulations! You leveled up to level {self.level}!")
            print(f"Your HP is now {self.player_hp}.")
            return True
        return False

    # Function to check your inventory
    def check_inventory(self):
        if not self.inventory:
            print("Your inventory is empty.")
        else:
            print("Inventory:", ', '.join(self.inventory))

    # Check if the player has a potion in their inventory then use it
    def use_potion(self):
        if "potion" in self.inventory:
            self.player_hp += 20
            if self.player_hp > MAX_HP:
                self.player_hp = MAX_HP
            print(f"You used a potion! Your HP is now {self.player_hp}.")
            self.inventory.remove("potion")
        else:
            print("You don't have any potions in your inventory!")

    # Enters NPC combat, and if player wins, theey loot the body
    def encounter_npc(self):
        npc = self.npcs[self.current_room]
        print(f"A {npc} appears!")

        action = input("Do you want to fight, potion or run? (fight/potion/run): ").strip().lower()
        if action == "fight":
            npc_hp = 30
            player_attack = roll_dice(6) + 5
            npc_attack = roll_dice(6) + 3
            print(f"Combat begins! You roll a {player_attack}, and the {npc} rolls a {npc_attack}.")
            while self.player_hp > 0 and npc_hp > 0:
                npc_hp -= player_attack
                print(f"You hit the {npc}! {npc_hp} HP left.")
                if npc_hp <= 0:
                    print(f"You defeated the {npc}!")
                    self.player_xp += 10
                    self.check_level_up()
                    loot = random.choice(["key", "potion"])
                    print(f"The {npc} drops a {loot}!")
                    self.inventory.append(loot)
                    break
                self.player_hp -= npc_attack
                print(f"The {npc} hits you! {self.player_hp} HP left.")
                if self.player_hp <= 0:
                    print("You have been defeated.")
                    break
        elif action == "potion":
            self.use_potion(self)
        elif action == "run":
            print("You chose to run. The encounter ends.")


    # Enters Boss combat
    def encounter_boss(self):
        boss = self.boss[self.current_room]
        print(f"A {boss} appears!")

        action = input("Do you want to fight, potion or run? (fight/potion/run): ").strip().lower()
        if action == "fight":
            boss_hp = 200
            player_attack = roll_dice(6) + 5
            boss_attack = roll_dice(6) + 5
            print(f"Combat begins! You roll a {player_attack}, and the {boss} rolls a {boss_attack}.")
            while self.player_hp > 0 and boss_hp > 0:
                boss_hp -= player_attack
                print(f"You hit the {boss}! {boss_hp} HP left.")
                if boss_hp <= 0:
                    print(f"You defeated the {boss}!")
                    self.player_xp += 10
                    self.check_level_up()
                    loot = random.choice(["trophy"])
                    print(f"The {boss} drops a {loot}!")
                    self.inventory.append(loot)
                    break
                self.player_hp -= boss_attack
                print(f"The {boss} hits you! {self.player_hp} HP left.")
                if self.player_hp <= 0:
                    print("You have been defeated.")
                    break
        elif action == "potion":
            self.use_potion(self)
        elif action == "run":
            print("You chose to run. The encounter ends.")

        # Show available directions based on current room's exits, generates new rooms after moving, prints out new rooms description
        def move_player(self):
            print("Where do you want to go?")
            if self.current_room not in self.map:
                print("No available directions.")
                return

            available_rooms = self.map[self.current_room]
            if not available_rooms:
                print("This room has no exits. It's a dead end!")
                return

            print("Available exits:", ', '.join(available_rooms))
            direction = input("Enter a direction: ").strip().lower()

            if direction not in available_rooms:
                print("You can't go that way.")
                return

            # Move to the new room
            self.current_room = direction
            if self.current_room not in self.visited_rooms:
                print(f"You move to {self.current_room}.")
                self.visited_rooms.add(self.current_room)
                new_rooms = generate_new_rooms(self.current_room, self.map)
                self.map[self.current_room].extend(new_rooms)
            else:
                print(f"You are already familiar with {self.current_room}.")
            
            # Print the room description
            description = get_location_description(self.current_room, self)
            print(description)



# Main function to run the game
def main():
    print("Welcome to the AI Dungeon Master!")
    game_state = GameState()
    game_state.load_state()

    while game_state.player_hp > 0:
        print(f"\nCurrent Room: {game_state.current_room}")
        print(f"\n{get_location_description(game_state.current_room, game_state)}")
        print(f"HP: {game_state.player_hp}, XP: {game_state.player_xp}")
        print(f"Inventory: {', '.join(game_state.inventory) if game_state.inventory else 'empty'}")
        
        action = input("What do you want to do? (move/encounter/challenge boss/check inventory/save/quit): ").strip().lower()
        
        if action == "move":
            game_state.move_player()
        elif action == "encounter":
            game_state.encounter_npc()
        elif (action == "challenge boss" and game_state.current_room == game_state.boss_room):
            game_state.encounter_boss()
        elif action == "check inventory":
            game_state.check_inventory()
        elif action == "save":
            game_state.save_state()
            print("Game saved.")
        elif action == "quit":
            print("Exiting the game.")
            break
        else:
            print("Invalid action. Please try again.")

    print("Game over!")

if __name__ == "__main__":
    main()
