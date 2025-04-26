
# 📄 AI-Powered PDF Table and Information Extraction API

This project is a **FastAPI-based microservice** that uses **Azure OpenAI GPT models** to perform **structured data extraction** from uploaded PDF files — specifically for Meeting Minutes (MOM) documents.  
It allows secure extraction of tables like attendees, topics covered, meeting details, and more into clean, structured JSON formats.

---

## 🚀 Features

- Upload a PDF file (Meeting MOM format) via a secure API.
- Extract **all structured tables** (Meeting Details, Attendees, Apologies, Topics, Signatures).
- Extract **only "Topics Covered"** table separately if needed.
- Uses **Azure OpenAI's GPT model** for intelligent, highly accurate extraction.
- Secured with **API Key Authentication**.
- Error handling, logging, and file cleanup included.
- Automatic temp file cleanup after extraction.

---

## 📂 Project Structure

```bash
.
├── app/                # Core FastAPI app (defined in code)
├── data_samples/       # Contains sample PDF files for testing
│   ├── sample1.pdf
│   ├── sample2.pdf
│   └── ...
├── .gitignore
├── .gitkeep            # Empty placeholder if required
├── README.md
└── requirements.txt    # Python dependencies
```

---

## 📂 Data Samples Storage

You can store PDF sample files inside the `data_samples/` folder to test your API.

Alternatively, if you prefer to use **Google Drive** securely for storing sample PDFs:
- Create a private Google Drive folder.
- Share it privately (only accessible to your account or service accounts).
- Use libraries like `gdown`, `pydrive`, or Google Drive API to download the PDF files during runtime.
- Example (using `gdown`):
    ```bash
    pip install gdown
    gdown --id FILE_ID_FROM_GOOGLE_DRIVE
    ```
- **Tip:** Make sure to restrict access using permissions and access tokens when connecting programmatically.





## ⚙️ Setup and Installation

### 1. Clone the Repository

```bash
git clone https://github.com/Shashank545/pdf-table-mining-ai
cd pdf-table-mining-ai
```

### 2. Create a Python Virtual Environment (recommended)

```bash
python3 -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

---

## 🔑 Environment Variables

Create a `.env` file in the root directory with the following content:

```env
AZURE_OPENAI_KEY=your-azure-openai-api-key
AI_API_KEY=your-custom-api-key-for-authentication
```

---

## 🛡️ Authentication

Pass the key in request headers:

```http
X-API-Key: your-api-key
```

---

## 📚 API Endpoints

| Endpoint                     | Description                               |
|-------------------------------|-------------------------------------------|
| POST `/extract-all-tables/`   | Extracts all predefined sections from MOM PDFs |
| POST `/extract-topics-covered/` | Extracts only 'Topics Covered' section   |


### 1. Extract All Structured Tables

- **POST** `/extract-all-tables/`
- **Purpose**: Extract *Meeting Details*, *Attendees*, *Apologies*, *Topics Covered*, and *Required Signatures*.

### 2. Extract Only "Topics Covered"

- **POST** `/extract-topics-covered/`
- **Purpose**: Extract only the *Topics Covered* section.

---

## 🛠️ How It Works Internally

1. **Upload PDF** → Uploaded via FastAPI file upload.
2. **Text Extraction** → `PyPDF2` library extracts raw text from the PDF.
3. **Prompt Engineering** → Predefined system prompts and user prompts guide the LLM.
4. **Azure OpenAI Call** → A chat completion API call generates structured JSON.
5. **Post-processing** → Cleans and validates JSON output.
6. **Respond** → Returns clean JSON via API.

---

## 📋 Important Notes

- Only `.pdf` files are accepted (validation enforced).
- Secure API Key header is mandatory.
- Extraction is based on standard Meeting MOM templates.
- If sections are missing in the PDF, empty arrays are returned.

---

## 🧹 Error Handling

- Invalid File Format → Returns 400 Bad Request.
- Unauthorized Access → Returns 403 Forbidden.
- Extraction/LLM Errors → Returns 500 Internal Server Error with details logged.

---

## 🖥️ Local Development

Run the app locally with:

```bash
uvicorn app_prod:app_prod --reload
```


**API will be available at**

    - API docs: [http://localhost:8000/docs](http://localhost:8000/docs)

## 🔐 Security

- API key-based authentication (`X-API-Key` header required).
- Files are stored temporarily and deleted automatically after processing.
- No PDF files are saved permanently.



## 📦 Dependencies

- fastapi
- uvicorn
- python-dotenv
- openai (Azure OpenAI)
- PyPDF2
- tempfile
- logging
- re
- json


---

## 🧑‍💻 Author

- [Shashank's Workspace](https://shashank-e-profile.wixsite.com/worklife)
- [Shashank's GIT](https://github.com/Shashank545)
- [My Medium Page](https://medium.com/%40Immaculate_sha2nk)
- [Follow me on Linkedin](https://www.linkedin.com/in/shashank-s-sahoo)

---

# 🚀 Happy Building with AI!
_"The future belongs to those who build with data, dream with AI, and deploy with passion."_