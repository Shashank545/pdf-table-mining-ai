from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import PyPDF2
import os
import json
import re
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import tempfile



# Load environment variables
load_dotenv()



app = FastAPI()

# Setup Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv('AZURE_OPENAI_KEY'),
    azure_endpoint="https://damac-data-openai-2.openai.azure.com/",
    api_version="2023-08-01-preview",
)

deployment_name = "DataTeam-OAI"

def extract_pdf_text(file_path: str) -> str:
    full_text = ""
    with open(file_path, "rb") as file:
        pdf_reader = PyPDF2.PdfReader(file)
        for page in pdf_reader.pages:
            full_text += page.extract_text() or ""
    # print(full_text)
    return full_text

@app.post("/extract-all-tables/")
async def extract_topics(pdf_file: UploadFile = File(...)):
    # Save uploaded PDF to a temporary file
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(await pdf_file.read())
        temp_pdf_path = tmp.name

    raw_text = extract_pdf_text(temp_pdf_path)

    # Prepare prompts
    system_prompt = """
        You are a structured data extraction assistant that analyzes Meeting Minutes (MOM) PDF documents containing consistently formatted tables and sections. Your task is to extract tabular content from the following predefined sections and return it in a clean, structured JSON format.

        The PDF document may contain the following sections:
        1. MEETING MOM
        2. ATTENDEES
        3. APOLOGIZE FOR ATTENDANCE
        4. TOPICS COVERED
        5. REQUIRED SIGNATURES

        For each section, map each table column accurately to its corresponding JSON key as described below:

        - MEETING MOM
        JSON Keys:
            - "Meeting Reference"
            - "Purpose of the Meeting"
            - "Location"
            - "Meeting starting date"
            - "Meeting end date"
            - "No of Attendance"
            - "Quorum"
            - "Rapporteur"
            - "Chairperson"

        - ATTENDEES
        JSON Keys:
            - "Name"
            - "Title"
            - "Company / Organization"

        - APOLOGIZE FOR ATTENDANCE
        JSON Keys:
            - "Name"
            - "Title"
            - "Company / Organization"
            - "Comment"

        - TOPICS COVERED
        JSON Keys:
            - "Topic"
            - "Discussion"
            - "Recommendation"
            - "In‐charge"
            - "Start Date"
            - "Voting result"

        - REQUIRED SIGNATURES
        JSON Keys:
            - "Rapporteur"
            - "Chairperson"

        📌 Important Instructions:
        - Only extract structured tabular data from the relevant sections.
        - Maintain the section order and hierarchy as listed above.
        - Each section should be a separate top-level key in the JSON.
        - If a section is missing, include an empty array for that section.
        - Do not stop until you have extracted **all available rows** from each section.
        - Continue extracting until the end of the provided text.
        - Do not summarize or omit any repeating rows.
        - Extract and return **each topic or row individually**, even if they appear repetitive.
        - If the number of rows is long, continue generating until all rows are processed.
        - It is acceptable to return a long JSON. Do not summarize or truncate data.




        Return your response in the following JSON structure:

        ```json
        {
        "meeting_mom": [...],
        "attendees": [...],
        "apologize_for_attendance": [...],
        "topics_covered": [...],
        "required_signatures": [...]
        }

        """


    user_prompt = f"""
    Below is the full extracted text from a Meeting MOM PDF document. Based on the structure and section rules shared earlier, extract all available sections and convert them to structured JSON format.

    Make sure that:
    - Each section is represented by its own top-level key in the output.
    - Each row from a table is converted to a dictionary using the predefined JSON keys.
    - The output follows the exact JSON schema described in your system instructions.
    - Omit any non-tabular free-text content unless it's part of a section's table row.

    --- START OF TEXT ---
    {raw_text}
    --- END OF TEXT ---
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]

    # Call Azure OpenAI
    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0.0,
            max_tokens=16384
        )

        # print(response)

        response_text = response.choices[0].message.content.strip()

        # Remove code fencing if any
        cleaned_response = re.sub(r"^```(?:json)?\n", "", response_text)
        cleaned_response = re.sub(r"\n```$", "", cleaned_response)

        # Parse to JSON
        topics_json = json.loads(cleaned_response)

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

    # Return parsed response
    return {"topics": topics_json}




# NEW ENDPOINT: /extract-topics-covered/
@app.post("/extract-topics-covered/")
async def extract_topics_covered(pdf_file: UploadFile = File(...)):
    try:
        # Save uploaded PDF to temp file
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf_file.read())
            temp_pdf_path = tmp.name

        # Extract and clean text
        raw_text = extract_pdf_text(temp_pdf_path)
        # raw_text = re.sub(r"Page\s+\d+\s+of\s+\d+", "", raw_text)  # Remove page headers

        # Prompts
        system_prompt = """
        You are an intelligent assistant that extracts structured information from PDFs.
        Focus only on the 'TOPICS COVERED' section of a meeting minutes document.

        Extract all topics listed under this section, and return each as a structured JSON object with the following keys:
        - "Topic"
        - "Discussion"
        - "Recommendation"
        - "In‐charge"
        - "Start Date"
        - "Voting result"

        Rules:
        - Do NOT summarize or merge rows. Extract every topic row separately.
        - If a field is missing, return it as an empty string.
        - Continue extracting until all rows are processed. Do not stop early.
        - Return valid JSON array with one object per topic.
        - Only extract structured tabular data from the relevant sections.
        - Maintain the section order and hierarchy as listed above.
        - Each section should be a separate top-level key in the JSON.
        - If a section is missing, include an empty array for that section.
        - Do not stop until you have extracted **all available rows** from each section.
        - Continue extracting until the end of the provided text.
        - Do not summarize or omit any repeating rows.
        - Extract and return **each topic or row individually**, even if they appear repetitive.
        - If the number of rows is long, continue generating until all rows are processed.
        - It is acceptable to return a long JSON. Do not summarize or truncate data.

        Example Output:
        [
            {
                "Topic": "...",
                "Discussion": "...",
                "Recommendation": "...",
                "In‐charge": "...",
                "Start Date": "...",
                "Voting result": "..."
            },
            ...
        ]
        """

        user_prompt = f"""
        Below is the extracted text from a PDF MOM document.

        Your task is to extract the complete 'TOPICS COVERED' section, row by row, **starting at 'TOPICS COVERED' and ending just before 'REQUIRED SIGNATURES'**.

        Each row should be extracted and mapped to a JSON object with the specified fields.

        Return your result as a JSON array, with one object per topic.

        --- START OF TEXT ---
        {raw_text}
        --- END OF TEXT ---
        """


        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ]

        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0.0,
            max_tokens=16384
        )

        response_text = response.choices[0].message.content.strip()

        # Clean formatting
        cleaned_response = re.sub(r"^```(?:json)?\n", "", response_text)
        cleaned_response = re.sub(r"\n```$", "", cleaned_response)

        topics_json = json.loads(cleaned_response)

        return {"topics_covered": topics_json}

    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})