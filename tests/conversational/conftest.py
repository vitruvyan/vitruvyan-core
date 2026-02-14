"""
Conversational tests - local conftest

Mock problematic imports for conversational tests to run in isolation.
"""

import sys
import os
from unittest.mock import MagicMock

# Add config to path BEFORE any test imports
_config_path = os.path.join(os.path.dirname(__file__), "..", "..", "config")
if _config_path not in sys.path:
    sys.path.insert(0, os.path.abspath(_config_path))

# Mock config.api_config module to prevent import errors
mock_api_config = MagicMock()
mock_api_config.get_embedding_url.return_value = "http://mock_embedding:8000"
mock_api_config.get_embedding_endpoint.return_value = "/embeddings"
sys.modules['config.api_config'] = mock_api_config
