import gym
from gym import spaces
import numpy as np
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import sys
import os

# Add project root to path to import ml.infer
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from ml.infer import ModelInference

class WebAppPenTestEnv(gym.Env):
    """
    A custom Gym environment for simulating a web application penetration test.
    The agent learns to discover vulnerabilities by taking actions and observing ML predictions.
    """
    def __init__(self, target_url):
        super(WebAppPenTestEnv, self).__init__()

        self.target_url = target_url
        self.inference_engine = ModelInference()
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'RL-Pentest-Agent/1.0'})

        # --- Action Space ---
        # 0: Probe Target - Make a GET request and get initial ML scores.
        # 1: Analyze HTML - Look for forms and interesting comments.
        # 2: Analyze JS - Find and analyze linked JavaScript files.
        # 3: Check Headers - Look for insecure headers.
        self.action_space = spaces.Discrete(4)

        # --- Observation Space ---
        # A vector representing the state of our knowledge about the target.
        # - 5 ML prediction scores (xss, sqli, csrf, rce, info_leak)
        # - 1 flag for forms found (0 or 1)
        # - 1 flag for JS files found (0 or 1)
        # - 1 flag for insecure headers found (0 or 1)
        # - 1 value for the number of links discovered
        num_vuln_classes = 5 # Assuming 5 classes from our ML model
        self.observation_space = spaces.Box(low=0, high=10, shape=(num_vuln_classes + 4,), dtype=np.float32)

        # --- Internal State ---
        self.reset()

    def reset(self):
        """Reset the environment to an initial state."""
        self.max_steps = 20
        self.current_step = 0
        self.discovered_links = {self.target_url}
        self.visited_links = set()
        self.current_ml_scores = np.zeros(5) # xss, sqli, etc.
        self.found_forms = 0
        self.found_js = 0
        self.found_insecure_headers = 0

        # Initial observation is all zeros
        return self._get_observation()

    def step(self, action):
        """Execute one time step within the environment."""
        self.current_step += 1
        reward = -0.1 # Small penalty for each step to encourage efficiency

        # Choose a link to investigate that hasn't been visited
        target_link = next((link for link in self.discovered_links if link not in self.visited_links), None)
        if not target_link:
            # If no new links, the episode ends
            return self._get_observation(), -10, True, {"info": "Exploration exhausted"}

        try:
            response = self.session.get(target_link, timeout=10)
            self.visited_links.add(target_link)

            if action == 0: # Probe Target
                text_content = BeautifulSoup(response.text, 'html.parser').get_text()
                preds = self.inference_engine.predict_tfidf(text_content)
                new_scores = np.array(list(preds.values()))

                # Reward for increasing vulnerability scores
                reward += np.sum(new_scores - self.current_ml_scores)
                self.current_ml_scores = new_scores

            elif action == 1: # Analyze HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                if not self.found_forms and soup.find_all('form'):
                    self.found_forms = 1
                    reward += 2 # Big reward for finding forms the first time

            elif action == 2: # Analyze JS
                soup = BeautifulSoup(response.text, 'html.parser')
                js_links = [urljoin(target_link, s['src']) for s in soup.find_all('script', src=True)]
                if not self.found_js and js_links:
                    self.found_js = 1
                    reward += 1 # Reward for finding JS

            elif action == 3: # Check Headers
                insecure_headers = ['Server', 'X-Powered-By', 'X-AspNet-Version']
                if not self.found_insecure_headers and any(h in response.headers for h in insecure_headers):
                    self.found_insecure_headers = 1
                    reward += 2 # Reward for finding leaky headers

            # Discover new links on the same domain
            soup = BeautifulSoup(response.text, 'html.parser')
            for link in soup.find_all('a', href=True):
                abs_link = urljoin(target_link, link['href'])
                if urlparse(abs_link).netloc == urlparse(self.target_url).netloc:
                    if abs_link not in self.discovered_links:
                        self.discovered_links.add(abs_link)
                        reward += 0.5 # Reward for discovering new paths

        except requests.RequestException:
            reward -= 2 # Penalty for trying to access a broken link

        # Check if the episode is done
        done = self.current_step >= self.max_steps or self.current_ml_scores.max() > 0.9

        return self._get_observation(), reward, done, {}

    def _get_observation(self):
        """Constructs the observation vector from the current state."""
        obs = np.concatenate([
            self.current_ml_scores,
            np.array([
                self.found_forms,
                self.found_js,
                self.found_insecure_headers,
                len(self.discovered_links)
            ])
        ])
        return obs.astype(np.float32)

    def render(self, mode='human'):
        """Renders the environment (optional)."""
        print(f"Step: {self.current_step}")
        print(f"ML Scores: {self.current_ml_scores}")
        print(f"State Flags: {[self.found_forms, self.found_js, self.found_insecure_headers]}")
        print(f"Discovered Links: {len(self.discovered_links)}")

if __name__ == '__main__':
    # --- Example Usage ---
    # It's recommended to run this against a local, safe target like DVWA or Juice Shop.
    # e.g., target = "http://localhost:3000"

    print("[*] RL Environment is ready. To use, instantiate it with a target URL.")
    # env = WebAppPenTestEnv(target_url="http://localhost:3000")
    # obs = env.reset()
    # print("Initial Observation:", obs)
    # for _ in range(10):
    #     action = env.action_space.sample() # Take a random action
    #     obs, reward, done, info = env.step(action)
    #     env.render()
    #     if done:
    #         break
