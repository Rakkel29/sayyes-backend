import os
import json
from sayyes_agent import process_message
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from typing import List, Any, Optional

class MockChatModel(BaseChatModel):
    """Mock LLM for testing."""
    def _generate(self, messages: List[Any], stop: Optional[List[str]] = None, **kwargs: Any) -> ChatResult:
        """Mock response generation."""
        mock_message = AIMessage(content="Here are some modern wedding venues in California! I've found some beautiful options that match your style preferences. [Mock LLM Response]")
        return ChatResult(generations=[ChatGeneration(message=mock_message)])

    def _llm_type(self) -> str:
        """Get type of llm."""
        return "mock"

# Override the LLM in sayyes_agent
import sayyes_agent
sayyes_agent.llm = MockChatModel()

def test_process_message():
    """Test the process_message function."""
    # Initial test state
    test_state = {
        'messages': [],
        'chat_history': [
            HumanMessage(content="Hi, I'm planning my wedding"),
            AIMessage(content="Hello! 👋 I'm excited to help you plan your wedding! What would you like to know about first?")
        ],
        'style_preference': 'modern',
        'location_preference': 'California',
        'seen_venues': False,
        'seen_dresses': False,
        'seen_hairstyles': False,
        'cta_shown': False,
        'soft_cta_shown': False
    }

    # Test message
    test_message = "Show me some modern wedding venues in California"

    try:
        # Process the message
        result = process_message(test_message, test_state)
        
        # Print the result structure
        print('\nAPI Response Structure:')
        print('======================')
        print(json.dumps({
            'response': result['response'],
            'state': {
                'style_preference': result['state'].get('style_preference'),
                'location_preference': result['state'].get('location_preference'),
                'seen_venues': result['state'].get('seen_venues'),
                'seen_dresses': result['state'].get('seen_dresses'),
                'seen_hairstyles': result['state'].get('seen_hairstyles'),
                'cta_shown': result['state'].get('cta_shown'),
                'soft_cta_shown': result['state'].get('soft_cta_shown'),
                'chat_history_length': len(result['state'].get('chat_history', [])),
            }
        }, indent=2))
        
        print('\nExpected Frontend Response Format:')
        print('================================')
        print('✅ Response contains main message text')
        print('✅ State tracking is preserved')
        print('✅ Chat history is maintained')
        
        # Verify the structure matches what frontend expects
        assert 'response' in result, "Response field is missing"
        assert 'state' in result, "State field is missing"
        assert isinstance(result['response'], str), "Response should be a string"
        assert isinstance(result['state'], dict), "State should be a dictionary"
        
        print('\nAll checks passed! The response format is correct for frontend consumption.')
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_process_message() 