import os
from google import genai
from dotenv import load_dotenv

load_dotenv()

def list_available_models():
    try:
        client = genai.Client(api_key=os.getenv("GOOGLE_API_KEY"))
        print("\n🔍 Listing available models...")
        
        # The SDK method might vary slightly depending on version, 
        # but usually it's client.models.list() or similar.
        # Based on the error message suggestion: "Call ListModels"
        
        for m in client.models.list():
            if '1.5' in m.name:
                print(f"- {m.name}")
            
    except Exception as e:
        print(f"❌ Error listing models: {e}")

if __name__ == "__main__":
    list_available_models()
