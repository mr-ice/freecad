"""Put the Wispwood project dir on sys.path so tests import its modules directly."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
