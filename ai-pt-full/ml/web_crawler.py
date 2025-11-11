import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import os
import json

class WebCrawler:
    def __init__(self, start_url, max_depth=2, output_dir="data/crawled_data"):
        self.start_url = start_url
        self.max_depth = max_depth
        self.output_dir = output_dir
        self.visited = set()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'AI-PT-Crawler/1.0'
        })
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

    def crawl(self):
        self._crawl_recursive(self.start_url, 0)

    def _crawl_recursive(self, url, depth):
        if url in self.visited or depth > self.max_depth:
            return

        print(f"[*] Crawling: {url} at depth {depth}")
        self.visited.add(url)

        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()

            # Process the page
            self.process_page(url, response)

            # Find and follow links
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                absolute_link = urljoin(url, link['href'])
                if self._is_valid_url(absolute_link):
                    self._crawl_recursive(absolute_link, depth + 1)

        except requests.exceptions.RequestException as e:
            print(f"[!] Error crawling {url}: {e}")

    def process_page(self, url, response):
        soup = BeautifulSoup(response.text, 'html.parser')

        # Extract data
        html_content = response.text
        js_files = [urljoin(url, script['src']) for script in soup.find_all('script', src=True)]
        headers = dict(response.headers)
        forms = self._extract_forms(soup, url)

        # Save data
        parsed_url = urlparse(url)
        filename = f"{parsed_url.netloc.replace('.', '_')}_{parsed_url.path.replace('/', '_') or 'index'}.json"
        filepath = os.path.join(self.output_dir, filename)

        data = {
            "url": url,
            "html": html_content,
            "js_files": js_files,
            "headers": headers,
            "forms": forms,
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2)

    def _extract_forms(self, soup, url):
        forms_data = []
        for form in soup.find_all('form'):
            action = form.get('action', '')
            method = form.get('method', 'GET').upper()
            inputs = []
            for input_tag in form.find_all('input'):
                inputs.append({
                    'name': input_tag.get('name'),
                    'type': input_tag.get('type', 'text'),
                    'value': input_tag.get('value', '')
                })
            forms_data.append({
                'action': urljoin(url, action),
                'method': method,
                'inputs': inputs
            })
        return forms_data

    def _is_valid_url(self, url):
        # Basic check to stay on the same domain
        return urlparse(url).netloc == urlparse(self.start_url).netloc

if __name__ == '__main__':
    # Example usage:
    # This should be run on authorized targets only.
    # Using a locally hosted or deliberately vulnerable app is recommended.
    # For instance, if Juice Shop is running at http://localhost:3000

    # target_url = "http://localhost:3000"
    # print(f"[*] Starting crawl of {target_url}. Ensure this is an authorized target.")
    # crawler = WebCrawler(target_url)
    # crawler.crawl()
    # print("[*] Crawling complete.")

    print("[*] Web Crawler script is ready. To use, uncomment the example in `if __name__ == '__main__':`")
    print("[*] and provide a root URL of an authorized target application.")
