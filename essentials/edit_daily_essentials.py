import questionary
from questionary import Choice
import json
import sys

subjects_items_kv_path = "essentials/items.json"
essential_items_path = "essentials/timetable.json"
daily_essentials_path = "essentials/daily_essentials.json"
subjects_items_kv:dict[str, list[str]] = {}

try:
    with open(subjects_items_kv_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        if isinstance(content, dict):
            subjects_items_kv = content
        else:
            print("Error: items.json must be a dict.")
            sys.exit(1)
except FileNotFoundError:
    print(f"Error: {subjects_items_kv_path} not found.")
    sys.exit(1)

timetable = {}
try:
    with open(essential_items_path, "r", encoding="utf-8") as f:
        timetable_content = json.load(f)
        if isinstance(timetable_content, dict):
            timetable = timetable_content
        else:
            print("Error: daily_essentials.json must be a dict.")
            sys.exit(1)
except Exception as e:
    print(f"Failed to read {essential_items_path}")
    print(str(e))
    sys.exit(1)

days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

selected_subjects = {}
daily_essentials = {}

subjects_set = set(subjects_items_kv.keys())
timetable_set = {k: set(v) for k,v in timetable.items()}

for day in days:
    if timetable_set[day] == set([]):
        options = ["new_subject"]
    else:
        options = choices=[
            *map(lambda x : Choice(x, checked=True), timetable_set[day]),
            Choice("new_subject", checked=False)
        ]
    res = set(questionary.checkbox(
        f"Select essentials ({day})",
        choices=options
    ).ask())
    if res is None:
        print("\nInterrupted by user.")
        sys.exit(0)
    if "new_subject" in res:
        res = res.union(set(questionary.checkbox(
            f"Select new item ({day})",
            choices=subjects_set.difference(timetable_set[day])
        ).ask()))
    res.discard("new_subject")
    selected_subjects[day] = list(res)
    print(selected_subjects[day])
    daily_essentials[day] = list(set([]).union(*[set(subjects_items_kv[subject]) for subject in selected_subjects[day]]))

if questionary.confirm("Save this configuration?").ask():
    try:
        with open(essential_items_path, "w", encoding="utf-8") as f:
            json.dump(selected_subjects, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to {essential_items_path}")
    except Exception as e:
        print(f"Failed to edit {essential_items_path}")
        print(str(e))
    try:
        with open(daily_essentials_path, "w", encoding="utf-8") as f:
            json.dump(daily_essentials, f, ensure_ascii=False, indent=4)
        print(f"Successfully saved to {daily_essentials_path}")
    except Exception as e:
        print(f"Failed to edit {daily_essentials_path}")
        print(str(e))
else:
    print("Discarded changes.")