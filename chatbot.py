import os
import sys

# Load environment variable from .env
if os.path.exists(".env"):
    with open(".env") as f:
        for line in f:
            if line.startswith("GOOGLE_API_KEY="):
                os.environ["GOOGLE_API_KEY"] = line.strip().split("=", 1)[1]

from google.genai.types import Content, Part
from google.adk.runners import InMemoryRunner, print_event
from adk_root import root_agent

# Use gemini-2.0-flash for high responsiveness and robust tool execution
root_agent.model = "gemini-2.0-flash"

runner = InMemoryRunner(agent=root_agent)
runner.auto_create_session = True

print("InsightPilot AI Assistant Ready (Orchestrated by ADK)")
print("Ask business questions. Type 'exit' to stop.\n")

while True:
    try:
        query = input("You: ")
    except (KeyboardInterrupt, EOFError):
        print("\nExiting...")
        break

    if query.strip().lower() == "exit":
        break

    if not query.strip():
        continue

    try:
        new_message = Content(role="user", parts=[Part.from_text(text=query)])
        events = runner.run(
            user_id="user_1",
            session_id="session_1",
            new_message=new_message
        )
        print("\nAgent:")
        for event in events:
            # We pass verbose=False to keep the output clean and show only final responses to the user.
            print_event(event, verbose=False)
        print()
    except Exception as e:
        print(f"\nError: {e}\n")