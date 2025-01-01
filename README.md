# Subdomain Notifier using Discord

## Overview
The Subdomain Notifier is a tool that helps monitor subdomains of a given website. It automatically scans for changes and updates in the subdomains every 2 hours and sends notifications via a Discord webhook.

## Features
- Automatically scans the provided website for subdomains.
- Notifies a Discord channel using a webhook whenever changes are detected.
- Simple to set up and use.

## Prerequisites
- A Discord server where you can create a webhook.
- Python installed on your system.
- Basic knowledge of running Python scripts.

## Installation
1. Clone this repository to your local machine:
   ```bash
   git clone <repository_url>
   cd <repository_folder>
   ```
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage
1. **Set up your Discord webhook:**
   - Go to your Discord server settings.
   - Navigate to **Integrations > Webhooks** and create a new webhook.
   - Copy the webhook URL.

2. **Run the script:**
   - Open the `config.json` file (if provided) or directly input the webhook URL when prompted.
   - Start the script:
     ```bash
     python subdomain_notifier.py
     ```

3. **Provide the target website:**
   - When prompted, enter the website you want to scan for subdomains.
   
4. The tool will automatically scan the website every 2 hours and notify the provided Discord webhook of any updates.

## Configuration
If the script supports a configuration file (e.g., `config.json`), you can pre-set values to avoid inputting them manually:
```json
{
  "webhook_url": "<your_discord_webhook_url>",
  "scan_interval": 7200
}
```

## Example Notification
A typical Discord notification will look like this:
```
New subdomains detected for example.com:
- sub1.example.com
- sub2.example.com
```

## Troubleshooting
- Ensure the webhook URL is correctly set and active.
- Check your internet connection if the script cannot reach the target website.
- Ensure Python dependencies are installed using `pip install -r requirements.txt`.

## Contributing
Feel free to submit issues or pull requests to improve this tool. Contributions are welcome!

## License
This project is licensed under the MIT License.
