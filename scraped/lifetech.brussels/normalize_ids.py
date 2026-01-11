import tomlkit
from pathlib import Path

# Path to your TOML file
target_file = Path(__file__).parent / 'members.toml'

def normalize_ids():
    if not target_file.exists():
        print(f"Error: File not found at {target_file}")
        return

    with open(target_file, 'r') as f:
        doc = tomlkit.parse(f.read())

    members = doc.get('members', {}).get('company', [])
    print(f"Found {len(members)} members. Assigning sequential IDs...")

    # Re-index all members with a sequential integer ID
    # This establishes the baseline (1 to 70)
    for index, member in enumerate(members, 1):
        # Overwrite existing string ID or add new integer ID
        member['id'] = index

    with open(target_file, 'w') as f:
        f.write(doc.as_string())
    
    print(f"Successfully re-indexed {len(members)} members.")

if __name__ == "__main__":
    normalize_ids()