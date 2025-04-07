import os
import json
import sys
import re  # Import the regular expression module
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path

# Load environment variables
load_dotenv(os.path.join(os.path.expanduser("~") , ".passkey" , ".env"))
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")  # Using GOOGLE_API_KEY

if not GOOGLE_API_KEY:
    print("Error: Missing GOOGLE_API_KEY in .env file")
    sys.exit(1)

# Configure Gemini API
try:
    client = genai.Client(api_key=GOOGLE_API_KEY)
except Exception as e:
    print(f"Error configuring Gemini API: {e}")
    sys.exit(1)

def analyze_pdf_with_gemini(pdf_path):
    """Send pdf to Gemini AI and get structured JSON data, with improved error handling."""

    with open("prompt.txt", "r", encoding='utf-8') as p:
        prompt = p.read()

    # Upload the PDF using the File API
    pdf_file = client.files.upload(
        file=pdf_path,
        )

    try:
        # Generate content using Gemini AI
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                temperature=0.5 # Low temperature for consistent outputs, low randomness
            ),
            contents=[pdf_file , prompt]  
        )

        print(response.usage_metadata)
        match = re.search(r"\{.*}", response.text, re.DOTALL)

        if match:
            json_text = match.group(0)
        else:
            print("ERROR: Could not extract JSON from Gemini response.")
            json_text = "{}"

        json_Sector = "{}"

        # Parse JSON
        try:
            json_data = json.loads(json_text)
            return json_data

        except json.JSONDecodeError as e:
            print(f"ERROR: JSON decoding error: {e}")
            return json_data
        
    except Exception as e:
        print(f"ERROR: Gemini processing failed: {e}")
        return {}


def save_json(structured_data, pdf_path, sector_flag = False):
    # Change output file name to match the PDF file name
    pdf_file_name = os.path.splitext(os.path.basename(pdf_path))[0]  # Get PDF file name without extension
    
    if not sector_flag:
        output_file = os.path.join("json", f"{pdf_file_name}.json")

    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=4, ensure_ascii=False)  # Ensure UTF-8 encoding
        print(f"Extraction complete! Data saved to {output_file}")
    except Exception as e:
        print(f"ERROR: Error writing to file: {e}")
    


def extract_pdf_financial(pdf_name):
   
    pdf_path = os.path.join("pdf", pdf_name)  # Replace with the actual path to your PDF file

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)

    print(f"Processing PDF: {pdf_path}")

    # save data from AI
    json_text = analyze_pdf_with_gemini(pdf_path)
    save_json(json_text , pdf_path)

if __name__ == "__main__":
    # Specify the PDF path here:
    pdf_path = os.path.join("pdf", "Hektar.pdf")  # Replace with the actual path to your PDF file

    if not os.path.exists(pdf_path):
        print(f"Error: PDF file '{pdf_path}' not found.")
        sys.exit(1)

    print(f"Processing PDF: {pdf_path}")

    # save data from AI
    json_text = analyze_pdf_with_gemini(pdf_path)
    save_json(json_text , pdf_path)


