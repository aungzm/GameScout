import importlib
import unittest
import sqlite3
import os
from datetime import datetime

import dbdriver
from dbdriver import (  # Replace `your_module` with the actual module name where your functions are located
    init_db, add_game_watch, update_game_watch, retrieve_game_names,
    list_game_info, retrieve_all_info, retrieve_schedule_for_game,
    delete_game_watch_by_id, delete_game_watch_by_name,
    update_schedule_for_game, retrieve_all_watches, retrieve_current_hour_watches
)

DB_FILE = "test_db.sqlite"


class TestDatabaseFunctions(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        Set up the environment and initialize the test database before all tests.
        """
        # Set the environment variable for DB_FILE to point to the test database
        os.environ["DB_FILE"] = DB_FILE
        # Reload the dbdriver module to use the updated environment variable
        importlib.reload(dbdriver)

        # Initialize the test database
        dbdriver.init_db()

    def setUp(self):
        """
        Runs before each test case to establish database connection and set test data.
        """
        self.conn = sqlite3.connect(DB_FILE)
        self.cursor = self.conn.cursor()
        self.game_id = "4343431"
        self.game_name = "Test Game2"
        self.price_watch_type = "lower than"
        self.schedule = "0 9 * * 1"
        self.country = "US"
        self.max_price = 20.00
        self.discount_percentage = None

    def tearDown(self):
        """Clean up the database after each test case."""
        self.cursor.execute("DELETE FROM game_watch")
        self.conn.commit()
        self.conn.close()
        self.conn = None  # Set to None to ensure it's not left open

    @classmethod
    def tearDownClass(cls):
        """
        Runs after all tests have completed to delete the test database file.
        """
        if hasattr(cls, 'conn') and cls.conn:
            cls.conn.close()

        # Delete the test database file if it exists
        if os.path.exists(DB_FILE):
            try:
                os.remove(DB_FILE)
            except PermissionError:
                print(f"Failed to delete {DB_FILE}. Please ensure no other processes are using it.")

    def test_add_game_watch(self):
        """
        Test adding a game watch entry to the database.
        """
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        self.cursor.execute("SELECT * FROM game_watch WHERE game_name = ?", (self.game_name,))
        result1 = self.cursor.fetchone()
        self.assertIsNotNone(result1)
        self.assertEqual(result1[2], self.game_name)

    def test_update_game_watch(self):
        """Test updating a game watch entry in the database."""
        # Add the initial game watch entry
        add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )

        # Retrieve the ID directly after insertion
        self.cursor.execute("SELECT game_id FROM game_watch WHERE game_name = ?", (self.game_name,))
        game_id = self.cursor.fetchone()[0]

        # Print initial data for verification
        print("Before update:", list_game_info(self.game_name))
        print("Game ID:", game_id)

        # Perform the update using the retrieved ID
        update_game_watch(
            game_id=game_id,  # Pass the retrieved game_id
            game_name="Updated Game",
            cron_schedule="0 9 * * 1",
            country="US",
        )

        # Print updated data for verification
        print("After update (original name):", list_game_info(self.game_name))
        print("After update (updated name):", list_game_info("Updated Game"))

        # Verify the update by checking for the updated name
        updated_info = list_game_info("Updated Game")
        self.assertTrue(updated_info)  # Check that the game exists

        # Verify that the fields are updated correctly
        self.assertEqual(updated_info[0]["game_name"], "Updated Game")

    def test_retrieve_game_names(self):
        """Test retrieving unique game names."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        game_names = retrieve_game_names()
        self.assertIn(self.game_name, game_names)

    def test_list_game_info(self):
        """Test listing all information for a game."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        game_info = list_game_info(self.game_name)
        self.assertEqual(game_info[0]["game_name"], self.game_name)

    def test_retrieve_all_info(self):
        """Test retrieving all game watch entries."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        all_info = retrieve_all_info()
        self.assertGreater(len(all_info), 0)

    def test_retrieve_schedule_for_game(self):
        """Test retrieving the schedule for a specific game."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        retrieved_schedule = retrieve_schedule_for_game(self.game_id)
        self.assertEqual(retrieved_schedule, self.schedule)

    def test_delete_game_watch_by_id(self):
        """Test deleting a game watch by game ID."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        delete_game_watch_by_id(self.game_id)
        result = list_game_info(self.game_name)
        self.assertEqual(result, [])

    def test_delete_game_watch_by_name(self):
        """Test deleting a game watch by game name."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        delete_game_watch_by_name(self.game_name)
        result = list_game_info(self.game_name)
        self.assertEqual(result, [])

    def test_update_schedule_for_game(self):
        """Test updating the schedule for a game."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        new_schedule = "0 10 * * 2"
        update_schedule_for_game(self.game_id, new_schedule)
        updated_schedule = retrieve_schedule_for_game(self.game_id)
        self.assertEqual(updated_schedule, new_schedule)

    def test_retrieve_all_watches(self):
        """Test retrieving all game watches."""
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )
        all_watches = retrieve_all_watches()
        self.assertGreater(len(all_watches), 0)

    def test_retrieve_current_hour_watches(self):
        """Test retrieving watches for the current hour."""
        # Convert the current time to a cron expression for the current hour
        current_hour = datetime.now().hour
        self.schedule = f"0 {current_hour} * * *"  # Every day at the current hour

        # Add the game watch entry with the cron schedule for the current hour
        dbdriver.add_game_watch(
            game_id=self.game_id,
            game_name=self.game_name,
            price_watch_type=self.price_watch_type,
            schedule=self.schedule,
            country=self.country,
            max_price=self.max_price,
            discount_percentage=self.discount_percentage
        )

        # Retrieve watches scheduled for the current hour
        current_hour_watches = retrieve_current_hour_watches()
        print(current_hour_watches)  # For debugging
        self.assertGreater(len(current_hour_watches), 0)


if __name__ == "__main__":
    unittest.main()
