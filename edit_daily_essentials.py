import questionary
import json
import sys

items_path = "items.json"
essential_items_path = "essentials.json"
items = []

try:
    with open(items_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        if isinstance(content, list):
            items = content
        else:
            print("Error: items.json must be a list.")
            sys.exit(1)
except FileNotFoundError:
    print(f"Error: {items_path} not found.")
    sys.exit(1)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

selected_items = {}

for day in days:
    res = questionary.checkbox(
        f"Select essentials ({day})",
        choices=items
    ).ask()

    if res is None:
        print("\nInterrupted by user.")
        sys.exit(0)
    selected_items[day] = res

if questionary.confirm("Save this configuration?").ask():
    with open(essential_items_path, "w", encoding="utf-8") as f:
        json.dump(selected_items, f, ensure_ascii=False, indent=4)
    print(f"Successfully saved to {essential_items_path}")
else:
    print("Discarded changes.")