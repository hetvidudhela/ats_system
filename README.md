# ATS Resume Analyzer

A deterministic, rule-based Applicant Tracking System (ATS) resume analyzer with a cross-platform Flutter Web frontend and a FastAPI Python backend.

---

## Architecture Overview

```
Flutter Web (Chrome)
       ↓  (HTTP POST multipart/form-data: resume file + job_description)
FastAPI Backend (/analyze/)
       ↓
Resume Parser (PyMuPDF for PDF, python-docx for DOCX)
       ↓
Job Description Analyzer (extracts required/preferred skills & domain keywords)
       ↓
Skill Normalizer & Matcher (exact, alias, and conservative fuzzy matching)
       ↓
Deterministic ATS Scorer (0-100 objective weighted components)
       ↓
Suggestions & Recommendations Generator
       ↓  (JSON response)
Flutter Results UI (Score circle, Breakdown progress bars, Matched/Missing skill chips)
```

---

## Technology Stack

- **Frontend**: Flutter (v3.44+) / Dart, Flutter Web (Chrome), Material 3 Design
- **Backend**: FastAPI, Uvicorn, Pydantic v2
- **Document Parsers**: PyMuPDF (`fitz`), `python-docx`
- **Matching & Normalization**: RapidFuzz, Regular Expressions
- **Testing**: Pytest, Flutter Test (`flutter test`, `flutter test -d chrome`)

---

## 1-Click Quickstart (Windows)

To launch both the FastAPI backend and Flutter Web frontend in Google Chrome:

```cmd
run_project.bat
```

To stop all running development processes:

```cmd
stop_project.bat
```

---

## Manual Setup & Execution

### 1. Backend Setup

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # On Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Check**: [http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup

```bash
cd flutter_app
flutter pub get
flutter run -d chrome
```

---

## Deterministic Scoring Model (100 Points Total)

The scoring algorithm is 100% deterministic and objective:

1. **Keywords & Skills Match (40 pts)**:
   - Required skills: 25 pts
   - Preferred skills: 10 pts
   - Domain keywords: 5 pts
2. **Experience Match (20 pts)**:
   - Evaluates years of experience against job description requirements.
3. **Project Relevance (15 pts)**:
   - Matches keywords and tech stack inside candidate project descriptions.
4. **Education Match (10 pts)**:
   - Compares candidate highest degree (e.g. Bachelor, Master, PhD) against requirements.
5. **Resume Structure & Formatting (10 pts)**:
   - Checks presence of standard ATS sections (Skills, Experience, Education, Projects).
6. **Content Quality & Contact (5 pts)**:
   - Verifies valid email, phone, links (LinkedIn/GitHub), and sufficient word count.

### Matching Safeguards:
- Strict token boundary matching (avoids false positives like `Java` matching `JavaScript`, `C` matching words like `career`, or `React` matching `React Native`).
- Negative intent detection (filters out phrasing like *"interested in learning Django"* so candidates are not credited with skills they don't have).

---

## Running Tests

### Backend Unit & Integration Tests:
```bash
cd backend
pytest
```
*(181 passing tests covering parsers, validators, API endpoints, and ATS engine)*

### Frontend Tests & Analysis:
```bash
cd flutter_app
flutter analyze
flutter test --no-pub
flutter test -d chrome test/services/ats_api_service_test.dart
```
