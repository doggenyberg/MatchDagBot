# MatchDagBot

## Overview

This Discord bot was created for me and my friends who support either AIK or Hammarby IF and want to stay updated on when the next game is. The bot uses data from an external football API to provide notifications about upcoming games for our favorite teams.

- **Game Notifications**: The bot automatically sends notifications to the channels you’ve set up one day before a game takes place. This ensures we get a reminder about the upcoming game and don’t miss any important gamedays.

By using this tool, we can easily stay informed and never miss a gameday.

**Note:** The bot operates in Swedish. To customize the language or modify messages, you can update the `ctx.send()` functions in the code.

## Features

- **Set Notification Channel**: Configure a channel to receive game notifications.
- **Remove Notification Channel**: Disable notifications for the current channel.
- **Get Next Game Info**: Retrieve information about the next game for AIK or Hammarby.
- **Automated Updates**: The bot sends automatic notifications to your designated channels one day before an upcoming game.

## Setup

### Prerequisites

1. **Python 3.7+**: Ensure Python 3.7 or higher is installed on your system.
2. **Dependencies**: Install required Python libraries using `pip`:
   ```bash
   pip install -r requirements.txt
   ```

### Configuration
1. **Create a settings.py File**  
   Add your Discord API token and football API key to a settings.py file.<br>
   ```python
   # settings.py
   DISCORD_API_SECRET = 'your_discord_api_token_here'
   FOOTBALL_API_SECRET = 'your_football_api_key_here'
   ```
   <br>
3. **Setup JSON Files**  
   Ensure the following files are in place:<br>
-  `channels.json`: Stores channel IDs for notifications.
-  `global_rounds.json`: Stores global game round data.  
  
   These files will be automatically created and updated by the bot if they don't exist.<br>
   <br>
3. **Run the bot**  
   Start the bot by running the following command:
   ```bash
   python main.py
   ```
   Ensure the main.py file includes the code provided in the project.
   <br>
## Commands
- `!mdb help`: Shows all the commands and information about the bot. <br>
  ![image](https://github.com/user-attachments/assets/f21094ef-936e-412a-8eb1-0ceca3f963f8) <br><br>
- `!mdb set_channel`: Sets the current channel for receiving game notifications. <br>
  ![image](https://github.com/user-attachments/assets/4a7c9e6b-a1f8-412e-9645-5f0269f20565) <br><br>
- `!mdb remove_channel`: Removes the current channel from receiving game notifications. <br>
  ![image](https://github.com/user-attachments/assets/f0c73f3c-bd6f-48ab-bcf8-a7edc92bca51) <br><br>
- `!mdb next_game <team_name>`: Shows information about the next game for the specified team. Replace <team_name> with AIK or Hammarby. <br>
  ![image](https://github.com/user-attachments/assets/9c534a95-4a1c-4013-a1d7-a18e49131cfb) <br><br>

## Logging
Logs are generated for bot events and errors. By default, logs are output to the console. You can modify the logging configuration in the code if needed.

## Troubleshooting
- **Bot not sending updates**: Ensure the bot has permission to send messages in the configured channels. Verify that the football API is returning valid data.
- **Command Errors**: Ensure commands are used correctly and the bot has appropriate permissions.
