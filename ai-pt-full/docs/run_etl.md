# How to Run the ETL Pipeline

This document provides instructions for running the ETL (Extract, Transform, Load) pipeline to gather and process the data needed for training the AI models.

## Prerequisites

1.  **Install Dependencies:** Ensure you have installed all the required Python packages.
    ```bash
    pip install -r requirements.txt
    ```

2.  **Check Internet Connection:** The ETL process requires an internet connection to download data from NVD, Exploit-DB, and Retire.js.

## Step 1: Download NVD, Exploit-DB, and Retire.js Data

These scripts download vulnerability information from public databases.

-   **NVD Data:** Downloads CVE information from the National Vulnerability Database.
-   **Exploit-DB Data:** Downloads a database of public exploits.
-   **Retire.js Data:** Downloads a repository of known vulnerable JavaScript libraries.

To run these scripts, navigate to the `ml` directory and execute them in order:

```bash
cd ml
python nvd_etl.py
python exploitdb_etl.py
python retire_etl.py
cd ..
```

This will create a `data` directory in the project root with subdirectories for `nvd`, `exploitdb`, and `retirejs` containing the downloaded data.

## Step 2: Web Crawling (Optional but Recommended)

This step involves crawling authorized web applications to gather real-world HTML and JavaScript samples.

**IMPORTANT:** Only run the web crawler on targets you are explicitly authorized to test. For development, we recommend using a locally hosted, deliberately vulnerable application like [OWASP Juice Shop](https://owasp.org/www-project-juice-shop/) or [DVWA](https://dvwa.co.uk/).

1.  **Start Your Target Application:** Make sure your target web application is running and accessible. For example, Juice Shop might be at `http://localhost:3000`.

2.  **Run the Crawler:** Edit the `ml/web_crawler.py` script to set the `target_url` variable.

    ```python
    # In ml/web_crawler.py
    if __name__ == '__main__':
        target_url = "http://localhost:3000" # CHANGE THIS
        print(f"[*] Starting crawl of {target_url}. Ensure this is an authorized target.")
        crawler = WebCrawler(target_url)
        crawler.crawl()
        print("[*] Crawling complete.")
    ```

3.  **Execute the Script:**
    ```bash
    cd ml
    python web_crawler.py
    cd ..
    ```
    This will create a `data/crawled_data` directory with JSON files for each crawled page.

## Step 3: Generate the Unified Dataset

After gathering all the raw data, this final step processes and combines it into a single labeled dataset ready for model training.

The `labeling.py` script will:
-   Process NVD descriptions and apply weak labels.
-   Incorporate exploit data to flag CVEs with known exploits.
-   Process crawled web data and apply labels.
-   Generate a unified `unified_dataset.csv` file in the `data` directory.

To run the script:

```bash
cd ml
python labeling.py
cd ..
```

After this step is complete, you will have `data/unified_dataset.csv`, and you are ready to proceed with model training.
