import os
from dotenv import load_dotenv
import random
import openai
from openai import OpenAI

# Load environment variables from the .env file
load_dotenv()

# Get OpenAI API Key from the environment variable
openai.api_key = os.getenv('OPENAI_API_KEY')
client = OpenAI(
    api_key=openai.api_key,
)

# Define the Room class
class Room:
    def __init__(self, room_id, room_name, npc=None, boss=False, connections=None):
        self.room_id = room_id
        self.room_name = room_name
        self.npc = npc
        self.boss = boss
        self.connections = connections or {}  # Dictionary to hold neighboring rooms

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


# Define the Player class
class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = ["health_potion"]
        self.health = 100
        self.room = None  # Current room

    def attack(self, enemy_health):
        roll = random.randint(1, 20)  # D20 for attack roll
        damage = random.randint(5, 15)  # Random damage
        if roll > 10:
            enemy_health -= damage
            return f"Attack successful! You dealt {damage} damage."
        else:
            return "Attack missed!"

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
            return None  # Invalid direction


# Function to generate NPC or Boss chance
def generate_npc_or_boss():
    npc_chance = random.randint(1, 10)
    if npc_chance <= 7:
        return "Goblin"  # 70% chance of goblin
    elif npc_chance == 8:
        return "Orc"  # 10% chance of orc
    elif npc_chance == 9:
        return "Troll"  # 10% chance of troll
    elif npc_chance == 10:
        return "Dragon"  # 10% chance of boss (Dragon)
    return None


# Create dungeon map and state management
def create_dungeon():
    rooms = {}
    room_count = 0
    start_room = Room(room_count, "Start Room", npc=generate_npc_or_boss(), boss=random.choice([True, False]))
    rooms[room_count] = start_room
    room_count += 1
    current_room = start_room

    # Initially create 4 neighboring rooms for the start room
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
    """Return the opposite direction."""
    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposite_directions[direction]


# Game loop
def game_loop():
    player_name = input("Enter your character's name: ")
    player = Player(player_name)
    rooms, start_room = create_dungeon()

    player.room = start_room
    print(player.room.describe())  # Show the start room description

    visited_rooms = set()  # Keep track of visited rooms for backtracking
    visited_rooms.add(player.room.room_id)  # Add the start room as visited

    previous_room = None  # To store the previous room for backtracking

    while True:
        print("\nChoose an action: (Type the number)")
        print("1. Move (north / south / east / west)")
        print("2. Fight")
        print("3. Heal")
        print("4. Check Inventory")
        print("5. Quit")

        action = input("Action: ")

        if action == "1":
            direction = input("Which direction would you like to move? (north / south / east / west): ").lower()
            if direction in player.room.connections:
                new_room = player.move(direction, rooms)
                if new_room:
                    # Save the current room as the previous room for backtracking
                    previous_room = player.room
                    player.room = new_room
                    visited_rooms.add(player.room.room_id)  # Mark the new room as visited

                    # Ensure all 4 neighboring rooms are generated (if not already done)
                    for direction in ["north", "south", "east", "west"]:
                        if direction not in player.room.connections:
                            room_name = f"Room {len(rooms)+1}"
                            npc = generate_npc_or_boss()
                            boss = random.choice([True, False])
                            room = Room(len(rooms), room_name, npc=npc, boss=boss)
                            player.room.connections[direction] = room.room_id
                            room.connections[get_opposite_direction(direction)] = player.room.room_id
                            rooms[len(rooms)] = room

                    # Ensure the previous room maintains the connection to the new room
                    if previous_room:
                        previous_room.connections[get_opposite_direction(direction)] = player.room.room_id
                        player.room.connections[get_opposite_direction(direction)] = previous_room.room_id

                    # Print the new room's description only
                    print(player.room.describe())

                else:
                    print("You can't move in that direction.")
            else:
                print("You can't move in that direction.")

        elif action == "2":
            if player.room.npc:
                print(f"A wild {player.room.npc} appears!")
                print("1. Attack")
                print("2. Heal")
                print("3. Flee")
                choice = input("What will you do? ")

                if choice == "1":
                    attack_result = player.attack(100)
                    print(attack_result)
                elif choice == "2":
                    heal_result = player.heal()
                    print(heal_result)
                elif choice == "3":
                    flee_result = player.flee()
                    print(flee_result)
                else:
                    print("Invalid action.")
            else:
                print("There are no enemies in this room.")

        elif action == "3":
            print("Your inventory:", player.inventory)

        elif action == "4":
            print("Your health:", player.health)
            print("Your inventory:", player.inventory)

        elif action == "5":
            print("You quit the game. Goodbye!")
            break

        else:
            print("Invalid action.")


if __name__ == "__main__":
    game_loop()
