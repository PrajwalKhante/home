import pandas as pd
import json
import os
import re
from tqdm import tqdm

# --- Configuration ---
NVD_FILE = "data/nvd/nvd_cves.jsonl"
EXPLOITDB_FILE = "data/exploitdb/exploitdb_exploits.csv"
CRAWLED_DIR = "data/crawled_data"
OUTPUT_DATASET = "data/unified_dataset.csv"

# --- Vulnerability Labeling Rules ---
VULN_KEYWORDS = {
    'xss': ['cross-site scripting', 'xss', 'reflected xss', 'stored xss'],
    'sqli': ['sql injection', 'sqli', 'database injection'],
    'csrf': ['cross-site request forgery', 'csrf', 'xsrf'],
    'rce': ['remote code execution', 'rce', 'code injection', 'command injection'],
    'info_leak': ['information disclosure', 'information leak', 'sensitive data exposure']
}

def load_nvd_data(filepath):
    """Loads NVD data from a JSON Lines file."""
    if not os.path.exists(filepath):
        print(f"[!] NVD data not found at {filepath}. Please run nvd_etl.py first.")
        return pd.DataFrame()
    return pd.read_json(filepath, lines=True)

def load_exploitdb_data(filepath):
    """Loads Exploit-DB data."""
    if not os.path.exists(filepath):
        print(f"[!] Exploit-DB data not found at {filepath}. Please run exploitdb_etl.py first.")
        return pd.DataFrame()
    return pd.read_csv(filepath)

def apply_text_based_labels(text):
    """Applies labels to a given text based on keyword matching."""
    labels = {}
    text = text.lower()
    for vuln, keywords in VULN_KEYWORDS.items():
        if any(re.search(r'\b' + re.escape(kw) + r'\b', text) for kw in keywords):
            labels[vuln] = 1
    return labels

def process_nvd_and_exploits():
    """Processes NVD data and merges exploit information."""
    df_nvd = load_nvd_data(NVD_FILE)
    df_exploitdb = load_exploitdb_data(EXPLOITDB_FILE)

    if df_nvd.empty:
        return []

    # Create a set of CVEs that have exploits for quick lookup
    exploited_cves = set(df_exploitdb['cve'].dropna())

    dataset = []
    for _, row in tqdm(df_nvd.iterrows(), total=len(df_nvd), desc="Processing NVD data"):
        text = row['description']
        labels = apply_text_based_labels(text)

        # Skip if no labels were applied
        if not labels:
            continue

        dataset.append({
            'id': row['cve_id'],
            'text': text,
            'html': '',
            'js_files': [],
            'cve': row['cve_id'],
            'exploit_exists': 1 if row['cve_id'] in exploited_cves else 0,
            'labels': json.dumps(labels),
            'severity': row.get('severity', 'UNKNOWN'),
            'headers': {},
            'source': 'nvd',
            'timestamp': pd.Timestamp.now()
        })
    return dataset

def process_crawled_data():
    """Processes crawled web data."""
    if not os.path.exists(CRAWLED_DIR) or not os.listdir(CRAWLED_DIR):
        print("[*] No crawled data found. Skipping.")
        return []

    dataset = []
    for filename in tqdm(os.listdir(CRAWLED_DIR), desc="Processing crawled data"):
        if filename.endswith(".json"):
            filepath = os.path.join(CRAWLED_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)

            # Analyze HTML content for labels
            text = data['html']
            labels = apply_text_based_labels(text)

            # Simple header check for info leaks
            if 'server' in data['headers'] or 'X-Powered-By' in data['headers']:
                if 'info_leak' not in labels:
                    labels['info_leak'] = 1
                else:
                    labels['info_leak'] += 0.1 # Boost score slightly

            if not labels:
                continue

            dataset.append({
                'id': data['url'],
                'text': text, # For simplicity, we'll use HTML content as the main text
                'html': data['html'],
                'js_files': json.dumps(data['js_files']),
                'cve': '', # No direct CVE for crawled content
                'exploit_exists': 0,
                'labels': json.dumps(labels),
                'severity': 'UNKNOWN',
                'headers': json.dumps(data['headers']),
                'source': 'crawled',
                'timestamp': pd.Timestamp.now()
            })
    return dataset

def create_unified_dataset():
    """Creates a unified dataset from all sources."""
    print("[*] Starting dataset generation...")

    nvd_dataset = process_nvd_and_exploits()
    crawled_dataset = process_crawled_data()

    full_dataset = nvd_dataset + crawled_dataset

    if not full_dataset:
        print("[!] No data was processed. The final dataset is empty.")
        return

    df = pd.DataFrame(full_dataset)

    # Reorder and save
    df = df[['id', 'text', 'html', 'js_files', 'cve', 'exploit_exists', 'labels', 'severity', 'headers', 'source', 'timestamp']]

    # Create the data directory if it doesn't exist
    if not os.path.exists('data'):
        os.makedirs('data')

    df.to_csv(OUTPUT_DATASET, index=False)
    print(f"[*] Unified dataset created with {len(df)} samples.")
    print(f"[*] Saved to {OUTPUT_DATASET}")


if __name__ == "__main__":
    create_unified_dataset()
