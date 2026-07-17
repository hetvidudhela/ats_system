# 📄 ATS Resume Parser

A **standalone Resume Parser & Data Extraction module** for the ATS Resume Analyzer project.

This module receives a resume file (PDF or DOCX) and returns structured JSON data. It is designed to be integrated into the FastAPI backend by a teammate.

---

## 📋 Table of Contents

- [Overview](#overview)
- [Folder Structure](#folder-structure)
- [Installation](#installation)
- [How to Run](#how-to-run)
- [How to Use (Integration)](#how-to-use-integration)
- [Example Output](#example-output)
- [Running Tests](#running-tests)
- [Supported Sections](#supported-sections)
- [Architecture](#architecture)

---

## 🔍 Overview

This parser does the following:

1. **Validates** the resume file (format, size, existence)
2. **Extracts** raw text from PDF (using PyMuPDF) or DOCX (using python-docx)
3. **Cleans** the text (removes junk characters, extra whitespace, etc.)
4. **Detects** resume sections (Skills, Education, Experience, etc.)
5. **Extracts** personal info (Name, Email, Phone, LinkedIn, GitHub)
6. **Returns** a structured Python dictionary (easily convertible to JSON)

---

## 📁 Folder Structure

```
parser/
│
├── parsers/                    # Text extraction from files
│   ├── __init__.py
│   ├── pdf_parser.py           # Extract text from PDF files
│   └── docx_parser.py          # Extract text from DOCX files
│
├── validators/                 # File validation
│   ├── __init__.py
│   └── file_validator.py       # Check file type, size, existence
│
├── extractor/                  # Text processing & data extraction
│   ├── __init__.py
│   ├── text_cleaner.py         # Clean raw extracted text
│   ├── section_detector.py     # Detect resume sections
│   └── info_extractor.py       # Extract name, email, phone, etc.
│
├── models/                     # Data models
│   ├── __init__.py
│   └── resume_model.py         # Resume data class
│
├── tests/                      # All test files
│   ├── __init__.py
│   ├── test_file_validator.py
│   ├── test_text_cleaner.py
│   ├── test_sections.py
│   ├── test_info_extractor.py
│   ├── test_pdf.py
│   ├── test_docx.py
│   ├── test_resume_model.py
│   └── test_main.py
│
├── sample_resumes/             # Sample resume files for testing
│
├── requirements.txt            # Python dependencies
├── README.md                   # This file
└── main.py                     # Entry point - parse_resume() function
```

---

## ⚙️ Installation

### Prerequisites

- Python 3.8 or higher

### Step 1: Clone the repository

```bash
git clone <repository-url>
cd ats_system/parser
```

### Step 2: Create a virtual environment (recommended)

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Required Libraries

| Library        | Version  | Purpose                        |
|---------------|----------|--------------------------------|
| PyMuPDF       | 1.25.4   | PDF text extraction            |
| python-docx   | 1.1.2    | DOCX text extraction           |
| pytest        | 8.4.1    | Running tests                  |

---

## 🚀 How to Run

### Quick Test with Sample Resumes

Place your resume files (PDF or DOCX) in the `sample_resumes/` folder, then run:

```bash
cd parser
python main.py
```

This will parse all resumes in the `sample_resumes/` folder and print the structured output.

### Run from Python Code

```python
from main import parse_resume

result = parse_resume("path/to/resume.pdf")

if result["success"]:
    print(result["data"])
else:
    print(result["error"])
```

---

## 🔗 How to Use (Integration)

**For the FastAPI teammate:**

You only need to call **one function**:

```python
from parser.main import parse_resume

# Parse a resume file
result = parse_resume(file_path)

# Check if parsing was successful
if result["success"]:
    resume_data = result["data"]  # This is a dictionary with all resume fields
    # Pass resume_data to the ATS Engine
else:
    error_message = result["error"]  # Human-readable error message
```

**That's it.** No need to understand the internal modules.

---

## 📤 Example Output

### Successful Parse

```json
{
    "success": true,
    "data": {
        "name": "Milan Rawal",
        "email": "milan@example.com",
        "phone": "+91 9876543210",
        "linkedin": "linkedin.com/in/milanrawal",
        "github": "github.com/milanrawal",
        "skills": [
            "Python",
            "Java",
            "SQL",
            "Flutter",
            "FastAPI"
        ],
        "education": "B.Tech in Computer Science\nXYZ University\n2020-2024",
        "experience": "Software Developer Intern at ABC Corp\nJan 2023 - Jun 2023",
        "projects": "ATS Resume Analyzer\nBuilt a resume parsing system...",
        "certifications": "AWS Cloud Practitioner\nGoogle IT Support",
        "achievements": "First place in college hackathon",
        "languages": [
            "English",
            "Hindi",
            "Gujarati"
        ],
        "raw_text": "Full cleaned text of the resume..."
    },
    "error": ""
}
```

### Failed Parse

```json
{
    "success": false,
    "data": null,
    "error": "Unsupported file type: '.txt'. Allowed types: .pdf, .docx"
}
```

---

## 🧪 Running Tests

### Run all tests

```bash
cd parser
pytest tests/ -v
```

### Run specific test files

```bash
# Test file validation
pytest tests/test_file_validator.py -v

# Test text cleaning
pytest tests/test_text_cleaner.py -v

# Test section detection
pytest tests/test_sections.py -v

# Test info extraction
pytest tests/test_info_extractor.py -v

# Test PDF parsing
pytest tests/test_pdf.py -v

# Test DOCX parsing
pytest tests/test_docx.py -v

# Test Resume model
pytest tests/test_resume_model.py -v

# Test full pipeline
pytest tests/test_main.py -v
```

---

## 📑 Supported Sections

The parser can detect these resume sections (with many heading variations):

| Section         | Detected Headings                                                |
|----------------|------------------------------------------------------------------|
| **Skills**      | Skills, Technical Skills, Key Skills, Core Skills, etc.          |
| **Education**   | Education, Academic Background, Qualification, etc.              |
| **Experience**  | Experience, Work Experience, Professional Experience, etc.       |
| **Projects**    | Projects, Academic Projects, Personal Projects, etc.             |
| **Certifications** | Certifications, Certificates, Courses, Training, etc.        |
| **Achievements** | Achievements, Accomplishments, Awards, Honors, etc.            |
| **Languages**   | Languages, Languages Known, Language Proficiency, etc.           |

---

## 🏗️ Architecture

```
                    ┌─────────────────┐
                    │   FastAPI Backend│
                    │   (Member 2)     │
                    └────────┬────────┘
                             │
                             │  parse_resume(file_path)
                             ▼
                    ┌─────────────────┐
                    │     main.py      │
                    │  (Orchestrator)  │
                    └────────┬────────┘
                             │
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
     ┌──────────────┐ ┌────────────┐ ┌────────────┐
     │  Validators   │ │  Parsers   │ │ Extractors │
     │               │ │            │ │            │
     │ file_validator│ │ pdf_parser │ │text_cleaner│
     │               │ │docx_parser │ │section_det.│
     │               │ │            │ │info_extract│
     └──────────────┘ └────────────┘ └─────┬──────┘
                                           │
                                           ▼
                                   ┌──────────────┐
                                   │    Models     │
                                   │              │
                                   │ resume_model │
                                   │ (Resume obj) │
                                   └──────┬───────┘
                                          │
                                          ▼
                                   ┌──────────────┐
                                   │  JSON Output  │
                                   │  → ATS Engine │
                                   └──────────────┘
```

---

## 👥 Team Integration Notes

- **This module is completely independent.** It has no dependency on FastAPI or Flutter.
- **FastAPI only needs to call `parse_resume(file_path)`** — that's the entire API.
- **The returned dict** can be directly serialized to JSON for API responses.
- **Error handling is built in.** The function never crashes — it always returns a result dict.

---

## 📝 License

This project is part of the ATS Resume Analyzer team project.
