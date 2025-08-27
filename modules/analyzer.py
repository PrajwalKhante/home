import os
import requests
import llm
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_vulnerability_confidence(response_text, vulnerability_type):
    """
    Uses an LLM to analyze the response text and determine a confidence score.
    """
    try:
        model = llm.get_model("claude-3-haiku")
        model.key = os.environ.get("ANTHROPIC_API_KEY")

        if not model.key:
            # print("ANTHROPIC_API_KEY environment variable not set. Skipping confidence scoring.")
            return "N/A", "API key not provided."

        prompt = f"""
        As a security expert, analyze the following server response to determine if it indicates a successful {vulnerability_type} injection.
        The response is:
        ---
        {response_text[:2000]}
        ---
        Based on the response, provide a confidence level (low, medium, high) for a {vulnerability_type} vulnerability.
        Then, provide a brief, one-sentence explanation for your reasoning.
        Format your response as: Confidence: [confidence_level], Reason: [explanation]
        """
        response = model.prompt(prompt)

        confidence = "unknown"
        reason = "Could not parse LLM response."

        response_text = response.text().lower()
        if "confidence:" in response_text and "reason:" in response_text:
            confidence_part = response_text.split("confidence:")[1].split(",")[0].strip()
            reason_part = response_text.split("reason:")[1].strip()

            if "low" in confidence_part:
                confidence = "low"
            elif "medium" in confidence_part:
                confidence = "medium"
            elif "high" in confidence_part:
                confidence = "high"

            reason = reason_part

        return confidence, reason

    except Exception as e:
        print(f"Error getting confidence score from LLM: {e}")
        return "error", str(e)

def get_forms(url):
    """This function extracts all forms from a URL"""
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find_all("form")
    except requests.RequestException:
        return []

def get_form_details(form):
    """This function extracts all the useful information about a form"""
    details = {}
    action = form.attrs.get("action", "").lower()
    method = form.attrs.get("method", "get").lower()
    inputs = []
    for input_tag in form.find_all("input"):
        input_type = input_tag.attrs.get("type", "text")
        input_name = input_tag.attrs.get("name")
        inputs.append({"type": input_type, "name": input_name})
    details["action"] = action
    details["method"] = method
    details["inputs"] = inputs
    return details

def submit_form(form_details, url, payload):
    """
    Submits a form with a payload.
    Returns the response
    """
    target_url = urljoin(url, form_details["action"])
    inputs = form_details["inputs"]
    data = {}
    for input_tag in inputs:
        if input_tag["type"] == "text" or input_tag["type"] == "search":
            input_tag["value"] = payload
        input_name = input_tag.get("name")
        input_value = input_tag.get("value")
        if input_name and input_value:
            data[input_name] = input_value

    if form_details["method"] == "post":
        return requests.post(target_url, data=data, timeout=10)
    else:
        return requests.get(target_url, params=data, timeout=10)

def analyze_for_sql_injection(endpoints):
    # (The implementation of this function remains the same)
    vulnerabilities = []
    sql_payloads = [
        "'", "\"", "OR 1=1", "OR '1'='1", "--", ";", "';-",
        "1' ORDER BY 1--", "1' ORDER BY 2--", "1' ORDER BY 3--",
        "1' UNION SELECT NULL--", "1' UNION SELECT NULL, NULL--",
        "1' UNION SELECT 1, 'a', 'b'--",
    ]

    for url in endpoints:
        forms = get_forms(url)
        for form in forms:
            form_details = get_form_details(form)
            for payload in sql_payloads:
                try:
                    response = submit_form(form_details, url, payload)
                    error_patterns = ["sql", "syntax error", "unclosed quotation mark", "mysql", "unknown column"]
                    if any(error in response.text.lower() for error in error_patterns):
                        print(f"Potential SQLi found at {url} with payload: {payload}. Getting confidence score...")
                        confidence, reason = get_vulnerability_confidence(response.text, "SQL Injection")
                        vulnerabilities.append({
                            "type": "SQL Injection",
                            "url": url,
                            "form_action": form_details["action"],
                            "payload": payload,
                            "reason": reason,
                            "confidence": confidence
                        })
                except requests.RequestException:
                    pass
    return vulnerabilities

def analyze_for_xss(endpoints):
    # (The implementation of this function remains the same)
    vulnerabilities = []
    xss_payloads = [
        "<script>alert('XSS')</script>",
        "<img src=x onerror=alert('XSS')>",
        "'\"><script>alert('XSS')</script>",
        "<body onload=alert('XSS')>",
    ]

    for url in endpoints:
        forms = get_forms(url)
        for form in forms:
            form_details = get_form_details(form)
            for payload in xss_payloads:
                try:
                    response = submit_form(form_details, url, payload)
                    if payload in response.text:
                        print(f"Potential XSS found at {url} with payload: {payload}. Getting confidence score...")
                        confidence, reason = get_vulnerability_confidence(response.text, "XSS")
                        vulnerabilities.append({
                            "type": "XSS",
                            "url": url,
                            "form_action": form_details["action"],
                            "payload": payload,
                            "reason": reason,
                            "confidence": confidence
                        })
                except requests.RequestException:
                    pass
    return vulnerabilities

def analyze_endpoints(endpoints, tests_to_run):
    """
    Analyzes endpoints for a variety of injection vulnerabilities.
    """
    vulnerabilities = []
    if "sql" in tests_to_run:
        print("Analyzing for SQL Injection...")
        vulnerabilities.extend(analyze_for_sql_injection(endpoints))
    if "xss" in tests_to_run:
        print("Analyzing for XSS...")
        vulnerabilities.extend(analyze_for_xss(endpoints))

    return vulnerabilities
