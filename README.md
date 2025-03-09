# Trash Collection Notification Script

A Python script that sends notifications about upcoming trash/recycling/compost collection directly to your phone or device. -Should- work with any city or municipality that uses the ReCollect waste management platform for their collection schedules.  I have only tested in Denver.

## Features

- Checks your next day's waste collection schedule
- Sends notifications via Pushover and/or ntfy.sh
- Runs automatically on Sundays to notify about Monday collections
- Supports extracting ReCollect IDs from your local waste management website
- Simple setup with a JSON configuration file

## Requirements

- Python 3.6 or later
- `requests` library (`pip install requests`)
- A waste collection service that uses the ReCollect platform
- At least one notification service:
  - [Pushover](https://pushover.net/) account and app (paid service, one-time fee)
  - [ntfy.sh](https://ntfy.sh/) (free service)

## Configuration

The script uses a `config.json` file in the same directory. When you run the script for the first time, it will create a default configuration file.

### Finding Your ReCollect IDs

The script needs your place_id and service_id to connect to the ReCollect API. Use the built-in tool to extract these IDs:

```bash
./main.py --extract-ids
```

Follow the instructions to paste a curl command from your local waste collection website's network requests. The script will extract the IDs and update your configuration file.

### Manual Configuration

You can also edit the configuration file manually:

```json
{
    "recollect": {
        "place_id": "YOUR-PLACE-ID-HERE",
        "service_id": "YOUR-SERVICE-ID-HERE"
    },
    "notifications": {
        "pushover": {
            "enabled": true,
            "user_key": "YOUR-PUSHOVER-USER-KEY",
            "api_token": "YOUR-PUSHOVER-API-TOKEN"
        },
        "ntfy": {
            "enabled": true,
            "topic": "YOUR-NTFY-TOPIC"
        }
    }
}
```

Replace the placeholder values with your actual information:

1. For **Pushover**:
   - Set `enabled` to `true`
   - Get your user key from your Pushover account page
   - Create an application at Pushover to get an API token

2. For **ntfy.sh**:
   - Set `enabled` to `true`
   - Choose a unique topic name (this becomes part of the URL)

## Usage

### Basic Usage

Run the script on Sundays to get a notification about Monday's collection:

```bash
./main.py
```

### Force Run

Run the script regardless of the day of the week:

```bash
./main.py --force
```

### Help

Display help information:

```bash
./main.py --help
```

Get detailed help about finding your ReCollect IDs:

```bash
./main.py --config-help
```

## Automation

You can set up a cron job to run the script automatically every Sunday:

```bash
# Edit crontab
crontab -e

# Add this line to run every Sunday at 2:00 PM
0 14 * * 0 /path/to/main.py
```

## Troubleshooting

### Notification Not Sent

Check your configuration file to ensure:
- Your place_id and service_id are correct
- At least one notification method is enabled and properly configured
- For Pushover: user_key and api_token are set
- For ntfy.sh: topic is set

### Data Not Found

If the script can't find your collection data:
- Verify your place_id and service_id
- Check if your waste collection service uses ReCollect
- Try running with `--extract-ids` again to get updated IDs

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- [ReCollect](https://recollect.net/) for providing the waste collection API
- [Pushover](https://pushover.net/) for the notification service
- [ntfy.sh](https://ntfy.sh/) for the alternative notification service