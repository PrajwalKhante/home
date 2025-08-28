import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse

class Crawler:
    def __init__(self, starting_url, max_pages=50):
        self.starting_url = starting_url
        self.domain_name = urlparse(starting_url).netloc
        self.links_to_visit = [starting_url]
        self.visited_links = set()
        self.max_pages = max_pages

    def crawl(self):
        """
        Crawls the website starting from self.starting_url.
        """
        while self.links_to_visit and len(self.visited_links) < self.max_pages:
            url = self.links_to_visit.pop(0)
            if url in self.visited_links:
                continue

            self.visited_links.add(url)
            print(f"Crawling: {url}")

            try:
                response = requests.get(url)
                response.raise_for_status()
            except requests.RequestException as e:
                print(f"Error fetching {url}: {e}")
                continue

            soup = BeautifulSoup(response.content, 'html.parser')

            for a_tag in soup.find_all('a', href=True):
                href = a_tag.get('href')
                absolute_url = urljoin(self.starting_url, href)
                parsed_url = urlparse(absolute_url)
                absolute_url = parsed_url.scheme + "://" + parsed_url.netloc + parsed_url.path

                if self.domain_name != urlparse(absolute_url).netloc:
                    continue # Stay on the same domain

                if absolute_url not in self.visited_links and absolute_url not in self.links_to_visit:
                    self.links_to_visit.append(absolute_url)

        return list(self.visited_links)

def scan_website(url, max_pages=50):
    """
    Initializes and runs the crawler.
    """
    crawler = Crawler(url, max_pages)
    return crawler.crawl()
