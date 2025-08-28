import os
import requests
import llm
import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def get_vulnerability_details(response_text, vulnerability_type, api_key):
    """
    Uses an LLM to analyze the response text and provide detailed information.
    """
    if not api_key:
        return {
            "confidence": "N/A",
            "explanation": "API key not provided.",
            "impact": "N/A",
            "remediation": "N/A"
        }

    try:
        model = llm.get_model("claude-3-haiku")
        model.key = api_key

        prompt = f"""
        You are a senior web security expert. Analyze the following server response which was triggered by a '{vulnerability_type}' payload.

        Server Response (first 2000 chars):
        ---
        {response_text[:2000]}
        ---

        Based on this response, provide a detailed analysis. Follow this format exactly, using the headings as markers:

        Confidence: [One of: low, medium, high]
        Explanation: [A detailed, 2-3 sentence explanation of why this response suggests a vulnerability.]
        Impact: [A 1-2 sentence description of the potential business or security impact.]
        Remediation: [A brief, actionable, step-by-step guide on how to fix this vulnerability.]
        """
        response = model.prompt(prompt)

        # Use regex to parse the more complex response from the LLM
        text = response.text()
        confidence = re.search(r"Confidence: (.*)", text)
        explanation = re.search(r"Explanation: (.*)", text, re.DOTALL)
        impact = re.search(r"Impact: (.*)", text, re.DOTALL)
        remediation = re.search(r"Remediation: (.*)", text, re.DOTALL)

        return {
            "confidence": confidence.group(1).strip() if confidence else "unknown",
            "explanation": explanation.group(1).strip() if explanation else "Could not parse explanation.",
            "impact": impact.group(1).strip() if impact else "Could not parse impact.",
            "remediation": remediation.group(1).strip() if remediation else "Could not parse remediation."
        }

    except Exception as e:
        print(f"Error getting details from LLM: {e}")
        return {"error": str(e)}

def get_forms(url):
    try:
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.content, "html.parser")
        return soup.find_all("form")
    except requests.RequestException: return []

def get_form_details(form):
    details = {}
    action = form.attrs.get("action", "").lower()
    method = form.attrs.get("method", "get").lower()
    inputs = []
    for input_tag in form.find_all("input"):
        input_type = input_tag.attrs.get("type", "text")
        input_name = input_tag.attrs.get("name")
        inputs.append({"type": input_type, "name": input_name})
    details["action"] = action; details["method"] = method; details["inputs"] = inputs
    return details

def submit_form(form_details, url, payload):
    target_url = urljoin(url, form_details["action"])
    inputs = form_details["inputs"]
    data = {}
    for input_tag in inputs:
        if input_tag["type"] == "text" or input_tag["type"] == "search":
            input_tag["value"] = payload
        input_name = input_tag.get("name")
        input_value = input_tag.get("value")
        if input_name and input_value: data[input_name] = input_value
    if form_details["method"] == "post":
        return requests.post(target_url, data=data, timeout=10)
    else:
        return requests.get(target_url, params=data, timeout=10)

def analyze_for_sql_injection(endpoints, api_key):
    vulnerabilities = []
    sql_payloads = ["'", "1' OR '1'='1"]
    for url in endpoints:
        for form in get_forms(url):
            form_details = get_form_details(form)
            for payload in sql_payloads:
                try:
                    response = submit_form(form_details, url, payload)
                    error_patterns = ["sql", "syntax error", "unclosed quotation mark", "mysql"]
                    if any(error in response.text.lower() for error in error_patterns):
                        details = get_vulnerability_details(response.text, "SQL Injection", api_key)
                        vulnerabilities.append({
                            "type": "SQL Injection", "url": url, "form_action": form_details["action"],
                            "payload": payload, **details
                        })
                except requests.RequestException: pass
    return vulnerabilities

def analyze_for_xss(endpoints, api_key):
    vulnerabilities = []
    xss_payloads = ["<script>alert('XSS')</script>", "'\"><script>alert('XSS')</script>"]
    for url in endpoints:
        for form in get_forms(url):
            form_details = get_form_details(form)
            for payload in xss_payloads:
                try:
                    response = submit_form(form_details, url, payload)
                    if payload in response.text:
                        details = get_vulnerability_details(response.text, "XSS", api_key)
                        vulnerabilities.append({
                            "type": "XSS", "url": url, "form_action": form_details["action"],
                            "payload": payload, **details
                        })
                except requests.RequestException: pass
    return vulnerabilities

def analyze_endpoints(endpoints, tests_to_run, api_key=None):
    vulnerabilities = []
    if "sql" in tests_to_run:
        print("Analyzing for SQL Injection...")
        vulnerabilities.extend(analyze_for_sql_injection(endpoints, api_key))
    if "xss" in tests_to_run:
        print("Analyzing for XSS...")
        vulnerabilities.extend(analyze_for_xss(endpoints, api_key))
    return vulnerabilities
