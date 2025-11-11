# Dataset Schema

This document describes the schema of the `unified_dataset.csv` file, which is the primary dataset used for training the machine learning models.

## File Format

The dataset is a standard CSV (Comma-Separated Values) file.

## Fields

| Column Name      | Type      | Description                                                                                             | Example                                             |
| ---------------- | --------- | ------------------------------------------------------------------------------------------------------- | --------------------------------------------------- |
| **id**           | `string`  | A unique identifier for the sample. For NVD data, this is the CVE ID. For crawled data, it's the URL.    | `CVE-2023-1234` or `http://example.com/login`       |
| **text**         | `string`  | The primary text content used for training. For NVD, it's the CVE description. For crawled data, it's the extracted text from HTML. | `A SQL injection vulnerability exists in...`        |
| **html**         | `string`  | The raw HTML content of the page. This is only present for samples from the web crawler (`source=crawled`). | `<html><body><h1>Login</h1>...</body></html>`        |
| **js_files**     | `string`  | A JSON-formatted list of JavaScript files found on the crawled page. Empty for NVD data.                  | `["http://example.com/main.js"]`                    |
| **cve**          | `string`  | The CVE ID, if applicable. This will be the same as the `id` for NVD data.                                | `CVE-2023-1234`                                     |
| **exploit_exists**| `integer` | A binary flag (0 or 1) indicating if a known public exploit exists for the CVE in the Exploit-DB database. | `1`                                                 |
| **labels**       | `string`  | A JSON-formatted dictionary representing the weakly-assigned vulnerability labels. Keys are vulnerability types (e.g., `xss`, `sqli`) and values are `1`. | `{"sqli": 1, "rce": 1}`                             |
| **severity**     | `string`  | The severity rating from NVD (e.g., `HIGH`, `MEDIUM`, `LOW`). Marked as `UNKNOWN` for crawled data.       | `HIGH`                                              |
| **headers**      | `string`  | A JSON-formatted dictionary of HTTP response headers from the crawled page. Empty for NVD data.          | `{"Server": "Apache", "Content-Type": "text/html"}` |
| **source**       | `string`  | The origin of the data sample. Either `nvd` or `crawled`.                                                 | `nvd`                                               |
| **timestamp**    | `string`  | The ISO-formatted timestamp of when the data sample was processed.                                        | `2023-10-27T10:00:00.123456`                        |
