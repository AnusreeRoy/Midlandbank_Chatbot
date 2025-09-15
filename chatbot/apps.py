from django.apps import AppConfig
import os
import json
from django.conf import settings
product_aliases_data = {}

class ChatbotConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'chatbot'
    def ready(self):
        """
        This method is called once when Django starts up.
        It loads your product aliases, sorts them by length (longest first),
        and then populates the global 'product_aliases_data' dictionary
        in that sorted order.
        """
        global product_aliases_data # Declare intent to modify the global variable


        aliases_file_path = os.path.join(settings.BASE_DIR, self.name, 'data', 'product_aliases.json')

        try:
            with open(aliases_file_path, 'r', encoding='utf-8') as f:
                loaded_aliases_dict = json.load(f)
                
                # Convert the dictionary to a list of (alias, canonical_name) tuples
                # and sort by alias string length (longest first).
                # Aliases (keys) are converted to lowercase here for consistent matching in views.py.
                sorted_aliases_list = sorted(
                    loaded_aliases_dict.items(),
                    key=lambda item: len(item[0]), # Sort by length of the alias (the dictionary key)
                    reverse=True # Arrange from longest to shortest
                )
                
                # Clear the existing dictionary to ensure a fresh population
                product_aliases_data.clear()

                # Re-populate the global product_aliases_data dictionary by inserting
                # items in the sorted order. This ensures Python's dictionary iteration
                # order (insertion order) is preserved.
                for alias, canonical in sorted_aliases_list:
                    product_aliases_data[alias.lower()] = canonical # Store alias key as lowercase

            print(f"Successfully loaded and ordered product aliases from {aliases_file_path}")
            print(f"Total aliases loaded: {len(product_aliases_data)}")
        except FileNotFoundError:
            print(f"ERROR: Product aliases file not found at {aliases_file_path}. Please create it.")
            print("Expected format: {'alias_string': 'Canonical Product Name', ...}")
        except json.JSONDecodeError:
            print(f"ERROR: Could not decode JSON from {aliases_file_path}. Check for syntax errors (e.g., missing commas, unquoted strings).")
        except Exception as e:
            print(f"An unexpected error occurred while loading aliases: {e}")


