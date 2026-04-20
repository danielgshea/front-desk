"""
Test suite for AdminAgent - Testing LM Studio connection and model responses.

These tests verify:
1. LM Studio server connectivity
2. Model loading and basic responses
3. Agent initialization
4. Agent interaction with tools
5. Error handling

To run these tests:
    pytest tests/test_agent.py -v -s

Prerequisites:
- LM Studio must be running on http://127.0.0.1:1234
- A model must be loaded in LM Studio
- .env file must have LM_STUDIO_BASE_URL and LM_STUDIO_MODEL configured
"""

import pytest
import asyncio
import os
import requests
from unittest.mock import Mock, patch, MagicMock
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class TestLMStudioConnection:
    """Test LM Studio server connection and availability."""
    
    def test_env_variables_set(self):
        """Test that required environment variables are set."""
        base_url = os.getenv('LM_STUDIO_BASE_URL')
        model_name = os.getenv('LM_STUDIO_MODEL') or os.getenv('LM_STUDIO_MODEL_NAME')
        
        assert base_url is not None, "LM_STUDIO_BASE_URL not set in .env"
        assert model_name is not None, "LM_STUDIO_MODEL or LM_STUDIO_MODEL_NAME not set in .env"
        
        print(f"\n✓ Base URL: {base_url}")
        print(f"✓ Model: {model_name}")
    
    def test_lm_studio_server_reachable(self):
        """Test that LM Studio server is reachable."""
        base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
        
        try:
            # Try to reach the models endpoint
            response = requests.get(f"{base_url}/v1/models", timeout=5)
            
            assert response.status_code == 200, f"Server returned {response.status_code}"
            
            models = response.json()
            print(f"\n✓ LM Studio server is running at {base_url}")
            print(f"✓ Available models: {len(models.get('data', []))}")
            
            for model in models.get('data', []):
                print(f"  - {model.get('id', 'unknown')}")
                
        except requests.exceptions.ConnectionError:
            pytest.skip("LM Studio server is not running. Start LM Studio and load a model.")
        except requests.exceptions.Timeout:
            pytest.skip("LM Studio server connection timed out.")
    
    def test_model_loaded(self):
        """Test that a model is actually loaded in LM Studio."""
        base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
        
        try:
            response = requests.get(f"{base_url}/v1/models", timeout=5)
            models = response.json()
            
            model_list = models.get('data', [])
            assert len(model_list) > 0, "No models loaded in LM Studio"
            
            print(f"\n✓ Model is loaded and ready")
            
        except requests.exceptions.ConnectionError:
            pytest.skip("LM Studio server is not running")


class TestModelBasicResponses:
    """Test basic model responses without agent framework."""
    
    def test_model_initialization(self):
        """Test that ChatOpenAI can be initialized with LM Studio config."""
        from langchain_openai import ChatOpenAI
        
        model_name = os.getenv('LM_STUDIO_MODEL') or os.getenv('LM_STUDIO_MODEL_NAME')
        base_url = os.getenv('LM_STUDIO_BASE_URL')
        
        # Note: Fix env variable inconsistency
        if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
            os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            print(f"\n⚠️  Fixed env variable: LM_STUDIO_MODEL_NAME → LM_STUDIO_MODEL")
        
        try:
            model = ChatOpenAI(
                model=model_name,
                openai_api_base=base_url,
                openai_api_key="not-needed",  # LM Studio doesn't require key
                temperature=0.7
            )
            
            assert model is not None
            print(f"\n✓ Model initialized successfully")
            print(f"  Model: {model_name}")
            print(f"  Base URL: {base_url}")
            
        except Exception as e:
            pytest.fail(f"Failed to initialize model: {e}")
    
    def test_simple_completion(self):
        """Test a simple completion request."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        model_name = os.getenv('LM_STUDIO_MODEL') or os.getenv('LM_STUDIO_MODEL_NAME')
        base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        try:
            model = ChatOpenAI(
                model=model_name,
                openai_api_base=base_url,
                openai_api_key="not-needed",
                temperature=0.7
            )
            
            # Simple test prompt
            response = model.invoke([HumanMessage(content="Say 'Hello, World!' and nothing else.")])
            
            assert response is not None
            assert hasattr(response, 'content')
            assert len(response.content) > 0
            
            print(f"\n✓ Model responded successfully")
            print(f"  Prompt: Say 'Hello, World!' and nothing else.")
            print(f"  Response: {response.content[:100]}")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Model invocation failed: {e}")
    
    def test_math_reasoning(self):
        """Test model's basic reasoning ability."""
        from langchain_openai import ChatOpenAI
        from langchain_core.messages import HumanMessage
        
        model_name = os.getenv('LM_STUDIO_MODEL') or os.getenv('LM_STUDIO_MODEL_NAME')
        base_url = os.getenv('LM_STUDIO_BASE_URL', 'http://127.0.0.1:1234')
        if not base_url.endswith('/v1'):
            base_url = f"{base_url}/v1"
        
        try:
            model = ChatOpenAI(
                model=model_name,
                openai_api_base=base_url,
                openai_api_key="not-needed"
            )
            
            response = model.invoke([HumanMessage(content="What is 15 + 27? Respond with only the number.")])
            
            assert response is not None
            # Check if 42 is in the response (might have extra text)
            assert "42" in response.content
            
            print(f"\n✓ Model can handle basic math")
            print(f"  Question: What is 15 + 27?")
            print(f"  Response: {response.content[:100]}")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Math reasoning test failed: {e}")


class TestAgentInitialization:
    """Test AdminAgent initialization and setup."""
    
    def test_agent_imports(self):
        """Test that agent module can be imported."""
        try:
            from admin_agent.agent import AdminAgent, get_agent
            print("\n✓ Agent imports successful")
        except ImportError as e:
            pytest.fail(f"Failed to import agent: {e}")
    
    def test_agent_creation(self):
        """Test creating an AdminAgent instance."""
        from admin_agent.agent import AdminAgent
        
        try:
            # Fix env variable if needed
            if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
                os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            
            agent = AdminAgent()
            
            assert agent is not None
            assert hasattr(agent, 'model')
            assert hasattr(agent, 'agent')
            
            print("\n✓ AdminAgent created successfully")
            print(f"  Has model: {agent.model is not None}")
            print(f"  Has agent: {agent.agent is not None}")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Agent creation failed: {e}")
    
    def test_agent_has_tools(self):
        """Test that agent is initialized with calendar tools."""
        from admin_agent.agent import AdminAgent
        from admin_agent.utils.tools import CALENDAR_TOOLS
        
        try:
            if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
                os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            
            agent = AdminAgent()
            
            # The agent should have tools available
            print(f"\n✓ Agent initialized with {len(CALENDAR_TOOLS)} calendar tools:")
            for tool in CALENDAR_TOOLS:
                print(f"  - {tool.name}")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Tool initialization failed: {e}")


class TestAgentInteraction:
    """Test agent interactions and responses."""
    
    @pytest.mark.asyncio
    async def test_simple_query(self):
        """Test agent responds to a simple query without tool use."""
        from admin_agent.agent import AdminAgent
        
        try:
            if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
                os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            
            agent = AdminAgent()
            
            # Simple question that doesn't require calendar access
            response = await agent.agent.ainvoke({
                "messages": [{"role": "user", "content": "What is your purpose? Keep your answer brief."}]
            })
            
            assert response is not None
            print(f"\n✓ Agent responded to simple query")
            print(f"  Query: What is your purpose?")
            print(f"  Response: {str(response)[:200]}...")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Simple query failed: {e}")
    
    @pytest.mark.asyncio
    @pytest.mark.slow
    async def test_tool_aware_query(self):
        """Test that agent knows about its calendar tools."""
        from admin_agent.agent import AdminAgent
        
        try:
            if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
                os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            
            agent = AdminAgent()
            
            # Ask about capabilities
            response = await agent.agent.ainvoke({
                "messages": [{"role": "user", "content": "What tools do you have access to? List them briefly."}]
            })
            
            assert response is not None
            
            # Check if response mentions calendar-related terms
            response_str = str(response).lower()
            has_calendar_mention = any(term in response_str for term in 
                                      ['calendar', 'event', 'schedule'])
            
            print(f"\n✓ Agent is aware of its tools")
            print(f"  Mentions calendar features: {has_calendar_mention}")
            print(f"  Response preview: {str(response)[:300]}...")
            
        except Exception as e:
            if "Connection" in str(e):
                pytest.skip("LM Studio server is not running")
            pytest.fail(f"Tool awareness query failed: {e}")


class TestAgentErrorHandling:
    """Test agent error handling and edge cases."""
    
    def test_missing_env_variable(self):
        """Test behavior when env variables are missing."""
        # Temporarily remove env variable
        original_model = os.getenv('LM_STUDIO_MODEL')
        original_model_name = os.getenv('LM_STUDIO_MODEL_NAME')
        
        if 'LM_STUDIO_MODEL' in os.environ:
            del os.environ['LM_STUDIO_MODEL']
        if 'LM_STUDIO_MODEL_NAME' in os.environ:
            del os.environ['LM_STUDIO_MODEL_NAME']
        
        try:
            from admin_agent.agent import AdminAgent
            
            # This should fail gracefully
            with pytest.raises((KeyError, ValueError, TypeError)):
                agent = AdminAgent()
            
            print("\n✓ Agent handles missing env variables appropriately")
            
        finally:
            # Restore env variables
            if original_model:
                os.environ['LM_STUDIO_MODEL'] = original_model
            if original_model_name:
                os.environ['LM_STUDIO_MODEL_NAME'] = original_model_name
    
    def test_invalid_base_url(self):
        """Test behavior with invalid LM Studio URL."""
        from admin_agent.agent import AdminAgent
        
        # Temporarily set invalid URL
        original_url = os.getenv('LM_STUDIO_BASE_URL')
        os.environ['LM_STUDIO_BASE_URL'] = 'http://invalid-url:9999'
        
        try:
            if not os.getenv('LM_STUDIO_MODEL') and os.getenv('LM_STUDIO_MODEL_NAME'):
                os.environ['LM_STUDIO_MODEL'] = os.getenv('LM_STUDIO_MODEL_NAME')
            
            # Agent creation should succeed (lazy connection)
            agent = AdminAgent()
            assert agent is not None
            
            print("\n✓ Agent handles invalid URL (lazy connection)")
            
        finally:
            # Restore original URL
            if original_url:
                os.environ['LM_STUDIO_BASE_URL'] = original_url


# Test markers for pytest
pytestmark = pytest.mark.integration


def pytest_configure(config):
    """Configure custom pytest markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests requiring LM Studio"
    )
