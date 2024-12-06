import os
import json
from dotenv import load_dotenv
import random
import openai
from openai import OpenAI

load_dotenv()

# Load the API Key
openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openai.api_key,
)

# Creates the room class that will be used when making the dungeon map
class Room:
    # Constructor
    def __init__(self, room_id, room_name, npc=None, boss=False, connections=None):
        self.room_id = room_id
        self.room_name = room_name
        self.npc = npc
        self.boss = boss
        self.connections = connections or {}
        self.enemy_defeated = False  

    # Uses openai's gpt 3.5 model to create descriptions about each room and its atmosphere
    def generate_random_room_description(self):
        prompt = f"Generate a description for a D&D room called {self.room_name}. It could be a normal room or a boss room. It has 4 paths leading to different rooms."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        description = response.choices[0].message.content.strip()
        return description

    # This method is used to attach the generated descriptions to rooms and update them accordingly
    def describe(self):
        room_description = f"Room {self.room_id} - {self.room_name}: {self.generate_random_room_description()}\n"
        if self.npc and not self.enemy_defeated:
            room_description += f"There is a {self.npc} here.\n"
        elif self.enemy_defeated:
            room_description += "The room is empty. You've defeated the enemy!\n"
        if self.boss and not self.enemy_defeated:
            room_description += "There is a terrifying boss here!\n"
        return room_description

    # This method is used to tag a room, saying that the enemies in here have been defeated
    def defeat_enemy(self):
        self.enemy_defeated = True

    # Turned the room into a dictonary for status storage
    def to_dict(self):
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "npc": self.npc,
            "boss": self.boss,
            "connections": self.connections,
            "enemy_defeated": self.enemy_defeated
        }

    # Turns a given dictionary back into a room for loading status
    @staticmethod
    def from_dict(data):
        room = Room(
            room_id=data["room_id"],
            room_name=data["room_name"],
            npc=data["npc"],
            boss=data["boss"],
            connections=data["connections"]
        )
        room.enemy_defeated = data["enemy_defeated"]
        return room

# This class is used to initialize the player and set up what they can do
class Player:
    # Constructor
    def __init__(self, name):
        self.name = name
        self.inventory = ["health_potion"]
        self.health = 100
        self.room = None

    # Define the rules of how an attack works on an enemy
    def attack(self, enemy_health):
        roll = random.randint(1, 20)
        damage = random.randint(5, 15)
        if roll > 7:
            enemy_health -= damage
            return f"Attack successful! You dealt {damage} damage.", enemy_health
        else:
            return "Attack missed!", enemy_health

    # Uses a potion from the inventory and heals 20 damage
    def heal(self):
        if "health_potion" in self.inventory:
            self.health += 20
            self.inventory.remove("health_potion")
            return "You healed yourself with a potion."
        else:
            return "You have no potions left."

    # Flee from combat
    def flee(self):
        return "You fled the battle."
    
    # Moves the player to an adjacent room, either north, south, east, or west
    def move(self, direction, rooms):
        if direction in self.room.connections:
            new_room_id = self.room.connections[direction]
            new_room = rooms.get(new_room_id)
            return new_room
        else:
            print("You can't move in that direction.")
            return None

    # Turns the player and its info into a dictionary for status storage
    def to_dict(self):
        return {
            "name": self.name,
            "inventory": self.inventory,
            "health": self.health,
            "room": self.room.room_id if self.room else None
        }

    # Turns the dictionary into the player information for status loading
    @staticmethod
    def from_dict(data, rooms):
        player = Player(data["name"])
        player.inventory = data["inventory"]
        player.health = data["health"]
        player.room = rooms.get(data["room"]) if data["room"] is not None else None
        return player

# Creates an enemy or a boss in a room
def generate_npc_or_boss():
    npc_chance = random.randint(1, 10)
    if npc_chance <= 7:
        return "Goblin"
    elif npc_chance == 8:
        return "Orc"
    elif npc_chance == 9:
        return "Troll"
    elif npc_chance == 10:
        return "Dragon"
    return None

# Creates the dungeon which holds a series of rooms
def create_dungeon():
    rooms = {}
    room_count = 0
    start_room = Room(room_count, "Start Room", npc=generate_npc_or_boss(), boss=random.choice([True, False]))
    rooms[room_count] = start_room
    room_count += 1
    current_room = start_room

    for direction in ["north", "south", "east", "west"]:
        room_name = f"Room {room_count}"
        npc = generate_npc_or_boss()
        boss = random.choice([True, False])
        room = Room(room_count, room_name, npc=npc, boss=boss)
        start_room.connections[direction] = room.room_id
        room.connections[get_opposite_direction(direction)] = start_room.room_id
        rooms[room_count] = room
        room_count += 1

    return rooms, start_room

# To be used when attaching rooms together so they lead to eachother
def get_opposite_direction(direction):
    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposite_directions[direction]

# Saves the current state into a JSON file
def save_state(player, rooms, filename="game_state.json"):
    game_state = {
        "player": player.to_dict(),
        "rooms": {room_id: room.to_dict() for room_id, room in rooms.items()}
    }

    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)

    print("Game state saved!")

# Loads the provided JSON file so a saves state can be used
def load_state(filename="game_state.json"):
    if not os.path.exists(filename):
        print("No saved state found!")
        return None, None

    with open(filename, 'r') as f:
        game_state = json.load(f)
    rooms = {room_data["room_id"]: Room.from_dict(room_data) for room_data in game_state["rooms"].values()}
    player_data = game_state["player"]
    player = Player.from_dict(player_data, rooms)
    player.room = rooms.get(player.room.room_id)
    print("Game state loaded!")
    return player, rooms

# Runs the game by looping through a series of available player actions
def game_loop():
    # Sets a player name to make player feel more emmersed
    player_name = input("Enter your character's name: ")
    player = Player(player_name)
    rooms, start_room = create_dungeon()

    player.room = start_room
    print(player.room.describe())

    visited_rooms = set()
    visited_rooms.add(player.room.room_id)

    previous_room = None

    while True:
        if player.health <= 0:
            print("Game Over! You've been defeated.")
            break
        # List of player options 
        print("\nChoose an action: (Type the number)")
        print("1. Move (north / south / east / west)")
        print("2. Enter Combat")
        print("3. Heal")
        print("4. Check Inventory")
        print("5. Save Game")
        print("6. Load Game")
        print("7. Quit")

        action = input("Action: ")
        # Handles player movement
        if action == "1":
            direction = input("Which direction would you like to move? (north / south / east / west): ").lower()
            if direction in player.room.connections:
                new_room = player.move(direction, rooms)
                if new_room:
                    previous_room = player.room
                    player.room = new_room
                    visited_rooms.add(player.room.room_id)
                    for direction in ["north", "south", "east", "west"]:
                        if direction not in player.room.connections:
                            room_name = f"Room {len(rooms)+1}"
                            npc = generate_npc_or_boss()
                            boss = random.choice([True, False])
                            room = Room(len(rooms), room_name, npc=npc, boss=boss)
                            player.room.connections[direction] = room.room_id
                            room.connections[get_opposite_direction(direction)] = player.room.room_id
                            rooms[len(rooms)] = room

                    if previous_room:
                        previous_room.connections[get_opposite_direction(direction)] = player.room.room_id
                        player.room.connections[get_opposite_direction(direction)] = previous_room.room_id

                    print(player.room.describe())

                else:
                    print("You can't move in that direction.")
            else:
                print("You can't move in that direction.")
        # Handles combat actions
        elif action == "2":
            enemy_health = 50
            while enemy_health > 0 and player.health > 0:
                print("Choose your combat action:")
                print("1. Attack")
                print("2. Heal")
                print("3. Flee")

                combat_action = input("Action: ")
                # attacking
                if combat_action == "1":
                    result, enemy_health = player.attack(enemy_health)
                    print(result)
                    print(f"Enemy Health: {enemy_health}")
                # healing
                elif combat_action == "2":
                    print(player.heal())
                # trying to flee
                elif combat_action == "3":
                    flee_chance = random.randint(1,20)
                    if flee_chance > 13:
                        print(player.flee())
                        break
                    else :
                        print("Could Not Escape")
                else:
                    print("Invalid action.")

                # For if an enemy dies
                if enemy_health <= 0:
                    print("You've defeated the enemy!")
                    player.room.defeat_enemy()
                    player.inventory.append("health_potion")
                    print("Enemy dropped a health potion!\n")
                    print(player.room.describe())
                    break

                # Enemy attacks back
                enemy_attack = random.randint(1, 15)
                if (enemy_attack >= 10):
                    player.health -= enemy_attack
                    print(f"The enemy attacks you for {enemy_attack} damage. Your health is now {player.health}.")
                else:
                    print(f"The enemy's attack missed!")
                if player.health <= 0:
                    break
        # Heals outside of combat
        elif action == "3":
            print(player.heal())
        # Checks players inventory
        elif action == "4":
            print(f"Inventory: {player.inventory}")
        # Saves game state
        elif action == "5":
            save_state(player, rooms)
        # Loads game state
        elif action == "6":
            player, rooms = load_state()
            if player:
                print(player.room.describe())
        # Quits game
        elif action == "7":
            print("Goodbye!")
            break
        # Handles all other inputs
        else:
            print("Invalid action.")

# Actually runs game
game_loop()
