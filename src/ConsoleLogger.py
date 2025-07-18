import logging
import os

"""

Log management involves collecting and analyzing logs,
which are essential for understanding system states and troubleshooting issues.

Example:

ConsoleLogger -- 2025-07-18 12:19:15,165 [DEBUG]: Debug message
ConsoleLogger -- 2025-07-18 12:19:15,165 [INFO]: Info message
ConsoleLogger -- 2025-07-18 12:19:15,166 [WARNING]: Warning message !
ConsoleLogger -- 2025-07-18 12:19:15,166 [ERROR]: An error has occurred
ConsoleLogger -- 2025-07-18 12:19:15,166 [CRITICAL]: Critical error

Utilization:

from src.ConsoleLogger import logger

# logger.debug("Debug message")
# logger.info("Info message")
# logger.warning("Warning message !")
# logger.error("An error has occurred")
# logger.critical("Critical error")

"""

# Directory
directory = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

# Example: ConsoleLogger -- 2025-07-18 12:19:15,165 [DEBUG]: Debug message
formatter = logging.Formatter("%(name)s -- %(asctime)s [%(levelname)s]: %(message)s")

logger = logging.getLogger("ConsoleLogger")
logger.setLevel(logging.DEBUG)

# *=*=*= cedzee_browser.log file =*=*=*
file_handler = logging.FileHandler(f"{directory}/cedzee_browser.log", mode='w')
file_handler.setLevel(logging.DEBUG)
# *=*=*= console =*=*=*
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)

file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

logger.addHandler(file_handler)
logger.addHandler(console_handler)
