import argparse
import os
from modules.scanner import scan_website
from modules.analyzer import analyze_endpoints
from modules.reporter import generate_report

def print_banner():
    """Prints a cool banner."""
    print(r"""
    ___    __    ____  __    ____  _  _  ____  ____  ____    __   ____  __  ____
   / __)  /__\  (  __)(  )  (  _ \( \/ )(  _ \(  __)(    \  /__\ (_  _)/  \(  _ \
  ( (__  /(__)\  ) _) / (_/\ ) __/ \  /  )   / ) _)  ) D ( /(__)\  )( (  O ))   /
   \___)(__)(__)(____)\____/(__)    \/  (__\_)(____)(____/(__)(__)(__) \__/(__\_)
    """)
    print("                      AI-Powered Vulnerability Scanner\n")


def main():
    print_banner()

    parser = argparse.ArgumentParser(
        description="AI-powered website scanner for vulnerability testing.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
        Example usage:
        python agent.py -u http://testphp.vulnweb.com/ --max-pages 10 --tests sql,xss --output report.csv

        Note: For confidence scoring, you must set the ANTHROPIC_API_KEY environment variable.
        You can get a free API key from Anthropic.
        """
    )
    parser.add_argument("-u", "--url", required=True, help="The target website URL to scan.")
    parser.add_argument("--max-pages", type=int, default=20, help="The maximum number of pages to crawl.")
    parser.add_argument("-o", "--output", default="vulnerability_report.csv", help="The name of the CSV report file.")
    parser.add_argument(
        "--tests",
        default="sql,xss",
        help="A comma-separated list of tests to run (e.g., sql,xss). Available tests: sql, xss."
    )

    args = parser.parse_args()

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("Warning: ANTHROPIC_API_KEY environment variable not set.")
        print("The scanner will run, but will not provide confidence scores for vulnerabilities.\n")

    tests_to_run = [test.strip() for test in args.tests.split(',')]

    print(f"Starting scan on {args.url} (max pages: {args.max_pages})...")
    endpoints = scan_website(args.url, args.max_pages)

    if endpoints:
        print(f"\nFound {len(endpoints)} endpoints. Now analyzing for vulnerabilities...")
        vulnerabilities = analyze_endpoints(endpoints, tests_to_run)
        if vulnerabilities:
            print("\n--- Potential Vulnerabilities Found ---")
            for vulnerability in vulnerabilities:
                print(f"Type: {vulnerability['type']}")
                print(f"URL: {vulnerability['url']}")
                print(f"Form Action: {vulnerability['form_action']}")
                print(f"Payload: {vulnerability['payload']}")
                print(f"Confidence: {vulnerability.get('confidence', 'N/A')}")
                print(f"Reason: {vulnerability.get('reason', 'N/A')}")
                print("-" * 35)

            generate_report(vulnerabilities, args.output)
        else:
            print("\nNo potential vulnerabilities found.")
    else:
        print("No endpoints were found to analyze.")

if __name__ == "__main__":
    main()
