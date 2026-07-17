from pathlib import Path

# ----------------------------
# API
# ----------------------------

API_PREFIX = "/api"

# ----------------------------
# Resume Files
# ----------------------------

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".docx",
}

SUPPORTED_MIME_TYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
}

# ----------------------------
# Temporary Uploads
# ----------------------------

TEMP_UPLOAD_FOLDER = Path("uploads")

# ----------------------------
# Response Messages
# ----------------------------

SUCCESS = "Success"

INVALID_FILE = "Invalid file."

UNSUPPORTED_FILE = "Unsupported file type."

PARSER_FAILED = "Failed to parse resume."

ATS_FAILED = "Failed to analyze resume."