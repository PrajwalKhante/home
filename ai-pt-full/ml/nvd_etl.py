import requests
import json
import os
import pandas as pd
from tqdm import tqdm
import time

# --- Configuration ---
NVD_API_URL = "https://services.nvd.nist.gov/rest/json/cves/2.0"
OUTPUT_DIR = "data/nvd"
OUTPUT_FILE = os.path.join(OUTPUT_DIR, "nvd_cves.jsonl")
RESULTS_PER_PAGE = 2000 # Max allowed by the API
MAX_RESULTS = 10000 # Limit the number of results for a quicker run

def fetch_nvd_data_from_api():
    """
    Downloads and parses NVD CVE data using the 2.0 API.
    """
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    all_cves = []
    start_index = 0

    print("[*] Fetching NVD data from the 2.0 API...")

    # Use a session for potential connection pooling
    session = requests.Session()
    # It's good practice to have an API key, but for this we'll add a delay
    # headers = {'apiKey': 'YOUR_NVD_API_KEY'} # If you have one

    with tqdm(total=MAX_RESULTS) as pbar:
        while start_index < MAX_RESULTS:
            params = {
                'resultsPerPage': RESULTS_PER_PAGE,
                'startIndex': start_index
            }

            try:
                # response = session.get(NVD_API_URL, params=params, headers=headers, timeout=30)
                response = session.get(NVD_API_URL, params=params, timeout=30)
                response.raise_for_status()

                data = response.json()
                vulnerabilities = data.get('vulnerabilities', [])

                if not vulnerabilities:
                    print("[*] No more vulnerabilities found. Ending fetch.")
                    break

                for item in vulnerabilities:
                    cve = item.get('cve', {})
                    cve_id = cve.get('id', 'N/A')

                    try:
                        # Descriptions are now in a list
                        description = next((d['value'] for d in cve.get('descriptions', []) if d['lang'] == 'en'), '')
                    except StopIteration:
                        description = ""

                    # Extract CVSSv3.1 metrics if available
                    cvss_v3 = cve.get('metrics', {}).get('cvssMetricV31', [{}])[0].get('cvssData', {})
                    if cvss_v3:
                        severity = cvss_v3.get('baseSeverity', 'UNKNOWN')
                        score = cvss_v3.get('baseScore', 0)
                    else:
                        severity = 'UNKNOWN'
                        score = 0

                    all_cves.append({
                        "cve_id": cve_id,
                        "description": description,
                        "severity": severity,
                        "score": score
                    })

                pbar.update(len(vulnerabilities))
                start_index += len(vulnerabilities)

                # NVD API recommends a delay between requests, especially without an API key
                time.sleep(1) # 1-second delay to be safe

            except requests.exceptions.RequestException as e:
                print(f"[!] Error fetching data from NVD API: {e}")
                # Wait longer before retrying
                time.sleep(10)
            except json.JSONDecodeError as e:
                print(f"[!] Error decoding JSON response: {e}")
                break

    # --- Save to a JSON Lines file ---
    print(f"\n[*] Saving {len(all_cves)} CVEs to {OUTPUT_FILE}...")
    with open(OUTPUT_FILE, 'w') as f:
        for cve in all_cves:
            f.write(json.dumps(cve) + '\n')

    print("[*] NVD ETL process completed.")

if __name__ == "__main__":
    fetch_nvd_data_from_api()
