#!/usr/bin/env python3
"""
Test script for LongcatChatbot to verify basic functionality
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from longcat_chatbot import LongcatChatbot

def test_longcat_basic():
    """Test basic initialization and methods of LongcatChatbot"""
    print("Testing LongcatChatbot basic functionality...")
    
    try:
        # Test initialization
        chatbot = LongcatChatbot()
        print("✓ LongcatChatbot initialized successfully")
        
        # Test header setup
        assert hasattr(chatbot, 'session')
        assert hasattr(chatbot, 'messages')
        assert hasattr(chatbot, 'api_url')
        print("✓ All required attributes present")
        
        # Test message ID generation
        msg_id = chatbot.generate_message_id()
        assert isinstance(msg_id, int)
        assert 10000000 <= msg_id <= 99999999
        print("✓ Message ID generation working")
        
        # Test clear history
        chatbot.clear_history()
        assert len(chatbot.messages) == 0
        print("✓ Clear history working")
        
        # Test show history with empty history
        print("Testing show_history with empty history:")
        chatbot.show_history()
        
        print("\n🎉 All basic tests passed! LongcatChatbot is working correctly.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

def test_longcat_api_call():
    """Test a simple API call (requires internet connection)"""
    print("\nTesting API call functionality...")
    
    try:
        chatbot = LongcatChatbot()
        
        # Test with a simple message
        print("Sending test message: 'Hello, can you say hi?'")
        response = chatbot.send_message("Hello, can you say hi?")
        
        if response and not response.startswith("Error:") and not response.startswith("Connection error:"):
            print("✓ API call successful")
            print(f"Response preview: {response[:100]}...")
            return True
        else:
            print(f"⚠️  API call returned error or empty response: {response}")
            return False
            
    except Exception as e:
        print(f"❌ API test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("=" * 50)
    print("LONGCAT CHATBOT TEST SUITE")
    print("=" * 50)
    
    # Run basic tests
    basic_test_passed = test_longcat_basic()
    
    # Run API test if basic tests pass
    if basic_test_passed:
        api_test_passed = test_longcat_api_call()
        
        if api_test_passed:
            print("\n🎉 All tests passed! LongcatChatbot is fully functional.")
        else:
            print("\n⚠️  Basic functionality works, but API test failed (might be network/API issue).")
    else:
        print("\n❌ Basic tests failed. Please check the implementation.")
    
    print("=" * 50)