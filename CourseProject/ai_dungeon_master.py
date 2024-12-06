import os
import json
from dotenv import load_dotenv
import random
import openai
from openai import OpenAI

load_dotenv()

openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openai.api_key,
)

class Room:
    def __init__(self, room_id, room_name, npc=None, boss=False, connections=None):
        self.room_id = room_id
        self.room_name = room_name
        self.npc = npc
        self.boss = boss
        self.connections = connections or {}

    def generate_random_room_description(self):
        prompt = f"Generate a description for a D&D room called {self.room_name}. It could be a normal room or a boss room."
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=100
        )
        description = response.choices[0].message.content.strip()
        return description

    def describe(self):
        room_description = f"Room {self.room_id} - {self.room_name}: {self.generate_random_room_description()}\n"
        if self.npc:
            room_description += f"There is a {self.npc} here.\n"
        if self.boss:
            room_description += "There is a terrifying boss here!\n"
        return room_description

    def to_dict(self):
        return {
            "room_id": self.room_id,
            "room_name": self.room_name,
            "npc": self.npc,
            "boss": self.boss,
            "connections": self.connections
        }

    @staticmethod
    def from_dict(data):
        return Room(
            room_id=data["room_id"],
            room_name=data["room_name"],
            npc=data["npc"],
            boss=data["boss"],
            connections=data["connections"]
        )


class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = ["health_potion"]
        self.health = 100
        self.room = None

    def attack(self, enemy_health):
        roll = random.randint(1, 20)
        damage = random.randint(5, 15)
        if roll > 10:
            enemy_health -= damage
            return f"Attack successful! You dealt {damage} damage.", enemy_health
        else:
            return "Attack missed!", enemy_health

    def heal(self):
        if "health_potion" in self.inventory:
            self.health += 20
            self.inventory.remove("health_potion")
            return "You healed yourself with a potion."
        else:
            return "You have no potions left."

    def flee(self):
        return "You fled the battle."

    def move(self, direction, rooms):
        if direction in self.room.connections:
            return rooms[self.room.connections[direction]]
        else:
            return None

    def to_dict(self):
        return {
            "name": self.name,
            "inventory": self.inventory,
            "health": self.health,
            "room": self.room.room_id if self.room else None
        }

    @staticmethod
    def from_dict(data, rooms):
        player = Player(data["name"])
        player.inventory = data["inventory"]
        player.health = data["health"]
        player.room = rooms.get(data["room"]) if data["room"] is not None else None
        return player


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


def get_opposite_direction(direction):
    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposite_directions[direction]


def save_state(player, rooms, filename="game_state.json"):
    game_state = {
        "player": player.to_dict(),
        "rooms": {room_id: room.to_dict() for room_id, room in rooms.items()}
    }

    with open(filename, 'w') as f:
        json.dump(game_state, f, indent=4)

    print("Game state saved!")


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


def game_loop():
    player_name = input("Enter your character's name: ")
    player = Player(player_name)
    rooms, start_room = create_dungeon()

    player.room = start_room
    print(player.room.describe())

    visited_rooms = set()
    visited_rooms.add(player.room.room_id)

    previous_room = None

    while True:
        print("\nChoose an action: (Type the number)")
        print("1. Move (north / south / east / west)")
        print("2. Fight")
        print("3. Heal")
        print("4. Check Inventory")
        print("5. Save Game")
        print("6. Load Game")
        print("7. Quit")

        action = input("Action: ")

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
        elif action == "2":
            print("You prepare for combat.")
        elif action == "3":
            print(player.heal())
        elif action == "4":
            print(f"Inventory: {player.inventory}")
        elif action == "5":
            save_state(player, rooms)
        elif action == "6":
            player, rooms = load_state()
            if player:
                print(player.room.describe())
        elif action == "7":
            print("Thanks for playing!")
            break
        else:
            print("Invalid action!")

if __name__ == "__main__":
    game_loop()
