import pytest
import sys
import os

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import clear_conversation, update_chat_info, cancel_inference, respond, custom_css, demo

def test_clear_conversation():
    result = clear_conversation()
    assert result is None

def test_update_chat_info_empty():
    history = None
    message_count, word_count = update_chat_info(history)
    assert message_count == 0
    assert word_count == 0

def test_cancel_inference():
    cancel_inference()
    from app import stop_inference
    assert stop_inference == True

def test_respond_input_types():
    message = "Test message"
    history = [("User", "Hello"), ("Bot", "Hi")]
    system_message = "You are a test bot"
    max_tokens = 100
    temperature = 0.7
    top_p = 0.9
    use_local_model = False

    generator = respond(message, history, system_message, max_tokens, temperature, top_p, use_local_model)
    
    assert hasattr(generator, '__next__')  # Check if it's a generator

def test_custom_css_exists():
    assert isinstance(custom_css, str)
    assert len(custom_css) > 0

def test_demo_object_creation():
    assert demo is not None
    assert hasattr(demo, 'launch')

if __name__ == "__main__":
    pytest.main([__file__])