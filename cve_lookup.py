import argparse
import json
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

def main():
    parser = argparse.ArgumentParser(description="Fetch information about a CVE.")
    parser.add_argument("cve_id", help="The CVE ID to look up (e.g., CVE-2021-26855).")
    args = parser.parse_args()
    cve_id = args.cve_id.upper()

    CISA_KEV_URL = "https://www.cisa.gov/sites/default/files/feeds/known_exploited_vulnerabilities.json"

    results = {
        "cve": cve_id,
        "exploited": False,
        "threat_actors": ["No public actor attribution yet"],
    }

    with ThreadPoolExecutor() as executor:
        future_to_check = {
            executor.submit(fetch_cisa_kev, CISA_KEV_URL, cve_id): "cisa"
        }

        for future in as_completed(future_to_check):
            check_type = future_to_check[future]
            try:
                if check_type == "cisa":
                    results["exploited"] = future.result()
            except Exception as exc:
                print(f"{check_type} generated an exception: {exc}")

    print(json.dumps(results, indent=4))

def fetch_cisa_kev(url, cve_id):
    """Fetches the CISA KEV catalog and checks if the CVE is present."""
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        kev_data = response.json()
        for vulnerability in kev_data.get("vulnerabilities", []):
            if vulnerability.get("cveID") == cve_id:
                return True
        return False
    except requests.exceptions.RequestException as e:
        print(f"Error fetching CISA KEV data: {e}")
        return False

if __name__ == "__main__":
    main()
