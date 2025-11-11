import requests
import json
import os

# Configuration
RETIREJS_JSON_URL = "https://raw.githubusercontent.com/Retirejs/retire.js/master/repository/jsrepository.json"
OUTPUT_DIR = "data/retirejs"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "retirejs_vulnerabilities.json")

def download_and_parse_retirejs():
    """
    Downloads and parses the Retire.js vulnerability repository.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    print(f"[*] Downloading Retire.js repository from {RETIREJS_JSON_URL}...")

    try:
        response = requests.get(RETIREJS_JSON_URL)
        response.raise_for_status()

        # Load the JSON content
        repo_data = response.json()

        # The data is already in a structured format that's easy to use.
        # We can simply save it for later use.

        print(f"[*] Saving Retire.js repository to {OUTPUT_FILE}...")
        with open(OUTPUT_FILE, 'w') as f:
            json.dump(repo_data, f, indent=2)

        print(f"[*] Retire.js ETL process completed. Found definitions for {len(repo_data.keys())} libraries.")

    except requests.exceptions.RequestException as e:
        print(f"[!] Error downloading Retire.js data: {e}")
    except json.JSONDecodeError as e:
        print(f"[!] Error decoding JSON: {e}")
    except Exception as e:
        print(f"[!] An unexpected error occurred: {e}")

if __name__ == "__main__":
    download_and_parse_retirejs()
