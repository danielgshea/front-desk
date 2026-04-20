"""Interactive demo of the Admin Agent.

This script provides a simple CLI interface to interact with your personal
assistant agent that has Google Calendar integration.
"""
import asyncio
from admin_agent import AdminAgent


async def main():
    """Run an interactive demo of the admin agent."""
    print("\n" + "=" * 70)
    print("🤖  ADMIN AGENT - Your Personal Calendar Assistant")
    print("=" * 70)
    print("\nWelcome! I'm your admin agent with access to your Google Calendar.")
    print("I can help you:")
    print("  • View your upcoming events")
    print("  • Create new calendar events")
    print("  • Update or delete existing events")
    print("  • Manage your schedule")
    print("\n📊 LangSmith tracing is enabled - check your dashboard!")
    print("=" * 70)
    print("\nType 'quit' or 'exit' to end the session.\n")
    
    # Initialize the agent
    agent = AdminAgent()
    chat_history = []
    
    # Interactive loop
    while True:
        try:
            # Get user input
            user_input = input("\n👤 You: ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\n👋 Goodbye! Have a great day!\n")
                break
            
            # Get agent response
            print("\n🤖 Admin Agent: ", end="", flush=True)
            response = await agent.ainvoke(user_input, chat_history)
            print(response['output'])
            
            # Update chat history
            chat_history.extend([
                {"role": "user", "content": user_input},
                {"role": "assistant", "content": response['output']}
            ])
            
        except KeyboardInterrupt:
            print("\n\n👋 Session interrupted. Goodbye!\n")
            break
        except Exception as e:
            print(f"\n❌ Error: {str(e)}")
            print("Please try again or type 'quit' to exit.\n")


if __name__ == "__main__":
    asyncio.run(main())
