# GameScout

GameScout is a Discord bot that helps users track game prices and watch for price changes based on customizable criteria. Set watch alerts for games to track discounts, target prices, and even monitor for all-time low prices.

## Features

- **Watch Game Prices**: Monitor prices and get alerts for all-time lows, discounts, and prices below a specified target.
- **Detailed Game Information**: Retrieve lowest prices, historical data, and ongoing deals.
- **Cron-based Scheduling**: Set hourly price checks with cron-style schedules.
- **Supported Platforms**: Works for Windows, MacOS, PS5, Xbox, and Switch.

## Prerequisites

- Python 3.8+
- Docker (optional for containerization)
- A `.env` file with:
  ```env
  DISCORD_TOKEN=<Your Discord Bot Token>
  API_KEY=<Your API Key for Price Data>
  DB_FILE=data/games.db

# Setup and Installation
## Prerequisites
- Bot token is required. Read how to setup it up [here](https://discordpy.readthedocs.io/en/stable/discord.html)
- Isthereanydeal api is also required. Create an account on [isthereanydeal](https://isthereanydeal.com) to get the API Token.
## Manual Setup
### Clone the repository

```bash
git clone https://github.com/aungzm/gamescout
cd gamescout
```

#### Install Dependencies
Make sure you have `pip` installed, then run:
```bash
pip install -r requirements.txt
```
#### Rename the sample-env file to .env
#### Get the [isthereanydeal api](https://isthereanydeal.com/) and paste it in .env
### Run the bot
To start the bot:
```bash
python main.py
```

## Pull from Docker
Create a .env file from sample-env, then in the same repository, pull the docker image. 
```bash
docker run -d --env-file .env --name gamescout aungzm/gamescout:latest
```
Or simply use docker-compose:
```docker-compose.yml
services:
  gamescout:
    image: aungzm/gamescout:latest
    container_name: gamescout-container
    environment:
      - DISCORD_TOKEN=${DISCORD_TOKEN}
      - API_KEY=${API_KEY}
      - DB_FILE=${DB_FILE}
    env_file:
      - .env
    volumes:
      - ./data:/app  # Recommended: To persist sqlite data
    restart: always

```
# Bot Commands

| Command           | Description                                                  | Example Usage                                                    |
|-------------------|--------------------------------------------------------------|------------------------------------------------------------------|
| !add_watch        | Add a game watch with specified criteria.                    | !add_watch "Game Name" "US" "discount" "0 9 * * *" 25 "Windows"  |
| !update_watch     | Update an existing game watch by game ID or name.            | !update_watch "Game Name" "US" "lower than" "0 8 * * *" 30 "PS5" |
| !delete_watch     | Delete a game watch by either game ID or game name.          | !delete_watch "Game Name"                                        |
| !all_games        | List all games currently being watched.                      | !all_games                                                       |
| !get_lowest       | Get the lowest current price for a game.                     | !get_lowest "Game Name" "US" "Windows"                           |
| !list_all         | List all detailed game watch entries.                        | !list_all                                                        |
| !show_commands    | Display all available bot commands with descriptions.        | !show_commands                                                   |
| !get_schedule     | Retrieve the cron schedule for a specific game ID.           | !get_schedule <game_id>                                          |
| !game_info        | Display all stored information about a specific game.        | !game_info "Game Name"                                           |
| !get_best_deal    | Fetch the best current deal for a specified game.            | !get_best_deal "Game Name" "US" "Windows"                        |
| !get_all_time_low | Get the all-time lowest price recorded for a specified game. | !get_all_time_low "Game Name" "US"                               |

# License 
This project is licensed under the MIT License - see the LICENSE file for details.
