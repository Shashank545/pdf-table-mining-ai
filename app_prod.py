from fastapi import FastAPI, UploadFile, File, HTTPException, Request, status, Depends
from fastapi.responses import JSONResponse
from fastapi.security import APIKeyHeader
import PyPDF2
import os
import json
import re
from datetime import datetime
from openai import AzureOpenAI
from dotenv import load_dotenv
import tempfile
import logging
from typing import Dict, Any

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


API_KEY_NAME = "X-API-Key"
api_key_header = APIKeyHeader(name=API_KEY_NAME, auto_error=False)

# Initialize FastAPI app
app_prod = FastAPI()

# Setup Azure OpenAI client
client = AzureOpenAI(
    api_key=os.getenv("AZURE_OPENAI_KEY"),
    azure_endpoint="https://damac-data-openai-2.openai.azure.com/",
    api_version="2023-08-01-preview",
)

deployment_name = "DataTeam-OAI"


async def get_api_key(api_key: str = Depends(api_key_header)):
    if api_key == os.getenv("AI_API_KEY"):
        return api_key
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate API KEY"
        )



def extract_pdf_text(file_path: str) -> str:
    full_text = ""
    try:
        with open(file_path, "rb") as file:
            pdf_reader = PyPDF2.PdfReader(file)
            for page in pdf_reader.pages:
                text = page.extract_text()
                if text:
                    full_text += text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise
    return full_text


def clean_llm_response(response_text: str) -> Any:
    try:
        cleaned_response = re.sub(r"^```(?:json)?\n", "", response_text)
        cleaned_response = re.sub(r"\n```$", "", cleaned_response)
        return json.loads(cleaned_response)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON: {e}")
        raise HTTPException(status_code=500, detail="Failed to parse JSON from LLM response.")


def create_chat_completion(system_prompt: str, user_prompt: str) -> Any:
    try:
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]
        response = client.chat.completions.create(
            model=deployment_name,
            messages=messages,
            temperature=0.0,
            max_tokens=16384,
        )
        return clean_llm_response(response.choices[0].message.content.strip())
    except Exception as e:
        logger.exception("Azure OpenAI request failed")
        raise HTTPException(status_code=500, detail="LLM request failed")


def validate_pdf_file(uploaded_file: UploadFile):
    if not uploaded_file.filename.endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are allowed.")


@app_prod.post("/extract-all-tables/")
async def extract_all_tables(pdf_file: UploadFile = File(...), api_key: str = Depends(get_api_key)):
    validate_pdf_file(pdf_file)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf_file.read())
            temp_path = tmp.name

        raw_text = extract_pdf_text(temp_path)

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

        structured_output = create_chat_completion(system_prompt, user_prompt)

        return JSONResponse(content={"topics": structured_output}, status_code=200)

    except Exception as e:
        logger.exception("Failed to extract all tables")
        raise HTTPException(status_code=500, detail="Extraction failed")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


@app_prod.post("/extract-topics-covered/")
async def extract_topics_covered(pdf_file: UploadFile = File(...),api_key: str = Depends(get_api_key)):
    validate_pdf_file(pdf_file)
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await pdf_file.read())
            temp_path = tmp.name

        raw_text = extract_pdf_text(temp_path)

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

        structured_output = create_chat_completion(system_prompt, user_prompt)

        return JSONResponse(content={"topics_covered": structured_output}, status_code=200)

    except Exception as e:
        logger.exception("Failed to extract topics covered")
        raise HTTPException(status_code=500, detail="Extraction failed")

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)
