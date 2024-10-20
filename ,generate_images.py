import os
import time
import base64
import requests
import re

# API endpoint
API_URL = "http://0.0.0.0:7860/sdapi/v1/txt2img"

# Directory to save generated images
OUTPUT_DIR = "./generated_images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Path to the text file with prompts
PROMPT_FILE = "prompts.txt"

# Function to format and clean prompts from the file
def format_prompts(file_path):
    with open(file_path, "r") as file:
        lines = file.readlines()

    formatted_prompts = []
    current_prompt = ""

    # Regular expression to detect a line starting with a number
    prompt_start_pattern = re.compile(r'^\d+')

    for line in lines:
        line = line.strip()

        # If the line starts with a number, it's the start of a new prompt
        if prompt_start_pattern.match(line):
            if current_prompt:
                # Save the previous prompt before starting a new one
                formatted_prompts.append(current_prompt.strip())
            # Start a new prompt
            current_prompt = line
        else:
            # Otherwise, it's a continuation of the current prompt
            current_prompt += " " + line

    # Append the last prompt
    if current_prompt:
        formatted_prompts.append(current_prompt.strip())

    return formatted_prompts

# Function to generate an image using the API
def generate_image(prompt, filename):
    # Payload with minimal key parameters for image generation    
    payload = {
        "batch_size": 1,
        "cfg_scale": 1,
        "distilled_cfg_scale": 3.5,
        "sampler_name": "Euler",
        "scheduler": "Simple",
        "prompt": prompt,
        "steps": 25,
        "width": 1280,  
        "height": 800  
    }

    # Send request to the API
    response = requests.post(API_URL, json=payload)

    # Log the response for debugging
    print(f"API Response: {response.status_code}")
    if response.status_code != 200:
        print(f"Failed to generate image for prompt: '{prompt}'. Response: {response.text}")
        return

    # Get the base64 image string from the response
    try:
        image_data = response.json().get("images", [])[0]

        # Decode the base64 image data
        image_binary = base64.b64decode(image_data)

        # Save the binary data as an image file
        with open(filename, "wb") as img_file:
            img_file.write(image_binary)
        print(f"Image saved to: {filename}")
    except Exception as e:
        print(f"Error processing response for prompt: '{prompt}'. Error: {e}")

# Read and format prompts from the file, then generate images
prompts = format_prompts(PROMPT_FILE)

for index, prompt in enumerate(prompts):
    if prompt:
        # Create a unique filename for each image based on the prompt and index
        filename = os.path.join(OUTPUT_DIR, f"image_{index + 1}_{int(time.time())}.png")
        generate_image(prompt, filename)

        # Optional: Add a small delay between requests to avoid overloading the WebUI
        time.sleep(1)

print("Image generation complete.")

