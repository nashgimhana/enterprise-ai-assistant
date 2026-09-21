import os


APP_NAME = os.getenv("APP_NAME", "Enterprise AI Assistant")
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", "2000"))
