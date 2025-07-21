"""Same as the server.

This is the server logger. Every file in the server writes logs. This file initializes and sets up the log
for other files to use.
Sets a logger named 'client_log.log' and the format in which other files put logs in is
DATE/TIME - LEVEL - MESSAGE an example would be 2025-01-23 17:00 - ERROR - 'Could not open the door.'


If the file reaches 5 mb it will be renamed adding numbers 1-5 at the end server_log.log.1'
and a new logger will be created. The program will keep the most recent 5 files as backups"""


import logging
from logging.handlers import RotatingFileHandler

#Logger
client_logger = logging.getLogger("client_logger")
client_logger.setLevel(logging.DEBUG)

# File handler
client_file_handler = RotatingFileHandler("client_log.log",maxBytes=5 * 1024 * 1024, backupCount=5)
client_file_handler.setLevel(logging.DEBUG)

#Stream handler
client_stream_handler = logging.StreamHandler()
client_stream_handler.setLevel(logging.DEBUG)


# Formatter
client_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
client_file_handler.setFormatter(client_formatter)
client_stream_handler.setFormatter(client_formatter)

#Add handlers to logger
client_logger.addHandler(client_file_handler)
client_logger.addHandler(client_stream_handler)