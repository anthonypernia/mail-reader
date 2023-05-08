""" Settings module """

import yaml

import mail_reader.utils.constants as c


def get_file_config() -> dict:
    """Get the configuration from the settings file
    Returns:
        dict: configuration
    """
    with open(c.SETTINGS_FILE, encoding="utf8") as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    return config


def get_config(key: str) -> dict:
    """Get the configuration from the settings file by key
    Args:
        key (str): key to get the configuration
    Returns:
        dict: configuration
    """
    config = get_file_config()
    return config.get(key, None)
