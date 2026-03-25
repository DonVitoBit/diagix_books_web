from google import genai
from google.genai import types
import os

api_key = 'AIzaSyA1feIzuCUxJADKmqnQrtXleV62byg3TVs'
client = genai.Client(api_key=api_key)

image_path = "test_image.png"
if not os.path.exists(image_path):
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(image_path)

print("\nTesting generate_content with gemini-2.5-flash-image (Image-to-Image?)...")
try:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # Create content with image + text
    prompt = "Redraw this image in high quality medical style. Output ONLY the image."
    
    # Check if we can pass Part object or something
    # For generate_content, we usually pass a list of parts.
    
    # We need to construct the input content properly.
    # Usually: contents=[types.Content(parts=[types.Part(text=...), types.Part(inline_data=...)])]
    
    response = client.models.generate_content(
        model='gemini-2.5-flash-image',
        contents=[
            types.Content(
                parts=[
                    types.Part(text=prompt),
                    types.Part(inline_data=types.Blob(
                        mime_type='image/png',
                        data=image_bytes
                    ))
                ]
            )
        ]
    )
    
    print("Response candidates:", len(response.candidates))
    for cand in response.candidates:
        print("Content parts:", len(cand.content.parts))
        for part in cand.content.parts:
            if part.inline_data:
                print("✅ Found inline image data!")
            if part.text:
                print(f"Text: {part.text[:50]}...")

except Exception as e:
    print(f"❌ Error: {e}")
