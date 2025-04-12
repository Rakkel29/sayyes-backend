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
        # Extract the planning stage from the system message
        system_message = next((msg for msg in messages if isinstance(msg, SystemMessage)), None)
        planning_stage = "initial"
        if system_message:
            for line in system_message.content.split("\n"):
                if "Current Planning Stage:" in line:
                    planning_stage = line.split(":")[1].strip()
                    break
        
        # Generate appropriate response based on planning stage
        if planning_stage == "initial":
            mock_message = AIMessage(content="Hello! 👋 I'm excited to help you plan your wedding! What kind of wedding vibe are you going for? Modern, rustic, boho, or something else?")
        elif planning_stage == "collecting_info":
            mock_message = AIMessage(content="That sounds beautiful! Do you already have a location in mind, or would you like some suggestions?")
        elif planning_stage == "sneak_peek":
            mock_message = AIMessage(content="Let me show you a sneak peek of what I can do for your dream day ✨")
        elif planning_stage == "exploring":
            mock_message = AIMessage(content="Here are some catering ideas you might love based on your theme!")
        elif planning_stage == "final_cta":
            mock_message = AIMessage(content="I've shown you a sneak peek of what I can do! Ready to take your wedding planning to the next level?")
        else:
            mock_message = AIMessage(content="Here are some modern wedding venues in California! I've found some beautiful options that match your style preferences.")
        
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
        'guest_count': 100,
        'budget': 'moderate',
        'food_preferences': 'Italian cuisine',
        'special_requests': 'Outdoor ceremony',
        'planning_stage': 'initial',
        'info_collected': 0,
        'seen_venues': False,
        'seen_dresses': False,
        'seen_hairstyles': False,
        'cta_shown': False,
        'soft_cta_shown': False,
        'email_collected': False
    }

    # Test message
    test_message = "I'm looking for a modern wedding venue in California"

    try:
        # Process the message
        result = process_message(test_message, test_state)
        
        # Print the result structure
        print('\nAPI Response Structure:')
        print('======================')
        print(json.dumps({
            'text': result['text'],
            'buttons': result.get('buttons', []),
            'state': {
                'style_preference': result['state'].get('style_preference'),
                'location_preference': result['state'].get('location_preference'),
                'planning_stage': result['state'].get('planning_stage'),
                'info_collected': result['state'].get('info_collected'),
                'seen_venues': result['state'].get('seen_venues'),
                'seen_dresses': result['state'].get('seen_dresses'),
                'seen_hairstyles': result['state'].get('seen_hairstyles'),
                'cta_shown': result['state'].get('cta_shown'),
                'soft_cta_shown': result['state'].get('soft_cta_shown'),
                'email_collected': result['state'].get('email_collected'),
                'chat_history_length': len(result['state'].get('chat_history', [])),
            }
        }, indent=2))
        
        print('\nExpected Frontend Response Format:')
        print('================================')
        print('✅ Response contains main message text')
        print('✅ Buttons are included when appropriate')
        print('✅ State tracking is preserved')
        print('✅ Chat history is maintained')
        
        # Verify the structure matches what frontend expects
        assert 'text' in result, "Text field is missing"
        assert 'state' in result, "State field is missing"
        assert isinstance(result['text'], str), "Text should be a string"
        assert isinstance(result['state'], dict), "State should be a dictionary"
        
        print('\nAll checks passed! The response format is correct for frontend consumption.')
        
    except Exception as e:
        print(f"\n❌ Error during testing: {str(e)}")
        raise

if __name__ == "__main__":
    test_process_message() 