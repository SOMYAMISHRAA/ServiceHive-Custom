import sys
import os

from agent import process_message

try:
    print(process_message("test-session", "Hi"))
    print("SUCCESS")
except Exception as e:
    import traceback
    traceback.print_exc()
