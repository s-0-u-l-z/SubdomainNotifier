import subprocess
import os
import json
import time
import requests
from pathlib import Path
import argparse
import sys
import time

def display_banner():
    """Display a cool ASCII banner with a disclaimer, loading line by line."""
    banner_lines = [
        r"  ██████  █    ██  ▄▄▄▄    ███▄    █  ▒█████  ▄▄▄█████▓ ██▓  █████▒██▓▓█████  ██▀███  ",
        r"▒██    ▒  ██  ▓██▒▓█████▄  ██ ▀█   █ ▒██▒  ██▒▓  ██▒ ▓▒▓██▒▓██   ▒▓██▒▓█   ▀ ▓██ ▒ ██▒",
        r"░ ▓██▄   ▓██  ▒██░▒██▒ ▄██▓██  ▀█ ██▒▒██░  ██▒▒ ▓██░ ▒░▒██▒▒████ ░▒██▒▒███   ▓██ ░▄█ ▒",
        r"  ▒   ██▒▓▓█  ░██░▒██░█▀  ▓██▒  ▐▌██▒▒██   ██░░ ▓██▓ ░ ░██░░▓█▒  ░░██░▒▓█  ▄ ▒██▀▀█▄  ",
        r"▒██████▒▒▒▒█████▓ ░▓█  ▀█▓▒██░   ▓██░░ ████▓▒░  ▒██▒ ░ ░██░░▒█░   ░██░░▒████▒░██▓ ▒██▒",
        r"▒ ▒▓▒ ▒ ░░▒▓▒ ▒ ▒ ░▒▓███▀▒░ ▒░   ▒ ▒ ░ ▒░▒░▒░   ▒ ░░   ░▓   ▒ ░   ░▓  ░░ ▒░ ░░ ▒▓ ░▒▓░"
    ]
    for line in banner_lines:
        print(line)
        time.sleep(0.1)  # Simulate cool fast-loading text

    # Add flashing red disclaimer
    disclaimer = "\033[5;31mThe creator of this program is not responsible for any misuse or damage.\033[0m"
    print(disclaimer)

def run_subfinder(target, output_file):
    """Run subfinder for the specified target and save the output to the specified file."""
    try:
        subprocess.run(["subfinder", "-d", target, "-o", output_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running subfinder: {e}")
        raise

def get_available_output_file(base_name, extension=".txt"):
    """Find an available file name, avoiding conflicts."""
    counter = 1
    while True:
        output_file = f"{base_name}{extension}" if counter == 1 else f"{base_name}{counter}{extension}"
        if not Path(output_file).exists() or not is_file_in_use(output_file):
            return output_file
        counter += 1

def is_file_in_use(file_path):
    """Check if a file is being used by another process."""
    try:
        with open(file_path, "a"):
            return False
    except IOError:
        return True

def run_httpx_toolkit(input_file, output_file):
    """Run httpx-toolkit on the input file and save the alive subdomains to the output file."""
    try:
        subprocess.run(["httpx-toolkit", "-l", input_file, "-o", output_file], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running httpx-toolkit: {e}")
        raise

def send_to_discord(webhook_url, message, file_path=None):
    """Send a message (and optionally a file) to Discord via webhook."""
    data = {"content": message}
    files = {"file": open(file_path, "rb")} if file_path else None
    headers = {"Content-Type": "application/json"} if not files else {}

    response = requests.post(webhook_url, data=json.dumps(data) if not files else None, files=files, headers=headers)
    response.raise_for_status()

def load_json(file_path):
    """Load JSON data from a file. Return an empty list if the file doesn't exist."""
    if Path(file_path).exists():
        with open(file_path, "r") as f:
            return json.load(f)
    return []

def save_json(file_path, data):
    """Save JSON data to a file."""
    with open(file_path, "w") as f:
        json.dump(data, f, indent=4)

def main():
    display_banner()

    parser = argparse.ArgumentParser(description="Subdomain Notifier Script")
    parser.add_argument("-d", "--domain", required=True, help="Target domain for subdomain discovery.")
    args = parser.parse_args()

    target_domain = args.domain

    temp_dir = "./temp"
    json_file = "subdomains.json"
    webhook_url = "https://discordapp.com/api/webhooks/1323956253516627999/FHMnjXAT7XSQmd4MTEdGSPslcG6LGSDKYVMjOZjbwM6Y5YTcZVrDUKL5wIP2-Lnt-gYS"

    os.makedirs(temp_dir, exist_ok=True)

    while True:
        # Define file paths
        subfinder_output = os.path.join(temp_dir, "subfinder_output.txt")
        if is_file_in_use(subfinder_output):
            subfinder_output = get_available_output_file(os.path.join(temp_dir, "subfinder_output"))
        httpx_output = os.path.join(temp_dir, "alive_subs.txt")

        try:
            # Run subfinder and httpx-toolkit
            run_subfinder(target_domain, subfinder_output)
            run_httpx_toolkit(subfinder_output, httpx_output)

            # Load previous subdomains from JSON file
            previous_subdomains = set(load_json(json_file))

            # Load new subdomains from httpx-toolkit output
            with open(httpx_output, "r") as f:
                current_subdomains = set(line.strip() for line in f)

            # Find new subdomains
            new_subdomains = current_subdomains - previous_subdomains

            if new_subdomains:
                # Notify Discord of new subdomains
                send_to_discord(webhook_url, f"Found new subdomains for {target_domain}.")
                new_file_path = os.path.join(temp_dir, "new_subdomains.txt")
                with open(new_file_path, "w") as f:
                    f.write("\n".join(new_subdomains))
                send_to_discord(webhook_url, "Here is the list of new subdomains:", new_file_path)

                # Update JSON file
                all_subdomains = list(previous_subdomains | current_subdomains)
                save_json(json_file, all_subdomains)
            else:
                # No new subdomains found
                send_to_discord(webhook_url, "No new subdomains found.")

        except FileNotFoundError as e:
            # Notify Discord that the JSON file was missing
            send_to_discord(webhook_url, "No JSON file found. Creating a new one.")
            save_json(json_file, list(current_subdomains))
        except Exception as e:
            # Notify Discord of any errors
            send_to_discord(webhook_url, f"An error occurred: {e}")

        # Wait for 2 hours before repeating
        time.sleep(7200)

if __name__ == "__main__":
    main()
