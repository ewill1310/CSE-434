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
        # Using the OpenAI API generation method you specified
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
        self.xp = 0  # XP counter
        self.level = 1
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
            next_room_id = self.room.connections[direction]
            return rooms[next_room_id]
        else:
            print("You can't move in that direction.")
            return self.room  # Stay in the same room if the direction is invalid

    def level_up(self):
        if self.xp >= 100:  # Level up condition
            self.level += 1
            self.health += 20  # Increase health on level up
            self.xp = 0  # Reset XP after leveling up
            return f"Congratulations! You've reached level {self.level} and gained 20 extra health!"
        return None  # No level up yet

    def enemy_attack(self):
        roll = random.randint(1, 20)
        if roll > 10:
            damage = random.randint(5, 15)
            self.health -= damage
            return f"The enemy attacks! You take {damage} damage."
        else:
            return "The enemy misses their attack!"

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
    previous_room = None

    # Generate connected rooms
    for i in range(1, 10):  # Create 10 rooms for now
        room_name = f"Room {i+1}"
        npc = generate_npc_or_boss()
        boss = random.choice([True, False])
        room = Room(room_count, room_name, npc=npc, boss=boss)

        # Link rooms in all 4 directions (ensure north, south, east, west connections)
        if current_room:
            current_room.connections["east"] = room.room_id
            room.connections["west"] = current_room.room_id
        
        if previous_room:
            previous_room.connections["south"] = room.room_id
            room.connections["north"] = previous_room.room_id

        rooms[room_count] = room
        current_room = room
        room_count += 1
        previous_room = current_room

    return rooms, start_room

# Game loop
def game_loop():
    player_name = input("Enter your character's name: ")
    player = Player(player_name)
    rooms, start_room = create_dungeon()

    player.room = start_room
    print(player.room.describe())

    while True:
        print("\nChoose an action:")
        print("1. Move (north / south / east / west)")
        print("2. Fight")
        print("3. Heal")
        print("4. Check Inventory")
        print("5. Quit")

        action = input("Action: ")

        if action == "1":
            direction = input("Which direction would you like to move? (north / south / east / west): ").lower()
            print(player.room.describe())
            new_room = player.move(direction, rooms)
            player.room = new_room  # Update player's current room after movement
            print(player.room.describe())

        elif action == "2":
            if player.room.npc:
                enemy_health = 40  # Set enemy health to 40
                print(f"A wild {player.room.npc} appears! (Health: {enemy_health})")
                while player.health > 0 and enemy_health > 0:
                    print(f"Your health: {player.health} | Enemy health: {enemy_health}")
                    print("1. Attack")
                    print("2. Heal")
                    print("3. Flee")
                    choice = input("What will you do? ")

                    if choice == "1":
                        attack_result = player.attack(enemy_health)
                        print(attack_result)
                        enemy_health -= random.randint(5, 15)  # Reduce enemy health
                    elif choice == "2":
                        heal_result = player.heal()
                        print(heal_result)
                    elif choice == "3":
                        flee_result = player.flee()
                        print(flee_result)
                        break  # Exit the combat loop
                    else:
                        print("Invalid action.")

                    if enemy_health <= 0:
                        print(f"You defeated the {player.room.npc}!")
                        player.xp += 50
                        print(f"XP Gained: 50")  # Print the XP gained
                        level_up_result = player.level_up()
                        if level_up_result:
                            print(level_up_result)
                        break

                    if player.health <= 0:
                        print("You have been defeated. Game over!")
                        return  # Exit the game

                    # Enemy's turn to attack
                    enemy_attack_result = player.enemy_attack()
                    print(enemy_attack_result)

            else:
                print("There are no enemies in this room.")

        elif action == "3":
            heal_result = player.heal()
            print(heal_result)

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
