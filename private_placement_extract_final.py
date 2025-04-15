import os
import json
import sys
import httpx
import re  # Import the regular expression module
import pymongo
from dotenv import load_dotenv
from google import genai
from google.genai import types
from pathlib import Path
from mongo_isaham import connect_isaham_db


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

def analyze_pdf_with_gemini(doc_url):
    """Send pdf to Gemini AI and get structured JSON data, with improved error handling."""
    with open("prompt.txt", "r", encoding='utf-8') as p:
        prompt = p.read()

    doc_data = doc_data = httpx.get(doc_url).content
    try:
        # Generate content using Gemini AI
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                temperature=0.5 # Low temperature for consistent outputs, low randomness
            ),
            contents=[types.Part.from_bytes(
                        data=doc_data,
                        mime_type='application/pdf'
                        ),
                        prompt])

        print(response.usage_metadata)
        match = re.search(r"\{.*}", response.text, re.DOTALL)

        if match:
            json_text = match.group(0)
        else:
            print("ERROR: Could not extract JSON from Gemini response.")
            json_text = "{}"

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
    
def analyze_contents_with_gemini(contents):
    """Send text contents to Gemini AI and get structured JSON data, with improved error handling."""
    with open("prompt.txt", "r", encoding='utf-8') as p:
        prompt = p.read()

    try:
        # Generate content using Gemini AI
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            config=types.GenerateContentConfig(
                temperature=0.5 # Low temperature for consistent outputs, low randomness
            ),
            contents=[types.Part.from_bytes(
                        data=contents,
                        mime_type='text/plain'
                        ),
                        prompt])

        print(response.usage_metadata)
        match = re.search(r"\{.*}", response.text, re.DOTALL)

        if match:
            json_text = match.group(0)
        else:
            print("ERROR: Could not extract JSON from Gemini response.")
            json_text = "{}"

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

def save_json(structured_data, symbol):
    # Change output file name to match the PDF file name
    output_file = os.path.join("json", f"{symbol}.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(structured_data, f, indent=4, ensure_ascii=False)  # Ensure UTF-8 encoding
        print(f"Extraction complete! Data saved to {output_file}")
    except Exception as e:
        print(f"ERROR: Error writing to file: {e}")
    
def get_latest_announcements(): ## helper function to get PRIVATE PLACEMENT docs using regex
    db = connect_isaham_db()
    latest = db.announcements.find(
        {"description": {"$regex": "PRIVATE PLACEMENT"}}
    ).sort("announcement_id", pymongo.DESCENDING).limit(25)  # Find announcements 10th to 20th sorted by date with regex on description
    return latest

def parse_private_placement_document(mongo_document): 
    entry = mongo_document 
    pdf_link = entry['pdf_link']
    symbol = entry['symbol']
    contents = str(entry['contents'][1]).encode('ascii', 'replace')  ## take 2nd one
    if pdf_link:
        json_text = analyze_pdf_with_gemini(pdf_link)
    else:
        json_text = analyze_contents_with_gemini(contents)
    save_json(json_text , symbol)

latest = get_latest_announcements()
parse_private_placement_document(latest[10])

