# ATS Resume Analyzer

A deterministic, rule-based Applicant Tracking System (ATS) resume analyzer featuring a cross-platform Flutter Web frontend, a high-performance FastAPI Python backend, and a companion Google Chrome extension.

---

## Architecture Overview

```
Google Chrome Extension (popup.html / popup.js)
       ↓  (chrome.tabs.create: opens http://localhost:57720/)
Flutter Web (Chrome, Port 57720)
       ↓  (HTTP POST multipart/form-data: resume file + job_description)
FastAPI Backend (Port 8000, /analyze/)
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
Flutter Results UI (Score gauge, Breakdown progress bars, Matched/Missing skill chips)
```

---

## Project Structure

```
ats_system/
├── backend/                  # FastAPI Python backend
│   ├── app/                  # Application core, models, endpoints, ATS engine
│   │   ├── api/              # /analyze/, /health/, /version/ routers
│   │   ├── core/             # Configuration & constants
│   │   ├── models/           # Pydantic schemas & response contracts
│   │   └── services/         # ATS engine, scorer, normalizer, matcher
│   ├── parser/               # PDF & DOCX text extraction and section parsing
│   ├── tests/                # Pytest unit & endpoint integration test suite
│   ├── requirements.txt      # Python dependencies
│   └── .env.example          # Backend environment variable template
├── flutter_app/              # Flutter Web frontend
│   ├── lib/                  # Dart source files
│   │   ├── core/             # ApiConfig (points to http://localhost:8000)
│   │   ├── models/           # AtsAnalysisResult deserialization models
│   │   ├── services/         # AtsApiService multipart HTTP client
│   │   ├── ats_screen.dart   # Main interactive ATS UI
│   │   └── main.dart         # Flutter entrypoint
│   ├── test/                 # Flutter unit, widget, and mock API tests
│   ├── web/                  # Flutter Web HTML host and manifest
│   └── pubspec.yaml          # Flutter dependencies (SDK >=3.0.0 <4.0.0)
├── extension/                # Google Chrome Extension (Manifest V3)
│   ├── manifest.json         # Extension metadata, permissions & host permissions
│   ├── popup.html            # Extension popup launcher interface
│   └── popup.js              # Launches Flutter Web on http://localhost:57720/
├── run_project.bat           # 1-click Windows launcher (starts Backend & Flutter Web)
├── stop_project.bat          # 1-click Windows stopper (terminates ports 8000 & 57720)
├── .env.example              # Root environment template
└── .gitignore                # Git ignore rules for Python, Flutter, IDEs, and OS
```

---

## Setup Requirements

- **Operating System**: Windows 10/11 (or macOS / Linux)
- **Python**: 3.10, 3.11, 3.12, 3.13, or 3.14 (with `pip`)
- **Flutter SDK**: 3.x (channel `stable`, compatible with Dart `>=3.0.0 <4.0.0`)
- **Google Chrome**: Latest version (required for Flutter Web and the extension)
- **Git**: 2.30+

---

## Port Allocation

| Component | Host / Port | Description |
|---|---|---|
| **FastAPI Backend** | `http://127.0.0.1:8000` | REST API handling parsing, skill matching, and scoring |
| **Flutter Web** | `http://localhost:57720` | Web frontend UI explicitly bound to port 57720 |
| **Chrome Extension** | Browser Popup | Targets and opens `http://localhost:57720/` |

> [!IMPORTANT]
> **Why Port 57720?**
> The Chrome Extension's popup launcher specifically targets `http://localhost:57720/`. Flutter Web must be started with `--web-port 57720` so the extension connects seamlessly without `ERR_CONNECTION_REFUSED`.

---

## 1-Click Quickstart (Windows)

To launch both the FastAPI backend (port 8000) and Flutter Web (port 57720) in Google Chrome:

```cmd
run_project.bat
```

To cleanly terminate all running ATS processes (both port 8000 and port 57720):

```cmd
stop_project.bat
```

---

## Manual Developer Setup

### 1. Backend Setup

```cmd
cd backend
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

- **Health Check**: [http://127.0.0.1:8000/health/](http://127.0.0.1:8000/health/)
- **Swagger Documentation**: [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

### 2. Frontend Setup

```cmd
cd flutter_app
flutter pub get
flutter run -d chrome --web-port 57720
```

- **Application URL**: [http://localhost:57720](http://localhost:57720)

### 3. Chrome Extension Setup

1. Open Google Chrome and navigate to `chrome://extensions/`.
2. Toggle on **Developer mode** in the top right corner.
3. Click **Load unpacked** in the top left.
4. Select the `extension` folder located at the root of this project:
   `C:\path\to\ats_system\extension`
5. The **ATS Resume Analyzer** icon will appear in your Chrome toolbar.
6. Click the extension icon to view the popup card, then click **Open ATS Analyzer** to launch the Flutter Web app on port 57720.

---

## Running Tests

### Backend Unit & Integration Tests (186 passing tests):

```cmd
cd backend
pytest
```

Verifies:
- Text extraction from PDFs and DOCX files
- Accurate date extraction isolating education dates from professional work experience
- Strict skill token boundary matching (no false positives)
- CORS preflight responses for `http://localhost:57720` and Chrome Extension origins

### Frontend Tests & Static Analysis:

```cmd
cd flutter_app
flutter analyze
flutter test
```

Verifies:
- 0 lint or analyzer errors
- JSON deserialization of ATS analysis response
- Score clamping and match rating calculations
- Multipart upload request formatting with both bytes and streamed data
- Error banner presentation on backend failures

---

## Troubleshooting

### 1. `flutter pub get` version solving failed on git clone
- **Cause**: Outdated or mismatched SDK constraints in local cache.
- **Solution**: The `pubspec.yaml` environment is configured with `sdk: ">=3.0.0 <4.0.0"`. Run `flutter pub get` from inside `flutter_app/`. If needed, run `flutter clean` then `flutter pub get`.

### 2. Port already in use (57720 or 8000)
- **Cause**: A previous Uvicorn or Dart process remained open in the background.
- **Solution**: Run `stop_project.bat`, which terminates listeners on both 8000 and 57720. Alternatively, run:
  ```cmd
  for /f "tokens=5" %a in ('netstat -aon ^| findstr ":8000 "') do taskkill /F /PID %a
  for /f "tokens=5" %a in ('netstat -aon ^| findstr ":57720 "') do taskkill /F /PID %a
  ```

### 3. Extension opens Flutter but shows "This site can't be reached"
- **Cause**: Flutter Web was started without `--web-port 57720`.
- **Solution**: Always run `flutter run -d chrome --web-port 57720` (or use `run_project.bat`).

### 4. CORS Errors in Browser Console
- **Cause**: Backend CORS middleware not recognizing the requesting origin.
- **Solution**: The backend in `app/main.py` is configured with `allow_origins=["*"]` and credentials enabled. Ensure the backend is running on `http://127.0.0.1:8000`.

### 5. Windows / OneDrive File Lock on `build\flutter_assets`
- **Cause**: Background processes holding open handles on generated files.
- **Solution**: `run_project.bat` automatically strips read-only attributes and purges stale build locks before building.
