import sqlite3
from typing import List, Tuple, Optional, Dict, Any
from dotenv import load_dotenv
import os
from cron_descriptor import get_description
from croniter import croniter
from datetime import datetime, timedelta

DB_FILE = os.getenv("DB_FILE")


def init_db():
    """
    Initialize the database and create the game_watch table if it doesn't exist.
    """

    load_dotenv()
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Create the game_watch table with a single target_value field
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS game_watch (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        game_id TEXT NOT NULL,
        game_name TEXT NOT NULL,
        price_watch_type TEXT NOT NULL,
        cron_schedule TEXT NOT NULL, 
        country TEXT NOT NULL DEFAULT "US",
        target_value REAL DEFAULT NULL,
        platform TEXT 
        );
    ''')

    conn.commit()
    conn.close()


def add_game_watch(game_id: str, game_name: str, price_watch_type: str, schedule: str,
                   country: str = "US", target_value: Optional[float] = None, platform: str = "Windows") -> None:
    """
    Adds a game watch entry to the database with validation on watch type and cron schedule.

    Args:
        game_id (str): The unique ID of the game.
        game_name (str): The name of the game.
        price_watch_type (str): The type of price watch (e.g., 'all time low', 'lower than', 'discount').
        schedule (str): The cron schedule string (e.g., '*/5 * * * *').
        country (str): The country code for the watch, default is "US".
        target_value (Optional[float]): Represents either max_price or discount_percentage, depending on `price_watch_type`
        platform (Optional[str]): What platform is the game on MacOS, PS5, Windows etc. Default is Windows
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if game watch already exists
    cursor.execute('SELECT * FROM game_watch WHERE game_name = ?', (game_name,))
    game_exists = cursor.fetchone()
    if game_exists:
        raise FileExistsError(
            f"The entry with game name '{game_name}' already exists. Please delete or use update_game function.")

    # Validate watch type
    allowed_watch_types = ['all time low', 'lower than', 'discount']
    if price_watch_type not in allowed_watch_types:
        raise ValueError("Not a valid watch type. Allowed types are: 'all time low', 'lower than', 'discount'.")

    # Validate target_value based on watch type
    if price_watch_type == "lower than" and target_value is None:
        raise ValueError("target_value is required as max_price for 'lower than' watch type.")
    if price_watch_type == "discount" and target_value is None:
        raise ValueError("target_value is required as discount_percentage for 'discount' watch type.")
    if price_watch_type == "all time low" and target_value is not None:
        raise ValueError("'all time low' watch type should not have a target_value.")

    # Validate cron schedule and generate a description
    try:
        description = get_description(schedule)
        if description is None:
            raise ValueError("Invalid cron schedule.")
    except Exception as e:
        raise ValueError(f"Invalid cron schedule: {schedule}. Error: {e}")

    # Insert the game watch into the database
    cursor.execute('''
        INSERT INTO game_watch (game_id, game_name, price_watch_type, cron_schedule, country, target_value, platform)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (game_id, game_name, price_watch_type, schedule, country, target_value, platform))

    conn.commit()
    conn.close()


def update_game_watch(
        game_id: str,
        game_name: Optional[str] = None,
        price_watch_type: Optional[str] = None,
        cron_schedule: Optional[str] = None,
        country: Optional[str] = None,
        target_value: Optional[float] = None,
        platform: Optional[str] = None
) -> None:
    """
    Updates a game watch entry in the database based on the provided game ID and fields.

    Args:
        game_id (str): The unique ID of the game.
        game_name (Optional[str]): The new name of the game.
        price_watch_type (Optional[str]): The new type of price watch ('all time low', 'lower than', 'discount').
        cron_schedule (Optional[str]): The new schedule for checking the price.
        country (Optional[str]): The new country code for the watch.
        target_value (Optional[float]): Represents either max_price or discount_percentage, depending on `price_watch_type`.
        platform (Optional[str]): The platform for the game (e.g., 'Windows', 'MacOS', 'PS5').
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Check if the game watch entry exists using game_id
    cursor.execute('SELECT * FROM game_watch WHERE game_id = ?', (game_id,))
    if not cursor.fetchone():
        raise FileNotFoundError(f"No game watch entry found with ID {game_id}")

    # Allowed watch types
    allowed_watch_types = ['all time low', 'lower than', 'discount']
    if price_watch_type and price_watch_type not in allowed_watch_types:
        raise ValueError(
            f"Invalid price_watch_type '{price_watch_type}'. Allowed types are: {', '.join(allowed_watch_types)}.")

    # Allowed platforms (optional validation)
    allowed_platforms = ['Windows', 'MacOS', 'PS5', 'Xbox', 'Switch']
    if platform and platform not in allowed_platforms:
        raise ValueError(f"Invalid platform '{platform}'. Allowed platforms are: {', '.join(allowed_platforms)}.")

    # Validate target_value based on watch type
    if price_watch_type == "lower than" and target_value is None:
        raise ValueError("target_value is required as max_price for 'lower than' watch type.")
    if price_watch_type == "discount" and target_value is None:
        raise ValueError("target_value is required as discount_percentage for 'discount' watch type.")
    if price_watch_type == "all time low" and target_value is not None:
        raise ValueError("'all time low' watch type should not have a target_value.")

    # Prepare fields to update based on provided values
    fields_to_update: Dict[str, Any] = {}
    if game_name:
        fields_to_update["game_name"] = game_name
    if price_watch_type:
        fields_to_update["price_watch_type"] = price_watch_type
    if cron_schedule:
        fields_to_update["cron_schedule"] = cron_schedule
    if country:
        fields_to_update["country"] = country
    if target_value is not None:
        fields_to_update["target_value"] = target_value
    if platform:
        fields_to_update["platform"] = platform

    # Build the update query dynamically
    set_clause = ", ".join([f"{field} = ?" for field in fields_to_update.keys()])
    values = list(fields_to_update.values()) + [game_id]  # Values for placeholders

    # Execute the update query with `game_id` in the WHERE clause
    cursor.execute(f'''
        UPDATE game_watch
        SET {set_clause}
        WHERE game_id = ?
    ''', values)

    conn.commit()
    conn.close()



def retrieve_game_names() -> List[str]:
    """
    Retrieves a list of all game names being watched.

    Returns:
        List[str]: A list of game names.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT DISTINCT game_name FROM game_watch')
    game_names = [row[0] for row in cursor.fetchall()]

    conn.close()
    return game_names


def list_game_info(game_name: str) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Retrieve everything about the game
    cursor.execute('SELECT * FROM game_watch WHERE game_name = ?', (game_name,))
    rows = cursor.fetchall()

    # Get column names
    column_names = [description[0] for description in cursor.description]

    # Map each row to a dictionary
    game_info = [dict(zip(column_names, row)) for row in rows]

    conn.close()
    return game_info


def retrieve_all_info() -> List[Dict[str, str]]:
    """
    Retrieves all information for each game watch entry.

    Returns:
        List[Dict[str, str]]: A list of dictionaries, each containing all details of a game watch entry.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Retrieve all columns from the game_watch table
    cursor.execute('SELECT * FROM game_watch')
    columns = [description[0] for description in cursor.description]  # Get column names
    game_watches = [dict(zip(columns, row)) for row in cursor.fetchall()]  # Combine column names with row data

    conn.close()
    return game_watches


def retrieve_schedule_for_game(game_id: str) -> Optional[str]:
    """
    Retrieves the schedule for a specific game by its ID.

    Args:
        game_id (str): The unique ID of the game.

    Returns:
        Optional[str]: The schedule for the game, or None if the game isn't found.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT cron_schedule FROM game_watch WHERE game_id = ?', (game_id,))
    result = cursor.fetchone()

    conn.close()
    return result[0] if result else None


def delete_game_watch_by_id(game_id: str) -> None:
    """
    Deletes a game watch entry from the database by its game ID.

    Args:
        game_id (str): The unique ID of the game to delete.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('DELETE FROM game_watch WHERE game_id = ?', (game_id,))

    conn.commit()
    conn.close()


def delete_game_watch_by_name(game_name: str) -> None:
    """
    Deletes a game watch entry from the database by its game name.
    :param game_name:
    :return:
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM game_watch WHERE game_name = ?', (game_name,))
    conn.commit()
    conn.close()


def update_schedule_for_game(game_id: str, new_schedule: str) -> None:
    """
    Updates the schedule for a specific game.

    Args:
        game_id (str): The unique ID of the game.
        new_schedule (str): The new schedule (e.g., 'weekly', 'daily').
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('''
        UPDATE game_watch
        SET cron_schedule = ?
        WHERE game_id = ?
    ''', (new_schedule, game_id))

    conn.commit()
    conn.close()


def retrieve_all_watches() -> List[Tuple[str, str, str, str, str]]:
    """
    Retrieves all game watches in the database.

    Returns:
        List[Tuple[str, str, str, str, str]]: A list of all game watch entries including game ID, name, type, user, and schedule.
    """
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute('SELECT game_id, game_name, price_watch_type, cron_schedule FROM game_watch')
    watches = cursor.fetchall()

    conn.close()
    return watches


def retrieve_current_hour_watches() -> List[Tuple[str, str, str, str, str, str]]:
    """
    Retrieves game watches scheduled for the current hour.

    Returns:
        List[Tuple[str, str, str]]: A list of tuples containing game ID, game name, and watch type for each scheduled game.
    """
    current_time = datetime.now()
    current_hour = current_time.replace(minute=0, second=0, microsecond=0)
    previous_hour = current_hour - timedelta(hours=1)  # Include the previous hour for matching
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    # Fetch all entries with their cron schedule
    cursor.execute('SELECT game_id, game_name, country, price_watch_type, cron_schedule, target_value, platform FROM '
                   'game_watch')
    games = []

    for row in cursor.fetchall():
        game_id, game_name, country, price_watch_type, cron_schedule, target_value, platform = row

        # Use croniter to check if the next or previous run falls within the current hour
        cron = croniter(cron_schedule, previous_hour)
        next_run = cron.get_next(datetime)

        # Check if the next or previous run falls within the current hour
        if next_run.hour == current_hour.hour and next_run.date() == current_hour.date():
            games.append((game_id, game_name, country, price_watch_type, target_value, platform))

    conn.close()
    return games
