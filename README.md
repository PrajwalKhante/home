# Real-time CVE to Threat Actor Lookup Tool

This script fetches information about a CVE in real-time.

## Requirements

- Python 3.6+
- `requests` library

## Installation

1.  Clone the repository.
2.  Install the required packages:
    ```bash
    pip install -r requirements.txt
    ```

## Usage

Run the script with a CVE ID as a command-line argument:

```bash
python3 cve_lookup.py <CVE_ID>
```

Example:

```bash
python3 cve_lookup.py CVE-2021-26855
```

### Output

The script will return a JSON object with the following information:

-   `cve`: The CVE ID provided.
-   `exploited`: A boolean indicating if the CVE is in the CISA KEV catalog.
-   `threat_actors`: A list of known threat actors associated with the CVE. Currently, this will always return "No public actor attribution yet".
