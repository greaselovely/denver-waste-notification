#!/usr/bin/env python3
import requests
import json
import datetime
import sys
import os
import re
import argparse
from pathlib import Path

# Config file in local directory
CONFIG_FILE = Path(__file__).parent / "config.json"

def print_config_help():
    """Print help information for finding place_id and service_id"""
    print("\n=== HOW TO FIND YOUR RECOLLECT IDs ===")
    print("To find your place_id and service_id:")
    print("1. Visit your local waste management website that uses ReCollect")
    print("2. Open the collection calendar page")
    print("3. Open browser developer tools (F12 or right-click -> Inspect)")
    print("4. Go to the Network tab")
    print("5. Refresh the page and look for requests to api.recollect.net")
    print("6. Find a request URL like:")
    print("   https://api.recollect.net/api/places/[PLACE_ID]/services/[SERVICE_ID]/events")
    print("")
    print("Alternatively, you can:")
    print("1. Open browser developer tools on your waste collection calendar")
    print("2. In the Console tab, paste and run this JavaScript:")
    print("   console.log(document.querySelector('body').innerHTML.match(/places\\/([0-9A-F-]+)/)[1]);")
    print("   console.log(document.querySelector('body').innerHTML.match(/services\\/([0-9]+)/)[1]);")
    print("")
    print("Another method:")
    print("1. Copy a cURL command from the Network tab in developer tools")
    print("2. Look for the place ID and service ID in the URL")
    print("   They may also appear in the X-Recollect-Place header as: [PLACE_ID]:[SERVICE_ID]")
    print("\nExample values:")
    print("place_id: XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX (a UUID format)")
    print("service_id: XXX (a numeric ID)")
    print("=======================================\n")

def load_config():
    """Load configuration from JSON file or create it if it doesn't exist"""
    default_config = {
        "recollect": {
            "place_id": "",
            "service_id": ""
        },
        "notifications": {
            "pushover": {
                "enabled": False,
                "user_key": "",
                "api_token": ""
            },
            "ntfy": {
                "enabled": False,
                "topic": ""
            }
        }
    }
    
    # Check if config file exists
    if not os.path.exists(CONFIG_FILE):
        # Create default config file
        with open(CONFIG_FILE, 'w') as f:
            json.dump(default_config, f, indent=4)
        print(f"Config file created at {CONFIG_FILE}")
        print("Please edit this file to add your configuration.")
        print_config_help()
        sys.exit(1)
    
    # Load config file
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # Check if required fields are populated
        if not config.get("recollect", {}).get("place_id") or not config.get("recollect", {}).get("service_id"):
            print(f"Missing required ReCollect configuration in {CONFIG_FILE}")
            print_config_help()
            sys.exit(1)
        
        # Check if at least one notification method is enabled and properly configured
        pushover_enabled = config.get("notifications", {}).get("pushover", {}).get("enabled", False)
        ntfy_enabled = config.get("notifications", {}).get("ntfy", {}).get("enabled", False)
        
        if pushover_enabled:
            pushover_config = config.get("notifications", {}).get("pushover", {})
            if not pushover_config.get("user_key") or not pushover_config.get("api_token"):
                print("Pushover is enabled but missing required configuration")
                print("Please update your configuration file.")
                sys.exit(1)
        
        if ntfy_enabled:
            ntfy_config = config.get("notifications", {}).get("ntfy", {})
            if not ntfy_config.get("topic"):
                print("ntfy.sh is enabled but missing required topic")
                print("Please update your configuration file.")
                sys.exit(1)
        
        if not pushover_enabled and not ntfy_enabled:
            print("No notification methods are enabled in the configuration")
            print("Please enable at least one notification method.")
            sys.exit(1)
            
        return config
    except Exception as e:
        print(f"Error loading config file: {e}")
        sys.exit(1)

def extract_ids_from_curl(curl_command):
    """Try to extract place_id and service_id from a curl command"""
    try:
        # Look for place ID in URL
        place_match = re.search(r'places/([0-9A-F-]+)', curl_command)
        service_match = re.search(r'services/([0-9]+)', curl_command)
        
        # Also check X-Recollect-Place header
        header_match = re.search(r'X-Recollect-Place:\s*([0-9A-F-]+):([0-9]+)', curl_command)
        
        place_id = None
        service_id = None
        
        if place_match:
            place_id = place_match.group(1)
        if service_match:
            service_id = service_match.group(1)
            
        if header_match:
            if not place_id:
                place_id = header_match.group(1)
            if not service_id:
                service_id = header_match.group(2)
                
        if place_id and service_id:
            return place_id, service_id
    except:
        pass
    
    return None, None

def extract_ids():
    """Helper function to extract ReCollect IDs from a curl command"""
    print("Please paste a curl command from your waste collection website's network requests.")
    print("(Right-click a request in browser dev tools Network tab -> Copy as cURL)")
    print("Press Enter twice when done pasting:")
    
    curl_lines = []
    while True:
        line = input()
        if not line.strip():
            break
        curl_lines.append(line)
    
    curl_command = " ".join(curl_lines)
    place_id, service_id = extract_ids_from_curl(curl_command)
    
    if place_id and service_id:
        print(f"\nExtracted IDs:")
        print(f"place_id: {place_id}")
        print(f"service_id: {service_id}")
        
        # Check if config file exists and update it
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r') as f:
                    config = json.load(f)
            else:
                config = {
                    "recollect": {},
                    "notifications": {
                        "pushover": {"enabled": False, "user_key": "", "api_token": ""},
                        "ntfy": {"enabled": False, "topic": ""}
                    }
                }
            
            config["recollect"] = {"place_id": place_id, "service_id": service_id}
            
            with open(CONFIG_FILE, 'w') as f:
                json.dump(config, f, indent=4)
                
            print(f"\nUpdated config file with these IDs: {CONFIG_FILE}")
        except Exception as e:
            print(f"Error updating config file: {e}")
    else:
        print("\nCould not extract the IDs from the provided curl command.")
        print("Please make sure you copied a valid curl command from the ReCollect API.")

def get_collection_data(config):
    # Calculate date range (today to one week from now)
    today = datetime.datetime.now().strftime('%Y-%m-%d')
    end_date = (datetime.datetime.now() + datetime.timedelta(days=7)).strftime('%Y-%m-%d')
    
    recollect_config = config.get("recollect", {})
    place_id = recollect_config.get("place_id")
    service_id = recollect_config.get("service_id")
    
    # Construct API URL
    api_url = f"https://api.recollect.net/api/places/{place_id}/services/{service_id}/events"
    params = {
        "nomerge": "1",
        "hide": "reminder_only",
        "after": today,
        "before": end_date,
        "locale": "en-US",
        "include_message": "email"
    }
    
    # Set headers
    headers = {
        "User-Agent": "Mozilla/5.0",
        "Content-Type": "application/json",
        "X-Recollect-Place": f"{place_id}:{service_id}",
        "X-Recollect-Locale": "en-US"
    }
    
    # Make the request
    try:
        response = requests.get(api_url, params=params, headers=headers)
        response.raise_for_status()  # Raise exception for HTTP errors
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching collection data: {e}")
        return None

def get_tomorrow_collections(data):
    if not data or "events" not in data:
        return []
    
    # Calculate tomorrow's date
    tomorrow = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    
    # Find events for tomorrow
    collection_types = []
    for event in data["events"]:
        if event.get("day") == tomorrow:
            for flag in event.get("flags", []):
                collection_type = flag.get("subject")
                if collection_type and collection_type not in collection_types:
                    collection_types.append(collection_type)
    
    return collection_types

def send_pushover_notification(collection_types, config):
    pushover_config = config.get("notifications", {}).get("pushover", {})
    if not pushover_config.get("enabled", False):
        return False
        
    if not collection_types:
        message = "No waste collection scheduled for tomorrow."
    else:
        message = f"Tomorrow's collection includes: {', '.join(collection_types)}."
    
    # Send notification via Pushover
    try:
        response = requests.post(
            "https://api.pushover.net/1/messages.json",
            data={
                "token": pushover_config.get("api_token"),
                "user": pushover_config.get("user_key"),
                "title": "Tomorrow's Waste Collection",
                "message": message
            }
        )
        response.raise_for_status()
        print("Pushover notification sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending Pushover notification: {e}")
        return False

def send_ntfy_notification(collection_types, config):
    ntfy_config = config.get("notifications", {}).get("ntfy", {})
    if not ntfy_config.get("enabled", False):
        return False
        
    if not collection_types:
        message = "No waste collection scheduled for tomorrow."
    else:
        message = f"Tomorrow's collection includes: {', '.join(collection_types)}."
    
    # Send notification via ntfy.sh
    try:
        topic = ntfy_config.get("topic")
        response = requests.post(
            f"https://ntfy.sh/{topic}",
            data=message,
            headers={
                "Title": "Tomorrow's Waste Collection",
                "Priority": "default",
                "Tags": "trash,recycle"
            }
        )
        response.raise_for_status()
        print("ntfy.sh notification sent successfully")
        return True
    except requests.exceptions.RequestException as e:
        print(f"Error sending ntfy.sh notification: {e}")
        return False

def validate_notification_settings(config):
    """Validate that enabled notification methods have required values"""
    notifications = config.get("notifications", {})
    
    # Check Pushover configuration
    pushover = notifications.get("pushover", {})
    if pushover.get("enabled") is True:
        if not pushover.get("user_key") or not pushover.get("api_token"):
            print("Error: Pushover is enabled but missing required keys (user_key or api_token)")
            return False
    
    # Check ntfy configuration
    ntfy = notifications.get("ntfy", {})
    if ntfy.get("enabled") is True:
        if not ntfy.get("topic"):
            print("Error: ntfy.sh is enabled but missing required topic")
            return False
    
    return True

def main():
    # Set up argument parser
    parser = argparse.ArgumentParser(
        description="Trash collection notification script for ReCollect API",
        epilog="For more information about finding your place_id and service_id, use the --config-help option."
    )
    
    # Define mutually exclusive group for main actions
    action_group = parser.add_mutually_exclusive_group()
    action_group.add_argument(
        "--force", 
        action="store_true", 
        help="Run the script regardless of day (normally only runs on Sundays)"
    )
    action_group.add_argument(
        "--extract-ids", 
        action="store_true", 
        help="Tool to extract place_id and service_id from a curl command"
    )
    action_group.add_argument(
        "--config-help", 
        action="store_true", 
        help="Show detailed help about finding your place_id and service_id"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Handle --config-help
    if args.config_help:
        print_config_help()
        return
    
    # Handle --extract-ids
    if args.extract_ids:
        extract_ids()
        return
    
    # Normal run mode
    config = load_config()
    if not validate_notification_settings(config):
        print("Please update your configuration file with the required values.")
        sys.exit(1)
    
    # Check if it's Sunday (weekday 6) unless --force is used
    if not args.force and datetime.datetime.now().weekday() != 6:  # 6 is Sunday
        print("Not running because today is not Sunday")
        print("Use --force to run regardless of day")
        return
    
    # Get collection data
    collection_data = get_collection_data(config)
    if not collection_data:
        print("Failed to retrieve collection data")
        return
    
    # Parse tomorrow's collections
    tomorrow_collections = get_tomorrow_collections(collection_data)
    
    # Send notifications
    notification_sent = False
    
    # Send via Pushover if enabled
    pushover_success = send_pushover_notification(tomorrow_collections, config)
    notification_sent = notification_sent or pushover_success
    
    # Send via ntfy.sh if enabled
    ntfy_success = send_ntfy_notification(tomorrow_collections, config)
    notification_sent = notification_sent or ntfy_success
    
    if not notification_sent:
        print("Warning: No notifications were sent successfully")

if __name__ == "__main__":
    main()
