import questionary
from questionary import Choice
import json
import sys

items_path = "essentials/items.json"
essential_items_path = "essentials/daily_essentials.json"
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

daily_essentials = {}
try:
    with open(essential_items_path, "r", encoding="utf-8") as f:
        essential_content = json.load(f)
        print(content)
        if isinstance(essential_content, dict):
            daily_essentials = essential_content
        else:
            print("Error: daily_essentials.json must be a dict.")
            sys.exit(1)
except Exception as e:
    print(f"Failed to read {essential_items_path}")
    print(str(e))
    sys.exit(1)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

selected_items = {}

items_set = set(items)
daily_essentials_set = {k: set(v) for k,v in daily_essentials.items()}

for day in days:
    if daily_essentials_set[day] == set([]):
        options = ["new_item"]
    else:
        options = choices=[
            *map(lambda x : Choice(x, checked=True), daily_essentials_set[day]),
            Choice("new_item", checked=False)
        ]
    res = set(questionary.checkbox(
        f"Select essentials ({day})",
        choices=options
    ).ask())
    if res is None:
        print("\nInterrupted by user.")
        sys.exit(0)
    if "new_item" in res:
        res = res.union(set(questionary.checkbox(
            f"Select new item ({day})",
            choices=items_set.difference(daily_essentials_set[day])
        ).ask()))
    res.discard("new_item")
    selected_items[day] = list(res)
    print(res)

if questionary.confirm("Save this configuration?").ask():
    try:
        with open(essential_items_path, "w", encoding="utf-8") as f:
            json.dump(selected_items, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to {essential_items_path}")
    except Exception as e:
        print(f"Failed to edit {essential_items_path}")
        print(str(e))
else:
    print("Discarded changes.")