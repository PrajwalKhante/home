import os
import requests
from bs4 import BeautifulSoup
from llama_cpp import Llama
import json
import re

# --- Local LLM Setup ---
MODEL_NAME = "phi-3-mini-4k-instruct.Q4_K_M.gguf"
MODEL_PATH = os.path.join(os.path.abspath(os.path.dirname(__file__)), MODEL_NAME)

llm = None
if os.path.exists(MODEL_PATH):
    try:
        llm = Llama(model_path=MODEL_PATH, n_ctx=4096, verbose=False)
    except Exception as e:
        print(f"Error loading local LLM model: {e}")
else:
    print(f"Model file not found at {MODEL_PATH}.")

def generate_qa_from_text(text_chunk):
    """
    Uses the local LLM to generate a question-and-answer pair from a chunk of text.
    """
    if not llm:
        return None

    prompt = f"""[INST] You are an expert in creating training data for AI models.
    Based on the following text from a cybersecurity guide, generate a single, clear question-and-answer pair that captures the main point of the text.
    Format your output as a single JSON object with two keys: "instruction" and "response".

    Text:
    ---
    {text_chunk}
    ---
    [/INST]
    """

    try:
        output = llm(prompt, max_tokens=512, stop=["[INST]"], temperature=0.5)
        response_text = output["choices"][0]["text"]

        # Use regex to find the JSON object in the response
        match = re.search(r'\{.*\}', response_text, re.DOTALL)
        if match:
            json_str = match.group(0)
            qa_pair = json.loads(json_str)
            if "instruction" in qa_pair and "response" in qa_pair:
                return qa_pair
    except Exception as e:
        print(f"Error generating Q&A pair: {e}")

    return None

def process_owasp_wstg():
    """
    Fetches, cleans, and processes the OWASP Web Security Testing Guide.
    """
    base_url = "https://owasp.org/www-project-web-security-testing-guide/latest/"
    # A few sample pages to demonstrate the process
    test_pages = [
        "0-The_Web_Security_Testing_Framework/0-The_Web_Security_Testing_Framework.html",
        "4-Web_Application_Security_Testing/01-Information_Gathering/01-Conduct_Search_Engine_Discovery.html",
        "4-Web_Application_Security_Testing/08-Session_Management_Testing/01-Testing_for_Session_Management_Schema.html",
        "4-Web_Application_Security_Testing/07-Input_Validation_Testing/01-Testing_for_Reflected_Cross_Site_Scripting.html",
        "4-Web_Application_Security_Testing/07-Input_Validation_Testing/05-Testing_for_SQL_Injection.html",
    ]

    training_data = []

    for page in test_pages:
        url = base_url + page
        try:
            print(f"Fetching {url}...")
            response = requests.get(url)
            soup = BeautifulSoup(response.content, "html.parser")

            # Find the main content of the page
            content = soup.find('div', id='main-content')
            if not content:
                continue

            # Get all text and split it into chunks of a reasonable size for the LLM
            text = content.get_text(separator='\n', strip=True)
            chunks = [p.strip() for p in text.split('\n\n') if len(p.strip()) > 200]

            print(f"Found {len(chunks)} text chunks. Generating Q&A pairs...")
            for chunk in chunks:
                qa_pair = generate_qa_from_text(chunk)
                if qa_pair:
                    training_data.append(qa_pair)
                    print(f"  Generated: {qa_pair['instruction']}")

        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")

    # Save the generated training data to a file
    with open('training_data.jsonl', 'w') as f:
        for item in training_data:
            f.write(json.dumps(item) + "\n")

    print("\nFinished generating training data. Saved to training_data.jsonl")

if __name__ == "__main__":
    if not llm:
        print("Cannot run data preparer because the local LLM model is not loaded.")
    else:
        process_owasp_wstg()
