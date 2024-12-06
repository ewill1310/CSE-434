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


# Define the Player class
class Player:
    def __init__(self, name):
        self.name = name
        self.inventory = ["health_potion"]
        self.health = 100
        self.room = None

    def attack(self, enemy_health):
        roll = random.randint(1, 20)
        damage = random.randint(5, 25) 
        if roll > 10:
            enemy_health -= damage
            return f"Attack successful! You dealt {damage} damage.", enemy_health
        else:
            return "Attack missed!", enemy_health

    def heal(self):
        if "health_potion" in self.inventory:
            heal_amount = 20
            self.health += heal_amount
            self.inventory.remove("health_potion")  # Remove the potion after use
            print(f"You used a health potion and healed {heal_amount} health.")
        else:
            print("You have no health potions left.")

    def flee(self):
        return "You fled the battle."

    def move(self, direction, rooms):
        # Check if the direction exists, otherwise generate the missing room
        if direction in self.room.connections:
            new_room = rooms[self.room.connections[direction]]
        else:
            # Generate the missing room
            new_room = self.create_new_room(direction, rooms)

        return new_room

    def create_new_room(self, direction, rooms):
        # Create a new room in the given direction
        global room_count  # Ensure to use the global room_count variable
        room_name = f"Room {room_count}"
        npc = generate_npc_or_boss()
        boss = random.choice([True, False])
        new_room = Room(room_count, room_name, npc=npc, boss=boss)
        
        # Connect the new room to the current room
        self.room.connections[direction] = new_room.room_id
        new_room.connections[get_opposite_direction(direction)] = self.room.room_id
        rooms[room_count] = new_room
        
        room_count += 1
        return new_room


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
    global room_count  # Use global room_count variable to maintain unique IDs
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
    opposite_directions = {
        "north": "south",
        "south": "north",
        "east": "west",
        "west": "east"
    }
    return opposite_directions[direction]


# Combat loop
def combat(player, enemy):
    enemy_health = 40

    while enemy_health > 0 and player.health > 0:
        print(f"\nYour health: {player.health} | Enemy ({enemy}) health: {enemy_health}")
        print("1. Attack")
        print("2. Heal")
        print("3. Flee")

        action = input("What will you do? ")

        if action == "1":
            attack_result, enemy_health = player.attack(enemy_health)
            print(attack_result)
        elif action == "2":
            player.heal()
        elif action == "3":
            print(player.flee())
            break
        else:
            print("Invalid action.")

        # If the enemy is still alive, they attack the player
        if enemy_health > 0:
            enemy_attack = random.randint(5, 10)
            player.health -= enemy_attack
            print(f"The {enemy} attacks! You take {enemy_attack} damage.")
        else:
            print(f"The {enemy} has been defeated!")
            player.inventory.append("health_potion")
            print("The enemy dropped a health potion!")

    if player.health <= 0:
        print("You have been defeated!")

# Game loop
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
        print("5. Quit")

        action = input("Action: ")

        if action == "1":
            direction = input("Which direction would you like to move? (north / south / east / west): ").lower()
            new_room = player.move(direction, rooms)
            player.room = new_room
            print(player.room.describe())

        elif action == "2":
            if player.room.npc:
                enemy = player.room.npc
                combat(player, enemy)
            else:
                print("There are no enemies in this room.")

        elif action == "3":
            player.heal()  # Heal by using a health potion

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
