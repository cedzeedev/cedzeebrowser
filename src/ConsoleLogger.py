import logging
import os

"""
ConsoleLogger provides logging to both console and file for debugging and monitoring.

Example output:
ConsoleLogger -- 2025-07-18 12:19:15,165 [DEBUG]: Debug message
ConsoleLogger -- 2025-07-18 12:19:15,165 [INFO]: Info message
ConsoleLogger -- 2025-07-18 12:19:15,166 [WARNING]: Warning message !
ConsoleLogger -- 2025-07-18 12:19:15,166 [ERROR]: An error has occurred
ConsoleLogger -- 2025-07-18 12:19:15,166 [CRITICAL]: Critical error

Usage:
from src.ConsoleLogger import logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message !")
logger.error("An error has occurred")
logger.critical("Critical error")
"""

# Get project root directory
directory = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Formatter for log messages
formatter = logging.Formatter("%(name)s -- %(asctime)s [%(levelname)s]: %(message)s")

logger = logging.getLogger("ConsoleLogger")
logger.setLevel(logging.DEBUG)

# Log to file
file_handler = logging.FileHandler(f"{directory}/cedzee_browser.log", mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Log to console
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
