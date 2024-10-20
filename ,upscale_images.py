import os
import base64
import requests

# API endpoint for batch upscaling images
UPSCALE_API_URL = "http://0.0.0.0:7860/sdapi/v1/extra-batch-images"

# Directories for input and output
INPUT_DIR = "./generated_images"
OUTPUT_DIR = "./upscaled_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Function to read and encode image in base64 format
def encode_image_to_base64(image_path):
    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read()).decode('utf-8')
    return encoded_string

# Function to upscale a batch of images using the API
def upscale_images_batch(image_paths):
    # Prepare the list of images to send to the API
    image_list = [{"data": encode_image_to_base64(image_path), "name": os.path.basename(image_path)} for image_path in image_paths]

    # Payload with parameters for batch upscaling
    payload = {
        "resize_mode": 0,
        "show_extras_results": True,
        "gfpgan_visibility": 0,
        "codeformer_visibility": 0,
        "codeformer_weight": 0,
        "upscaling_resize": 2,  # Scaling factor of 2
        #"upscaling_resize_w": 512,  # Optional: Fixed width, can be changed as needed
        #"upscaling_resize_h": 512,  # Optional: Fixed height, can be changed as needed
        "upscaling_crop": True,  # Whether to crop the image
        "upscaler_1": "4x-UltraSharp",  # Default upscaler, adjust if needed
        "upscaler_2": "None",
        "extras_upscaler_2_visibility": 0,
        "upscale_first": False,
        "imageList": image_list  # List of base64-encoded images
    }

    # Send the request to the API
    response = requests.post(UPSCALE_API_URL, json=payload)

    # Log the API response for debugging
    print(f"API Response: {response.status_code}")
    if response.status_code != 200:
        print(f"Failed to upscale batch of images. Response: {response.text}")
        return

    try:
        # Get the base64-encoded upscaled images from the API response
        upscaled_images = response.json().get("images", [])

        # Save each upscaled image
        for idx, upscaled_image_data in enumerate(upscaled_images):
            image_binary = base64.b64decode(upscaled_image_data)
            output_filename = os.path.join(OUTPUT_DIR, f"upscaled_{os.path.basename(image_paths[idx])}")

            with open(output_filename, "wb") as img_file:
                img_file.write(image_binary)
            print(f"Upscaled image saved to: {output_filename}")
    except Exception as e:
        print(f"Error processing the response for the batch. Error: {e}")

# Gather all image paths from the INPUT_DIR
image_files = [os.path.join(INPUT_DIR, f) for f in os.listdir(INPUT_DIR) if f.endswith((".png", ".jpg", ".jpeg"))]

# Check if there are images to process
if image_files:
    # Call the function to upscale the batch of images
    upscale_images_batch(image_files)
else:
    print("No images found to upscale.")

print("Batch upscaling process complete.")

