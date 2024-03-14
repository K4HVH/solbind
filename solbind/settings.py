import json
import os

class settings:

    private_key = ""
    rpc_url = ""
    strategy = 0
    amount = 0

    @classmethod
    def read_settings(cls):
        try:
            with open("settings.json", "r") as file:
                settings_data = json.load(file)
            
            # Update settings using environment variables if they exist
            for key in settings_data:
                env_variable = os.getenv(key.upper())
                if env_variable:
                    setattr(cls, key, env_variable)
                else:
                    setattr(cls, key, settings_data[key])

        except FileNotFoundError:
            return {}
        
    @classmethod
    def write_settings(cls, variable_name=None, variable_value=None):
        settings_data = {
            "private_key": cls.private_key,
            "rpc_url": cls.rpc_url,
            "strategy": cls.strategy,
            "amount": cls.amount
        }

        # If a specific variable is provided, update only that variable
        if variable_name and variable_value is not None:
            settings_data[variable_name] = variable_value

        with open("settings.json", "w") as file:
            json.dump(settings_data, file, indent=4)

    @classmethod
    def configure_settings(cls, logger):
        cls.read_settings()

        logger.print_and_log("Current settings:")
        logger.print_and_log({"private_key": cls.private_key, "rpc_url": cls.rpc_url, "strategy": cls.strategy, "amount": cls.amount})

        logger.print_and_log("Let's configure the settings.")

        # Get user input for settings
        keys_to_configure = ["private_key", "rpc_url", "strategy", "amount"]
        for key in keys_to_configure:
            current_value = getattr(cls, key, "")
            new_value = input(f"Enter value for {key} ({current_value}): ") or current_value
            setattr(cls, key, new_value)

        # Update the settings file with user input
        cls.write_settings()

        logger.print_and_log("Settings updated.")

    @classmethod
    def check_settings(cls, logger):
        # Check if the settings file exists
        if not os.path.isfile("settings.json"):
            logger.print_and_log("Error: settings.json file not found.")
            return False

        # Read settings from the file
        settings_data = cls.read_settings()

        # Check if each variable exists and has a valid value
        required_variables = ["private_key", "rpc_url", "strategy", "amount"]
        missing_variables = []
        invalid_variables = []

        try:
            with open("settings.json", "r") as file:
                file_settings = json.load(file)

            for variable in required_variables:
                if variable not in file_settings:
                    missing_variables.append(variable)
                else:
                    value = file_settings[variable]
                    if not value or not isinstance(value, str):
                        invalid_variables.append(variable)

            if missing_variables or invalid_variables:
                logger.print_and_log("Error: The following issues were found in the settings file:")
                for variable in missing_variables:
                    logger.print_and_log(f"- {variable} is missing")
                for variable in invalid_variables:
                    logger.print_and_log(f"- {variable} has an invalid value")
                return False

            logger.print_and_log("Settings are valid.")
            return True

        except json.JSONDecodeError:
            logger.print_and_log("Error: Unable to decode settings.json file.")
            return False
