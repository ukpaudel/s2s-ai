import csv
import json
'''
python s2s_pipeline\utils\contact_to_json.py .\personaldata\contacts.csv .\personaldata\contacts.json
'''

def convert_csv_to_json(csv_path, json_path="contacts.json"):
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        contacts = {}

        for row in reader:
            first = row.get("First Name", "").strip()
            middle = row.get("Middle Name", "").strip()
            last = row.get("Last Name", "").strip()
            email = row.get("E-mail 1 - Value", "").strip().lower()

            full_name = " ".join(filter(None, [first, middle, last])).lower()

            if full_name and email:
                contacts[full_name] = email

        with open(json_path, "w", encoding="utf-8") as jsonfile:
            json.dump(contacts, jsonfile, indent=2)

    print(f"✅ Converted {csv_path} → {json_path}")

# Optional CLI usage
if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python csv_to_contacts_json.py path/to/contacts.csv [output.json]")
    else:
        input_csv = sys.argv[1]
        output_json = sys.argv[2] if len(sys.argv) > 2 else "contacts.json"
        convert_csv_to_json(input_csv, output_json)
