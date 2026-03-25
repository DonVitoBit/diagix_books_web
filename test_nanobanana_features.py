from google import genai
from google.genai import types
import os

api_key = 'AIzaSyA1feIzuCUxJADKmqnQrtXleV62byg3TVs'
client = genai.Client(api_key=api_key)

print("Listing all models...")
for m in client.models.list():
    print(f" - {m.name}")

image_path = "test_image.png"

# Create a dummy image if not exists
if not os.path.exists(image_path):
    from PIL import Image
    img = Image.new('RGB', (100, 100), color = 'red')
    img.save(image_path)

print(f"\nTesting upscale with imagen-4.0-generate-001...")
try:
    with open(image_path, "rb") as f:
        image_bytes = f.read()
        
    resp = client.models.upscale_image(
        model='imagen-4.0-generate-001',
        image=types.Image(image_bytes=image_bytes),
        upscale_factor='x2'
    )
    print("✅ Upscale Success!")
except Exception as e:
    print(f"❌ Upscale Error: {e}")

print(f"\nTesting edit_image with imagen-4.0-generate-001...")
try:
    with open(image_path, "rb") as f:
        image_bytes = f.read()

    # RawReferenceImage
    ref_img = types.RawReferenceImage(
        reference_id=1,
        reference_image=types.Image(image_bytes=image_bytes)
    )

    resp = client.models.edit_image(
        model='imagen-4.0-generate-001',
        prompt='make it blue',
        reference_images=[ref_img],
        config=types.EditImageConfig(
            edit_mode='EDIT_MODE_INPAINT_INSERTION', # Just testing if this works
            number_of_images=1
        )
    )
    print("✅ Edit Success!")
except Exception as e:
    print(f"❌ Edit Error: {e}")
