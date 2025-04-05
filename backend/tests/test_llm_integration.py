"""
Tests for the LLM integration.
"""
import os
import sys
import pytest
import json
from pathlib import Path

# Add the parent directory to the path so we can import app
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.llm.service import LLMService
from app.llm.parser import LLMResponseParser
from app.agent.message_manager import MessageManager

@pytest.mark.asyncio
async def test_llm_service_init():
    """Test that the LLM service initializes correctly."""
    llm_service = LLMService()
    assert llm_service is not None
    assert llm_service.llm is not None

@pytest.mark.asyncio
async def test_message_manager():
    """Test the message manager functionality."""
    manager = MessageManager(max_history_length=5)
    
    # Test adding messages
    manager.add_user_message("Hello")
    manager.add_assistant_message("Hi there!")
    manager.add_system_message("System message")
    
    # Test getting messages
    messages = manager.get_messages()
    assert len(messages) == 3
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Hello"
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Hi there!"
    assert messages[2]["role"] == "system"
    assert messages[2]["content"] == "System message"
    
    # Test max history length
    for i in range(5):
        manager.add_user_message(f"Message {i}")
    
    messages = manager.get_messages()
    assert len(messages) == 5  # Should be truncated to max length
    assert messages[0]["content"] == "Message 0"  # Oldest messages should be removed
    
    # Test state management
    manager.update_state("current_url", "https://example.com")
    assert manager.get_state("current_url") == "https://example.com"
    assert manager.get_state("nonexistent") is None
    assert manager.get_state("nonexistent", "default") == "default"
    
    # Test serialization and deserialization
    serialized = manager.serialize()
    new_manager = MessageManager.deserialize(serialized)
    assert new_manager.get_state("current_url") == "https://example.com"
    assert len(new_manager.get_messages()) == 5

@pytest.mark.asyncio
async def test_llm_response_parser():
    """Test the LLM response parser."""
    parser = LLMResponseParser()
    
    # Test parsing valid JSON response
    valid_response = """
    I'll help you navigate to Google.
    
    ```json
    {
      "thought": "The user wants to navigate to Google's homepage. I need to use the go_to_url action with the URL for Google.",
      "action": "go_to_url",
      "parameters": {
        "url": "https://www.google.com"
      }
    }
    ```
    """
    
    parsed = parser.parse_response(valid_response)
    assert parsed["action"] == "go_to_url"
    assert parsed["parameters"]["url"] == "https://www.google.com"
    assert "thought" in parsed
    
    # Test JSON extraction with different formats
    inline_json = 'Here is the action: `{"action": "done", "parameters": {}, "thought": "Nothing to do"}`'
    parsed = parser.parse_response(inline_json)
    assert parsed["action"] == "done"
    
    # Test URL fixing
    url_response = """
    ```json
    {
      "thought": "The user wants to navigate to Google's homepage.",
      "action": "go_to_url",
      "parameters": {
        "url": "google.com"
      }
    }
    ```
    """
    
    parsed = parser.parse_response(url_response)
    assert parsed["parameters"]["url"] == "https://google.com"

if __name__ == "__main__":
    # Run the tests manually
    import asyncio
    asyncio.run(test_llm_service_init())
    asyncio.run(test_message_manager())
    asyncio.run(test_llm_response_parser())
    print("All tests passed!") 