


import os
from google import genai
from google.genai import types

def run_interactive_chat():
    """
    Sets up an interactive command-line chat session with the Gemini API.
    """
    
    
    
    
    
    
    
    API_KEY=os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        print("ERROR: The GEMINI_API_KEY environment variable is not set.")
        print("Please get your key from Google AI Studio and set the environment variable.")
        return


    
    
    
    
    print("\n--- Interactive Gemini Chat ---")
    print("Ask a question, or type 'exit' or 'quit' to end the session.")
    print("="*30)

    
    while True:
        try:
            
            prompt = input("You: ")

            
            if prompt.lower() in ['exit', 'quit']:
                print("\nExiting chat. Goodbye!")
                break
            
            if not prompt:
                continue

            
            client = genai.Client(api_key=API_KEY)    
            
            print("\nGemini: ", end="")
            response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0) 
            ),
)
            
            
            print(response.text)
            
            print("\n") 

        except KeyboardInterrupt:
            
            print("\n\nExiting chat. Goodbye!")
            break
        except Exception as e:
            print(f"\nAn error occurred: {e}")
            break


if __name__ == "__main__":
    run_interactive_chat()
