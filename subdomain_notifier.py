import subprocess
import os
import json
import time
import requests
from pathlib import Path
import argparse
import logging
from datetime import datetime
from typing import Set, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('subdomain_notifier.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def display_banner():
    """Display ASCII banner with disclaimer."""
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
        time.sleep(0.1)
    
    disclaimer = "\033[5;31mThe creator of this program is not responsible for any misuse or damage.\033[0m"
    print(f"\n{disclaimer}\n")

def check_dependencies():
    """Verify required tools are installed."""
    required_tools = ['subfinder', 'httpx']
    missing = []
    
    for tool in required_tools:
        try:
            subprocess.run([tool, '-h'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(tool)
    
    if missing:
        logger.error(f"Missing required tools: {', '.join(missing)}")
        logger.error("Install them before running this script.")
        return False
    return True

def run_subfinder(target: str, output_file: str) -> bool:
    """Run subfinder for the specified target."""
    try:
        logger.info(f"Running subfinder for {target}...")
        result = subprocess.run(
            ["subfinder", "-d", target, "-o", output_file, "-silent"],
            capture_output=True,
            text=True,
            timeout=300
        )
        if result.returncode != 0:
            logger.error(f"Subfinder error: {result.stderr}")
            return False
        logger.info(f"Subfinder completed. Output: {output_file}")
        return True
    except subprocess.TimeoutExpired:
        logger.error("Subfinder timed out after 5 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running subfinder: {e}")
        return False

def run_httpx(input_file: str, output_file: str) -> bool:
    """Run httpx on the input file."""
    try:
        logger.info(f"Running httpx on {input_file}...")
        result = subprocess.run(
            ["httpx", "-l", input_file, "-o", output_file, "-silent"],
            capture_output=True,
            text=True,
            timeout=600
        )
        if result.returncode != 0:
            logger.warning(f"httpx returned non-zero exit code: {result.returncode}")
            logger.warning(f"httpx stderr: {result.stderr}")
        
        # Check if output file exists and has content
        if Path(output_file).exists() and Path(output_file).stat().st_size > 0:
            logger.info(f"httpx completed. Output: {output_file}")
            return True
        else:
            logger.warning("httpx produced no output")
            return False
    except subprocess.TimeoutExpired:
        logger.error("httpx timed out after 10 minutes")
        return False
    except Exception as e:
        logger.error(f"Error running httpx: {e}")
        return False

def send_to_discord(webhook_url: str, message: str, file_path: str = None) -> bool:
    """Send a message and optionally a file to Discord via webhook."""
    try:
        if file_path and Path(file_path).exists():
            with open(file_path, "rb") as f:
                files = {"file": (Path(file_path).name, f)}
                data = {"content": message}
                response = requests.post(webhook_url, data=data, files=files, timeout=30)
        else:
            data = {"content": message}
            response = requests.post(webhook_url, json=data, timeout=30)
        
        response.raise_for_status()
        logger.info(f"Discord notification sent: {message[:50]}...")
        return True
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Discord notification: {e}")
        return False

def load_json(file_path: str) -> List[str]:
    """Load JSON data from a file."""
    try:
        if Path(file_path).exists():
            with open(file_path, "r") as f:
                return json.load(f)
    except json.JSONDecodeError as e:
        logger.error(f"Error reading JSON file: {e}")
    except Exception as e:
        logger.error(f"Unexpected error loading JSON: {e}")
    return []

def save_json(file_path: str, data: List[str]) -> bool:
    """Save JSON data to a file."""
    try:
        with open(file_path, "w") as f:
            json.dump(data, f, indent=4)
        return True
    except Exception as e:
        logger.error(f"Error saving JSON file: {e}")
        return False

def read_subdomains(file_path: str) -> Set[str]:
    """Read subdomains from a file, filtering empty lines."""
    try:
        with open(file_path, "r") as f:
            return {line.strip() for line in f if line.strip()}
    except Exception as e:
        logger.error(f"Error reading file {file_path}: {e}")
        return set()

def main():
    display_banner()
    
    parser = argparse.ArgumentParser(description="Subdomain Notifier Script")
    parser.add_argument("-d", "--domain", required=True, help="Target domain for subdomain discovery")
    parser.add_argument("-wh", "--webhook", required=True, help="Discord webhook URL for notifications")
    parser.add_argument("-i", "--interval", type=int, default=7200, help="Check interval in seconds (default: 7200)")
    args = parser.parse_args()
    
    if not check_dependencies():
        return 1
    
    target_domain = args.domain
    webhook_url = args.webhook
    interval = args.interval
    
    temp_dir = Path("./temp")
    json_file = "subdomains.json"
    
    temp_dir.mkdir(exist_ok=True)
    
    logger.info(f"Starting subdomain monitoring for {target_domain}")
    logger.info(f"Check interval: {interval} seconds ({interval/3600:.1f} hours)")
    send_to_discord(webhook_url, f"🚀 Subdomain monitoring started for **{target_domain}**")
    
    iteration = 0
    while True:
        iteration += 1
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        logger.info(f"=== Iteration {iteration} started at {timestamp} ===")
        
        subfinder_output = temp_dir / "subfinder_output.txt"
        httpx_output = temp_dir / "alive_subs.txt"
        
        try:
            # Run subfinder
            if not run_subfinder(target_domain, str(subfinder_output)):
                send_to_discord(webhook_url, f"⚠️ Subfinder failed for {target_domain}")
                logger.warning("Skipping this iteration due to subfinder failure")
                time.sleep(interval)
                continue
            
            # Run httpx with fallback to subfinder output
            httpx_success = run_httpx(str(subfinder_output), str(httpx_output))
            
            if httpx_success:
                # Use httpx output (live subdomains)
                current_subdomains = read_subdomains(httpx_output)
                logger.info(f"Using httpx results: {len(current_subdomains)} live subdomains")
            else:
                # Fallback to subfinder output
                logger.warning("httpx failed or produced no output, using subfinder results as fallback")
                send_to_discord(webhook_url, f"⚠️ httpx failed for {target_domain}, using all discovered subdomains")
                current_subdomains = read_subdomains(subfinder_output)
                logger.info(f"Using subfinder results: {len(current_subdomains)} total subdomains")
            
            # Load previous subdomains
            previous_subdomains = set(load_json(json_file))
            
            if not current_subdomains:
                logger.warning("No subdomains found in current scan")
            
            # Find new subdomains
            new_subdomains = current_subdomains - previous_subdomains
            
            if new_subdomains:
                logger.info(f"Found {len(new_subdomains)} new subdomain(s)")
                message = f"🎯 Found **{len(new_subdomains)}** new subdomain(s) for **{target_domain}**"
                send_to_discord(webhook_url, message)
                
                # Save and send new subdomains
                new_file_path = temp_dir / "new_subdomains.txt"
                with open(new_file_path, "w") as f:
                    f.write("\n".join(sorted(new_subdomains)))
                send_to_discord(webhook_url, "📋 New subdomains list:", str(new_file_path))
                
                # Update JSON file
                all_subdomains = sorted(previous_subdomains | current_subdomains)
                save_json(json_file, all_subdomains)
            else:
                logger.info("No new subdomains found")
                send_to_discord(webhook_url, f"✅ No new subdomains for **{target_domain}** (Total: {len(current_subdomains)})")
            
            # Clean up temp files
            for temp_file in [subfinder_output, httpx_output]:
                if temp_file.exists():
                    temp_file.unlink()
        
        except Exception as e:
            logger.error(f"Unexpected error in main loop: {e}", exc_info=True)
            send_to_discord(webhook_url, f"❌ Error occurred: {str(e)[:100]}")
        
        logger.info(f"Sleeping for {interval} seconds...")
        time.sleep(interval)

if __name__ == "__main__":
    try:
        exit(main())
    except KeyboardInterrupt:
        logger.info("\nScript terminated by user")
        print("\n👋 Script stopped by user")
