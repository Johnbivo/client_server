
"""This is the server logger. Every file in the server writes logs. This file initializes and sets up the log
for other files to use.
Sets a logger named 'server_log.log' and the format in which other files put logs in is
DATE/TIME - LEVEL - MESSAGE an example would be 2025-01-23 17:00 - ERROR - 'Could not open the door.

If the file reaches 5 mb it will be renamed adding numbers 1-5 at the end server_log.log.1'
and a new logger will be created. The program will keep the most recent 5 files as backups"""



import logging
from logging.handlers import RotatingFileHandler


#Logger
server_logger = logging.getLogger("server_logger")
server_logger.setLevel(logging.DEBUG)

# File handler
# When the logger exceeds 5 mb it will put it aside and create a new logger. Up to 5 files.
server_file_handler = RotatingFileHandler("server_log.log",maxBytes=5 * 1024 * 1024, backupCount=5)
server_file_handler.setLevel(logging.DEBUG)

#Stream handler
server_stream_handler = logging.StreamHandler()
server_stream_handler.setLevel(logging.DEBUG)


# Formatter
server_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
server_file_handler.setFormatter(server_formatter)
server_stream_handler.setFormatter(server_formatter)

#Add handlers to logger
server_logger.addHandler(server_file_handler)
server_logger.addHandler(server_stream_handler)

