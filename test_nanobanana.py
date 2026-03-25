from google import genai
from google.genai import types
import os

api_key = 'AIzaSyA1feIzuCUxJADKmqnQrtXleV62byg3TVs'

print(f"Testing with API Key: {api_key[:5]}...")

try:
    client = genai.Client(api_key=api_key)
    print("Client initialized")
    
    print("Listing models...")
    for m in client.models.list():
        if 'image' in m.name:
            print(f" - {m.name}")

    print("\nAttempting generation with 'imagen-4.0-fast-generate-001'...")
    resp = client.models.generate_images(
        model='imagen-4.0-fast-generate-001',
        prompt='Medical illustration of a heart',
        config=types.GenerateImagesConfig(
            number_of_images=1,
            output_mime_type="image/png"
        )
    )
    
    if resp.generated_images:
        print("✅ Success! Image generated.")
        print(f"Image bytes length: {len(resp.generated_images[0].image_bytes)}")
    else:
        print("❌ Generated images list is empty.")

except Exception as e:
    print(f"\n❌ Error occurred: {e}")
