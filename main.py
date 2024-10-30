from datetime import datetime
from typing import List, Dict, Optional

import asyncio
import discord
from discord.ext import commands, tasks
import os
from dotenv import load_dotenv
import logging
from cron_descriptor import get_description

# Configure logging
logging.basicConfig(level=logging.INFO)
from api import get_all_time_low_price, get_current_lowest_price, get_game_id, current_best_deal, get_original_price
from compare import percentage_compare, is_below_target_price, all_time_low_compare
from dbdriver import retrieve_current_hour_watches, add_game_watch, retrieve_all_watches, \
    delete_game_watch_by_name, delete_game_watch_by_id, update_game_watch, retrieve_game_names, \
    retrieve_all_info, init_db, retrieve_schedule_for_game, list_game_info

# Load environment variables
DB_FILE = os.getenv("DB_FILE")
TOKEN = os.getenv("DISCORD_TOKEN")
API_KEY = os.getenv("API_KEY")

# Set up intents and bot
intents = discord.Intents.default()
intents.message_content = True  # Required for reading message content in certain commands
bot = commands.Bot(command_prefix="!", intents=intents)


# Commands
@bot.event
async def on_ready():
    print(f"Logged in as {bot.user} (ID: {bot.user.id})")
    print("------")
    init_db()


@bot.command(name="add_watch")
async def add_watch(ctx, game_name: str, country: str, watch_type: str, schedule: str,
                    target_value: Optional[str] = None, platform: str = "Windows"):
    """
    Adds a new game watch.
    Usage: !add_watch <game_name> <country> <watch_type> <schedule> [target_value] [platform]
    """
    game_id = get_game_id(game_name)

    if game_id is None:
        await ctx.send("Could not find game with such name.")
        return

    # Convert target_value to float if provided
    try:
        target_value = float(target_value) if target_value else None
    except ValueError:
        await ctx.send("Invalid input: target_value must be a valid number.")
        return

    # Normalize and validate watch_type
    normalized_watch_type = watch_type.strip().lower()
    allowed_watch_types = ['all time low', 'lower than', 'discount']
    if normalized_watch_type not in allowed_watch_types:
        await ctx.send("Not a valid watch type. Allowed types are: **all time low**, **lower than**, **discount**.")
        return

    # Validate platform
    allowed_platforms = ['Windows', 'MacOS', 'PS5', 'Xbox', 'Switch']
    if platform not in allowed_platforms:
        await ctx.send(f"Invalid platform '{platform}'. Allowed platforms are: {', '.join(allowed_platforms)}.")
        return

    # Add the game watch
    try:
        add_game_watch(
            game_id=game_id,
            game_name=game_name,
            country=country,
            price_watch_type=normalized_watch_type,
            schedule=schedule,
            target_value=target_value,
            platform=platform
        )
        await ctx.send(
            f"Added watch for {game_name} with type '{watch_type}' on {platform} scheduled at {get_description(schedule)}!"
        )
    except ValueError as e:
        await ctx.send(str(e))
    except FileExistsError as e:
        await ctx.send(str(e))


@bot.command(name="update_watch")
async def update_watch(ctx, game_name: str, country: str, watch_type: str = None, schedule: str = None,
                       target_value: Optional[float] = None, platform: Optional[str] = None):
    """
    Updates an existing game watch by game ID.
    Usage: !update_watch <game_name> <country> <watch_type> <schedule> [target_value] [platform]
    """
    # Fetch the game ID based on game name
    game_id = get_game_id(game_name)
    if game_id is None:
        await ctx.send("Could not find game with such name.")
        return

    # Convert target_value to float if provided
    try:
        target_value = float(target_value) if target_value is not None else None
    except ValueError:
        await ctx.send("Invalid input: target_value must be a valid number.")
        return

    # Validate platform if provided
    allowed_platforms = ['Windows', 'MacOS', 'PS5', 'Xbox', 'Switch']
    if platform and platform not in allowed_platforms:
        await ctx.send(f"Invalid platform '{platform}'. Allowed platforms are: {', '.join(allowed_platforms)}.")
        return

    # Call the update function
    try:
        update_game_watch(
            game_id=game_id,
            game_name=game_name,
            price_watch_type=watch_type,
            cron_schedule=schedule,
            country=country,
            target_value=target_value,
            platform=platform
        )
        await ctx.send(f"Updated watch for {game_name}.")
    except ValueError as e:
        await ctx.send(f"Update failed: {str(e)}")


@bot.command(name="delete_watch")
async def delete_watch(ctx, identifier: str):
    """
    Deletes a game watch by either game ID or game name.
    Usage: !delete_watch <game_id or game_name>
    """
    try:
        if identifier.isdigit():
            delete_game_watch_by_id(identifier)
            await ctx.send(f"Deleted watch for game ID {identifier}.")
        else:
            delete_game_watch_by_name(identifier)
            await ctx.send(f"Deleted watch for game name '{identifier}'.")
    except Exception as e:
        await ctx.send(f"Failed to delete watch: {e}")


@bot.command(name="all_games")
async def list_all_game_watched(ctx):
    """
    Lists all unique game names being watched.

    :param ctx: Context of the command
    """
    game_names = retrieve_game_names()
    if game_names:
        response = "\n".join(game_names)
    else:
        response = "No games are currently being watched."
    await ctx.send(response)


@bot.command(name="get_lowest")
async def get_lowest_now(ctx, name: str, country: str, platform: str):
    """
    Fetch and display the lowest game price from IsThereAnyDeal API for a given game name, country, and platform.
    """
    # Get the current lowest price data
    price_dict = get_current_lowest_price(name, country, platform)

    # Check if price data exists
    if not price_dict:
        await ctx.send(f"No price data found for {name} in {country} on {platform}.")
        return

    # Format the message to make it readable
    message = (
        f"**Lowest Price for {name}**\n"
        f"**Platform**: {platform}\n"
        f"**Country**: {country}\n"
        f"**Current Price**: {price_dict['current_price']} {price_dict['currency']}\n"
    )

    # Send the formatted message to Discord
    await ctx.send(message)


@bot.command(name="get_all_time_low")
async def get_all_time_low_now(ctx, name: str, country: str):
    """

    :param ctx:
    :param name:
    :param country:
    :param platform:
    :return:
    """
    price_dict = get_all_time_low_price(name, country)
    await ctx.send(f"{price_dict.get('price')} {price_dict.get('currency')}")


@bot.command(name="get_best_deal")
async def get_best_deal_now(ctx, name: str, country: str, platform: str):
    """

    :param ctx:
    :param name:
    :param country:
    :param platform:
    :return:
    """
    # Fetch the deals
    deals = current_best_deal(name, country, platform)

    # Check if deals exist
    if not deals:
        await ctx.send(f"No deals found for {name} in {country} on {platform}.")
        return

    # Format each deal for better readability
    formatted_deals = []
    for deal in deals:
        formatted_deals.append(
            f"**Store**: {deal['store_name']}\n"
            f"**Currency**: {deal['currency']}\n"
            f"**Current Price**: {deal['current_price']}\n"
            f"**Original Price**: {deal['original_price']}\n"
            f"**URL**: {deal['url']}\n"
            "-----------------------------"
        )

    # Join all formatted deals into a single message
    message = "\n\n".join(formatted_deals)

    # Send the formatted message to Discord
    await ctx.send(message)


@bot.command(name="list_all")
async def list_all_info(ctx):
    """
    Lists all detailed information for each game watch entry.

    :param ctx: Context of the command
    """
    game_information = retrieve_all_info()
    if game_information:
        response = "\n\n".join([
            f"**Game Watch Entry #{info['id']}**\n"
            f"**Game Name:** {info['game_name']}\n"
            f"**Watch Type:** {info['price_watch_type'].capitalize()}\n"
            f"**Schedule:** {info['cron_schedule']}\n"
            f"**Country:** {info['country']}\n"
            f"**Max Price:** {info.get('max_price', 'N/A')}\n"
            f"**Discount Percentage:** {info.get('discount_percentage', 'N/A')}\n"
            f"------------------------"
            for info in game_information
        ])
    else:
        response = "No game watch entries found."
    await ctx.send(response)


@bot.command(name="show_commands")
async def show_commands(ctx):
    """
    Lists all available commands with descriptions.

    Usage: !show_commands
    """
    response = "**Available Commands:**\n\n"

    for command in bot.commands:
        response += f"**!{command.name}** - {command.help}\n\n"

    await ctx.send(response)


@bot.command(name="get_schedule")
async def get_schedule(ctx, game_id: str):
    """
    Retrieves and displays the schedule for a specific game.
    Usage: !get_schedule <game_id>
    """
    schedule = retrieve_schedule_for_game(game_id)
    if schedule:
        await ctx.send(f"The schedule for game ID {game_id} is: {schedule}")
    else:
        await ctx.send(f"No schedule found for {game_id}.")


@bot.command(name="game_info")
async def game_info(ctx, game_name: str):
    """
    Retrieves and displays all information about a specific game.
    Usage: !game_info <game_name>
    """
    info = list_game_info(game_name)
    if info:
        # Format and send each game's info in a readable format
        for game in info:
            details = "\n".join([f"**{key}**: {value}" for key, value in game.items()])
            await ctx.send(f"**Game Information for {game_name}**:\n{details}")
    else:
        await ctx.send(f"No information found for game '{game_name}'.")


@bot.command(name="start_watch")
async def start_check_price_watches(ctx):
    # Calculate the delay to the next full hour
    now = datetime.now()
    delay = (60 - now.minute) * 60 - now.second  # Delay until the next full hour

    await asyncio.sleep(delay)
    check_price_watches.start(ctx)


@tasks.loop(hours=1)
async def check_price_watches(ctx):
    """
    Periodically checks for watches scheduled for the current hour.
    """
    current_hour_watches = retrieve_current_hour_watches()

    for game_id, game_name, country, watch_type, target_value, platform in current_hour_watches:
        try:
            # Get the current lowest price
            current_price_data = get_current_lowest_price(game_id, country, platform).get("current_price")
            currency = current_price_data.get("currency")
            current_price = current_price_data.get("current_price")
            original_price = get_original_price(game_name, country, platform).get("original_price")

            if not current_price:
                print(f"No current prices found for {game_name}.")
                raise ValueError("Can't find current prices")
            if not original_price:
                raise ValueError("Can't find original price")

            # Determine action based on watch_type
            if watch_type == "all time low":
                all_time_low = get_all_time_low_price(game_id, country).get("price")
                if all_time_low and all_time_low_compare(current_price, all_time_low):
                    print(
                        f"{game_name} is at its all-time low price of {all_time_low} {currency}!")
                    print(get_lowest_now(game_id, country))

            elif watch_type == "discount":
                if percentage_compare(current_price, original_price, target_value):
                    await ctx.send(
                        f"{game_name} is available at a {target_value}% discount! Current price: {current_price}.")
                    await ctx.send(get_best_deal_now(game_name, country, platform))

            elif watch_type == "lower than":
                if target_value and is_below_target_price(current_price, target_value):
                    await ctx.send(
                        f"{game_name} is now below your target price of {target_value}. Current price: {current_price}.")
                    await ctx.send(get_lowest_now(game_id, country))

        except Exception as e:
            print(f"Error checking price for {game_name}: {e}")


# Error handler for commands
@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Missing arguments for this command.")
    elif isinstance(error, commands.CommandNotFound):
        await ctx.send("Unknown command.")
    else:
        await ctx.send(f"An error occurred {error}")


# Run bot
if __name__ == "__main__":
    bot.run(TOKEN)
