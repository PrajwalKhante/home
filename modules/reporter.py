import csv

def generate_report(vulnerabilities, filename="vulnerability_report.csv"):
    """
    Generates a CSV report of the vulnerabilities found.
    """
    if not vulnerabilities:
        print("No vulnerabilities to report.")
        return

    keys = vulnerabilities[0].keys()

    try:
        with open(filename, 'w', newline='') as output_file:
            dict_writer = csv.DictWriter(output_file, fieldnames=keys)
            dict_writer.writeheader()
            dict_writer.writerows(vulnerabilities)
        print(f"Report generated successfully: {filename}")
    except IOError as e:
        print(f"Error writing report to {filename}: {e}")
