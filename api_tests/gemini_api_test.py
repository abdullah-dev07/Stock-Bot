# To run this code, you need to install the following dependency:
# pip install google-generativeai

import os
from google import genai
from google.genai import types

def run_interactive_chat():
    """
    Sets up an interactive command-line chat session with the Gemini API.
    """
    # --- API Key Configuration ---
    # The script reads the API key from an environment variable for security.
    # To set this up in your terminal:
    # On Linux/macOS: export GEMINI_API_KEY='YOUR_API_KEY_HERE'
    # On Windows (cmd): set GEMINI_API_KEY=YOUR_API_KEY_HERE
    # On Windows (PowerShell): $env:GEMINI_API_KEY="YOUR_API_KEY_HERE"
    
    API_KEY=os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("ERROR: The GEMINI_API_KEY environment variable is not set.")
        print("Please get your key from Google AI Studio and set the environment variable.")
        return


    # --- Model Selection ---
    # We'll use 'gemini-pro' as it's a powerful and widely available model
    # suitable for a wide range of conversational tasks.
    
    print("\n--- Interactive Gemini Chat ---")
    print("Ask a question, or type 'exit' or 'quit' to end the session.")
    print("="*30)

    # --- Interactive Loop ---
    while True:
        try:
            # Get input from the user
            prompt = input("You: ")

            # Check for exit commands
            if prompt.lower() in ['exit', 'quit']:
                print("\nExiting chat. Goodbye!")
                break
            
            if not prompt:
                continue

            
            client = genai.Client(api_key=API_KEY)    
            # Generate the response
            print("\nGemini: ", end="")
            response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0) # Disables thinking
            ),
)
            
            # Print the response chunks as they arrive
            print(response.text)
            
            print("\n") # Add a newline for clean formatting after the response

        except KeyboardInterrupt:
            # Allow exiting with Ctrl+C
            print("\n\nExiting chat. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            break


if __name__ == "__main__":
    run_interactive_chat()
