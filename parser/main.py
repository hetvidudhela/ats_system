"""
main.py
=======

WHY THIS FILE EXISTS:
    This is the ENTRY POINT of the Resume Parser module.
    
    It exposes ONE simple function: parse_resume(file_path)
    
    Your FastAPI teammate only needs to call this function.
    Everything else happens internally.

    The pipeline is:
        1. Validate the file
        2. Extract raw text (PDF or DOCX)
        3. Clean the text
        4. Detect resume sections
        5. Extract personal information
        6. Build and return a Resume object

HOW IT CONNECTS:
    - FastAPI backend will call: resume = parse_resume(file_path)
    - This function orchestrates ALL other modules.
    - It returns a Resume object (or a dict with an error).

HOW TO TEST:
    Run this file directly:
        python main.py
    
    It will parse the sample resumes in the sample_resumes/ folder.
"""

import os
import json

# Import our modules
from validators.file_validator import validate_file, get_file_extension
from parsers.pdf_parser import extract_text_from_pdf
from parsers.docx_parser import extract_text_from_docx
from extractor.text_cleaner import clean_text
from extractor.section_detector import detect_sections
from extractor.info_extractor import (
    extract_email,
    extract_phone,
    extract_name,
    extract_linkedin,
    extract_github,
    extract_skills_list,
    extract_languages_list,
)
from models.resume_model import Resume


# ==========================================
# MAIN FUNCTION (PUBLIC API)
# ==========================================

def parse_resume(file_path: str) -> dict:
    """
    Parse a resume file and return structured data.
    
    This is the ONLY function your teammates need to call.
    It handles everything internally.
    
    Args:
        file_path (str): The path to the resume file (PDF or DOCX).
    
    Returns:
        dict: A dictionary with the parsing result:
            - If successful:
                {
                    "success": True,
                    "data": { ... resume data ... },
                    "error": ""
                }
            - If failed:
                {
                    "success": False,
                    "data": None,
                    "error": "Error message explaining what went wrong"
                }
    """

    # ---- Step 1: Validate the file ----
    validation_result = validate_file(file_path)
    
    if not validation_result["is_valid"]:
        return {
            "success": False,
            "data": None,
            "error": validation_result["error"],
        }
    
    # ---- Step 2: Extract raw text based on file type ----
    file_extension = get_file_extension(file_path)
    
    if file_extension == ".pdf":
        extraction_result = extract_text_from_pdf(file_path)
    elif file_extension == ".docx":
        extraction_result = extract_text_from_docx(file_path)
    else:
        return {
            "success": False,
            "data": None,
            "error": f"Unsupported file type: {file_extension}",
        }
    
    # Check if text extraction was successful
    if not extraction_result["success"]:
        return {
            "success": False,
            "data": None,
            "error": extraction_result["error"],
        }
    
    raw_text = extraction_result["text"]
    
    # ---- Step 3: Clean the extracted text ----
    cleaned_text = clean_text(raw_text)
    
    if not cleaned_text:
        return {
            "success": False,
            "data": None,
            "error": "No text could be extracted from the file after cleaning.",
        }
    
    # ---- Resume Validation Layer ----
    from validators.resume_validator import validate_resume_text
    validation = validate_resume_text(cleaned_text)
    if not validation["is_valid"]:
        return {
            "success": False,
            "data": None,
            "error": validation["error"],
        }
    
    # ---- Step 4: Detect resume sections ----
    sections = detect_sections(cleaned_text)
    
    # ---- Step 5: Extract personal information ----
    name = extract_name(cleaned_text)
    email = extract_email(cleaned_text)
    phone = extract_phone(cleaned_text)
    linkedin = extract_linkedin(cleaned_text)
    github = extract_github(cleaned_text)
    
    # Extract skills and languages as lists
    skills_list = extract_skills_list(sections.get("skills", ""))
    languages_list = extract_languages_list(sections.get("languages", ""))
    
    # ---- Step 6: Build the Resume object ----
    resume = Resume()
    
    # Set personal info
    resume.name = name
    resume.email = email
    resume.phone = phone
    resume.linkedin = linkedin
    resume.github = github
    
    # Set sections
    resume.skills = skills_list
    resume.education = sections.get("education", "")
    resume.experience = sections.get("experience", "")
    resume.projects = sections.get("projects", "")
    resume.certifications = sections.get("certifications", "")
    resume.achievements = sections.get("achievements", "")
    resume.languages = languages_list
    
    # Set raw text
    resume.raw_text = cleaned_text
    
    # ---- Step 7: Return the result ----
    return {
        "success": True,
        "data": resume.to_dict(),
        "error": "",
    }


# ==========================================
# HELPER: Parse and get Resume object directly
# ==========================================

def parse_resume_object(file_path: str):
    """
    Parse a resume and return the Resume object directly.
    
    This is a convenience function if someone prefers to work
    with the Resume object instead of a dict.
    
    Args:
        file_path (str): Path to the resume file.
    
    Returns:
        Resume or None: The Resume object, or None if parsing failed.
    """
    result = parse_resume(file_path)
    
    if result["success"]:
        # Reconstruct the Resume object from the dict
        resume = Resume()
        data = result["data"]
        resume.name = data["name"]
        resume.email = data["email"]
        resume.phone = data["phone"]
        resume.linkedin = data["linkedin"]
        resume.github = data["github"]
        resume.skills = data["skills"]
        resume.education = data["education"]
        resume.experience = data["experience"]
        resume.projects = data["projects"]
        resume.certifications = data["certifications"]
        resume.achievements = data["achievements"]
        resume.languages = data["languages"]
        resume.raw_text = data["raw_text"]
        return resume
    else:
        print(f"Parsing failed: {result['error']}")
        return None


# ==========================================
# DIRECT EXECUTION (for testing)
# ==========================================

if __name__ == "__main__":
    """
    When you run this file directly:
        python main.py
    
    It will try to parse any resume files found in the sample_resumes/ folder.
    """
    
    print("=" * 60)
    print("  ATS Resume Parser - Test Run")
    print("=" * 60)
    print()
    
    # Path to the sample resumes folder
    sample_folder = os.path.join(os.path.dirname(__file__), "sample_resumes")
    
    # Check if the folder exists
    if not os.path.exists(sample_folder):
        print(f"Sample folder not found: {sample_folder}")
        print("Please create a 'sample_resumes' folder and add PDF or DOCX files.")
        exit()
    
    # Get all files in the sample folder
    files = os.listdir(sample_folder)
    resume_files = [f for f in files if f.endswith(".pdf") or f.endswith(".docx")]
    
    if not resume_files:
        print("No PDF or DOCX files found in sample_resumes/ folder.")
        print("Please add some resume files to test.")
        exit()
    
    # Parse each file
    for filename in resume_files:
        file_path = os.path.join(sample_folder, filename)
        
        print(f"Parsing: {filename}")
        print("-" * 40)
        
        # Call our main function
        result = parse_resume(file_path)
        
        if result["success"]:
            # Print the parsed data as formatted JSON
            print(json.dumps(result["data"], indent=4, ensure_ascii=False))
        else:
            print(f"ERROR: {result['error']}")
        
        print()
        print("=" * 60)
        print()
