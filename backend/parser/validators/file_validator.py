"""
file_validator.py
=================

WHY THIS FILE EXISTS:
    Before we try to parse any resume, we need to make sure the file
    is valid. This file checks:
    
    1. Does the file exist?
    2. Is it a supported format (PDF or DOCX)?
    3. Is the file empty?
    4. Is the file too large?
    5. Is the file corrupted or unreadable?

HOW IT CONNECTS:
    - main.py calls validate_file() FIRST before doing anything else.
    - If validation fails, parsing stops and an error message is returned.
    - If validation passes, the file goes to pdf_parser.py or docx_parser.py.
"""

import os


# ==========================================
# CONFIGURATION
# ==========================================

# Maximum file size allowed: 10 MB (in bytes)
MAX_FILE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

# Supported file extensions
ALLOWED_EXTENSIONS = [".pdf", ".docx"]


# ==========================================
# MAIN VALIDATION FUNCTION
# ==========================================

def validate_file(file_path: str) -> dict:
    """
    Validate a resume file before parsing.
    
    This function runs ALL validation checks on the file.
    If any check fails, it returns an error message.
    If all checks pass, it returns success.
    
    Args:
        file_path (str): The path to the resume file.
    
    Returns:
        dict: A dictionary with two keys:
            - "is_valid" (bool): True if file passed all checks.
            - "error" (str): Error message if validation failed, empty string if valid.
    """

    # Check 1: Does the file exist?
    existence_check = check_file_exists(file_path)
    if not existence_check["is_valid"]:
        return existence_check

    # Check 2: Is the extension supported?
    extension_check = check_file_extension(file_path)
    if not extension_check["is_valid"]:
        return extension_check

    # Check 3: Is the file empty?
    empty_check = check_file_not_empty(file_path)
    if not empty_check["is_valid"]:
        return empty_check

    # Check 4: Is the file too large?
    size_check = check_file_size(file_path)
    if not size_check["is_valid"]:
        return size_check

    # All checks passed!
    return {"is_valid": True, "error": ""}


# ==========================================
# INDIVIDUAL VALIDATION FUNCTIONS
# ==========================================

def check_file_exists(file_path: str) -> dict:
    """
    Check if the file exists on disk.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        dict: Validation result.
    """
    if not os.path.exists(file_path):
        return {
            "is_valid": False,
            "error": f"File not found: '{file_path}'"
        }
    
    # Also make sure it's a file (not a folder)
    if not os.path.isfile(file_path):
        return {
            "is_valid": False,
            "error": f"Path is not a file: '{file_path}'"
        }
    
    return {"is_valid": True, "error": ""}


def check_file_extension(file_path: str) -> dict:
    """
    Check if the file has a supported extension (.pdf or .docx).
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        dict: Validation result.
    """
    # Get the file extension and convert to lowercase
    _, extension = os.path.splitext(file_path)
    extension = extension.lower()

    if extension not in ALLOWED_EXTENSIONS:
        allowed = ", ".join(ALLOWED_EXTENSIONS)
        return {
            "is_valid": False,
            "error": f"Unsupported file type: '{extension}'. Allowed types: {allowed}"
        }
    
    return {"is_valid": True, "error": ""}


def check_file_not_empty(file_path: str) -> dict:
    """
    Check if the file is not empty (0 bytes).
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        dict: Validation result.
    """
    file_size = os.path.getsize(file_path)
    
    if file_size == 0:
        return {
            "is_valid": False,
            "error": "File is empty (0 bytes)."
        }
    
    return {"is_valid": True, "error": ""}


def check_file_size(file_path: str) -> dict:
    """
    Check if the file is within the allowed size limit.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        dict: Validation result.
    """
    file_size = os.path.getsize(file_path)
    max_size_mb = MAX_FILE_SIZE_BYTES / (1024 * 1024)

    if file_size > MAX_FILE_SIZE_BYTES:
        actual_size_mb = round(file_size / (1024 * 1024), 2)
        return {
            "is_valid": False,
            "error": f"File is too large: {actual_size_mb} MB. Maximum allowed: {max_size_mb} MB."
        }
    
    return {"is_valid": True, "error": ""}


def get_file_extension(file_path: str) -> str:
    """
    Get the lowercase file extension from a file path.
    
    This is a helper function used by main.py to decide
    which parser (PDF or DOCX) to use.
    
    Args:
        file_path (str): Path to the file.
        
    Returns:
        str: The file extension in lowercase (e.g., ".pdf", ".docx").
    """
    _, extension = os.path.splitext(file_path)
    return extension.lower()
