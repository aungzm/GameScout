def all_time_low_compare(current_price: float, all_time_low_price: float) -> bool:
    """
    Compares current price with all-time low price.

    Args:
        current_price (float): The current price of the item.
        all_time_low_price (float): The recorded all-time low price of the item.

    Returns:
        bool: True if current price is less than or equal to all-time low price, False otherwise.
    """
    return current_price <= all_time_low_price


def percentage_compare(current_price: float, original_price: float, discount_percentage: float) -> bool:
    """
    Compares current price with the calculated discount price.

    Args:
        current_price (float): The current price of the item.
        original_price (float): The original price of the item.
        discount_percentage (float): The discount percentage (as a value between 0 and 100).

    Returns:
        bool: True if the discounted price is greater than or equal to the current price, False otherwise.
    """
    discounted_price = original_price * (1 - (discount_percentage / 100))
    return discounted_price >= current_price


def is_on_sale(current_price: float, original_price: float) -> bool:
    """
    Checks if the item is currently on sale by comparing the current price with the original price.

    Args:
        current_price (float): The current price of the item.
        original_price (float): The original price of the item.

    Returns:
        bool: True if the item is on sale, False otherwise.
    """
    return current_price < original_price


def is_significant_drop(current_price: float, historical_prices: list[float], threshold_percentage: float) -> bool:
    """
    Analyzes if the current price is significantly lower than the average historical price.

    Args:
        current_price (float): The current price of the item.
        historical_prices (list[float]): A list of historical prices for the item.
        threshold_percentage (float): The percentage threshold below the average to consider as a significant drop.

    Returns:
        bool: True if the current price is lower than the threshold below the historical average, False otherwise.
    """
    if not historical_prices:
        return False
    average_price = sum(historical_prices) / len(historical_prices)
    significant_drop = average_price * (1 - threshold_percentage / 100)
    return current_price <= significant_drop


def is_below_target_price(current_price: float, target_price: float) -> bool:
    """
    Checks if the current price is below a user-specified target price.

    Args:
        current_price (float): The current price of the item.
        target_price (float): The price the user is waiting for.

    Returns:
        bool: True if the current price is below the target price, False otherwise.
    """
    return current_price <= target_price


def is_in_price_range(current_price: float, min_price: float, max_price: float) -> bool:
    """
    Checks if the current price falls within the specified price range.

    Args:
        current_price (float): The current price of the item.
        min_price (float): The minimum acceptable price.
        max_price (float): The maximum acceptable price.

    Returns:
        bool: True if the price is within the specified range, False otherwise.
    """
    return min_price <= current_price <= max_price
