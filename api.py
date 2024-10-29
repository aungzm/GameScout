from collections import Counter
from typing import List, Dict, Optional
import requests
import os
import logging
from dotenv import load_dotenv
import pycountry

load_dotenv()
API_KEY: Optional[str] = os.getenv('API_KEY')
if API_KEY is None:
    raise Exception("API_KEY not found in .env file")


def get_game_id(game_name: str) -> Dict[str, Optional[str]]:
    """
    Given a list of game names, returns a dictionary with game names and their corresponding IDs.

    Args:
        game_names (List[str]): List of game titles as strings.

    Returns:
        Dict[str, Optional[str]]: A dictionary where keys are game names and values are game IDs (or None if not found).
    """
    url: str = "https://api.isthereanydeal.com/lookup/id/title/v1"

    headers: Dict[str, str] = {
        'Content-Type': 'application/json'
    }
    params: Dict[str, str] = {
        'key': API_KEY
    }

    # The body needs to be a JSON array of game names
    body = [game_name]

    # Send POST request
    response = requests.post(url, params=params, json=body, headers=headers)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"API to get Game IDs request failed with status code {response.status_code}: {response.text}")
    data = response.json()
    # Return the JSON response, which maps game names to their IDs
    return data.get(game_name)


def get_game_info(game_id: str) -> Dict:
    """
    Fetch game information from IsThereAnyDeal API using the game ID.

    Args:
        game_id (str): The unique ID of the game.

    Returns:
        Dict: A dictionary containing game information.
    """
    url: str = "https://api.isthereanydeal.com/games/info/v2"

    # Parameters to be sent with the request
    params: Dict[str, str] = {
        'key': API_KEY,  # API key from .env
        'id': game_id  # Game ID to look up
    }

    # Send GET request
    response = requests.get(url, params=params)

    # Check if the request was successful
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Return the JSON response containing game information
    return response.json()


def get_original_price(game_name: str, country: str, platform: str) -> Dict:
    url = "https://api.isthereanydeal.com/games/prices/v3"
    game_id = get_game_id(game_name)
    if not API_KEY:
        raise Exception("API Key is missing. Check your .env file or environment configuration")

    # Set up the query parameters
    params = {
        "key": API_KEY,
        "country": country
    }

    # The body of the POST request contains the game_id as a list
    body = [game_id]
    headers = {"Content-Type": "application/json"}

    logging.info("Request URL: %s", url)
    logging.info("Request Params: %s", params)
    logging.info("Request Headers: %s", headers)
    logging.info("Request Body: %s", body)

    response = requests.post(url, params=params, json=body, headers=headers)

    # Raise an error if the request failed
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    data = response.json()

    # Access nested game data within the response
    if isinstance(data, list) and data:
        game_data = data[0]  # Access the first dictionary in the list
    else:
        raise Exception(f"No data found for the game '{game_id}' in country '{country}'.")

    # Collect all regular prices from the deals
    regular_prices = []
    currency = game_data.get("deals", [])[0]["price"]["currency"]
    for deal in game_data.get("deals", []):
        regular_price = deal.get("regular", {}).get("amount")
        if regular_price is not None:
            regular_prices.append(regular_price)
    # Calculate the mode (most common value) as the original price
    if not regular_prices:
        raise Exception("No regular prices found in the deals.")

    original_price = Counter(regular_prices).most_common(1)[0][0]
    logging.info(f"Most common original price: {original_price}")
    return {"original_price": original_price, "currency": currency}


def current_best_deal(game_name: str, country: str, platform: str) -> List[Dict]:
    url = "https://api.isthereanydeal.com/games/prices/v3"
    game_id = get_game_id(game_name)
    if not API_KEY:
        raise Exception("API key is missing. Check your .env file or environment configuration.")
    else:
        # Set up the query parameters
        params = {
            "key": API_KEY,
            "country": country
        }

        # The body of the POST request contains the game_id as a list
        body = [
            game_id
        ]

        headers = {
            "Content-Type": "application/json"
        }

        logging.info("Request URL: %s", url)
        logging.info("Request Params: %s", params)
        logging.info("Request Headers: %s", headers)
        logging.info("Request Body: %s", body)

        # Send POST request to the API
        response = requests.post(url, params=params, json=body, headers=headers)

        # Raise an error if the request failed
        if response.status_code != 200:
            raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

        # Parse the response JSON
        data = response.json()

        # Ensure that the data is a list and access the first element
        if isinstance(data, list) and data:
            game_data = data[0]  # Access the first dictionary in the list
        else:
            raise Exception(f"No data found for the game '{game_id}' in country '{country}'.")

        # Filter deals based on the platform
        filtered_deals = []
        deals = game_data.get("deals", [])

        # Get the minimum price for the specified platform
        min_price = None
        for deal in deals:
            platforms = [p["name"] for p in deal["platforms"]]
            if platform in platforms:
                price = deal["price"]["amount"]
                if min_price is None or price < min_price:
                    min_price = price

        # Collect all deals that match the minimum price and return only relevant data
        result = []
        for deal in deals:
            platforms = [p["name"] for p in deal["platforms"]]
            if platform in platforms and deal["price"]["amount"] == min_price:
                result.append({
                    "store_name": deal["shop"]["name"],
                    "currency": deal["price"]["currency"],
                    "current_price": deal["price"]["amount"],
                    "original_price": deal["regular"]["amount"],
                    "url": deal["url"],
                    "timestamp": deal["timestamp"]
                })

        # Return the filtered list of stores with relevant data
        return result


def get_current_lowest_price(game_id: str, country: str, platform: str) -> Dict:
    """
    Uses get_current_best_deals to get the current_lowerst price
    """
    best_deals = current_best_deal(game_id, country, platform)
    lowest = {"current_price": best_deals[0].get("current_price"), "currency": best_deals[0].get("currency")}
    return lowest


def get_all_time_low_price(game_name: str, country: str) -> Dict:
    """
    Fetch the all-time lowest game price from IsThereAnyDeal API for a given game ID and country.

    Args:
        game_id (str): The unique ID of the game.
        country (str): Two-letter country code.

    Returns:
        Dict: A dictionary containing the all-time lowest price information, if available.
    """
    if not (is_valid_iso2_country_code(country)):
        return ValueError
    game_id = get_game_id(game_name)
    url = "https://api.isthereanydeal.com/games/prices/v3"

    # Set up the query parameters
    params = {
        "key": API_KEY,
        "country": country
    }

    body = [
        game_id
    ]

    headers = {
        "Content-Type": "application/json"
    }
    # Send POST request to the API
    response = requests.post(url, params=params, json=body, headers=headers)

    # Raise an error if the request failed
    if response.status_code != 200:
        raise Exception(f"API request failed with status code {response.status_code}: {response.text}")

    # Parse the response JSON
    data = response.json()
    if isinstance(data, list) and data:
        game_data = data[0]  # Access the first dictionary in the list
    else:
        raise Exception(f"No data found for the game '{game_id}' in country '{country}'.")

        # Extract the all-time low price from historyLow
    history_low = game_data.get("historyLow", {}).get("all", {})

    if history_low:
        return {
            "price": history_low.get("amount"),
            "currency": history_low.get("currency")
        }

    # If no all-time low price found, raise an exception
    raise Exception(f"All-time low price not found for the game '{game_id}' in country '{country}'.")


def is_valid_iso2_country_code(country_code: str) -> bool:
    """
    Check if a given country code is a valid ISO 3166-1 alpha-2 (ISO2) code.

    Args:
        country_code (str): The country code to validate.

    Returns:
        bool: True if the country code is valid, False otherwise.
    """
    try:
        # Use pycountry to look for the country with the given alpha_2 code
        return pycountry.countries.get(alpha_2=country_code.upper()) is not None
    except KeyError:
        return False
