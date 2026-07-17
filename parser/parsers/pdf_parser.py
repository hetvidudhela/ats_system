"""
pdf_parser.py
=============

WHY THIS FILE EXISTS:
    This file is responsible for extracting text from PDF resume files.
    It uses PyMuPDF (imported as 'fitz') which is one of the fastest
    and most reliable PDF text extraction libraries in Python.

HOW IT CONNECTS:
    - main.py calls extract_text_from_pdf() after file validation passes.
    - The extracted text is then sent to text_cleaner.py for cleaning.
    - After cleaning, it goes to section_detector.py and info_extractor.py.
"""

import fitz  # PyMuPDF library - imported as 'fitz'


def extract_text_from_pdf(file_path: str) -> dict:
    """
    Extract all readable text from a PDF file.
    
    This function opens the PDF, goes through each page one by one,
    and collects all the text. The text from all pages is combined
    into a single string.
    
    Args:
        file_path (str): The path to the PDF file.
    
    Returns:
        dict: A dictionary with two keys:
            - "success" (bool): True if text was extracted successfully.
            - "text" (str): The extracted text (empty string if failed).
            - "error" (str): Error message if extraction failed.
    """
    
    try:
        # Open the PDF file
        pdf_document = fitz.open(file_path)

        # This will hold all the text from every page
        full_text = ""

        # Get the total number of pages
        total_pages = pdf_document.page_count

        # Loop through each page and extract text
        for page_number in range(total_pages):
            # Get the page object
            page = pdf_document[page_number]

            # Extract text from this page
            page_text = page.get_text()

            # Add this page's text to the full text
            # Add a newline between pages so they don't merge together
            full_text = full_text + page_text + "\n"

        # Close the PDF document (free memory)
        pdf_document.close()

        # Check if we actually got any text
        if full_text.strip() == "":
            return {
                "success": False,
                "text": "",
                "error": "PDF file contains no readable text. It may be a scanned image."
            }

        return {
            "success": True,
            "text": full_text,
            "error": ""
        }

    except Exception as error:
        # If anything goes wrong, return a helpful error message
        return {
            "success": False,
            "text": "",
            "error": f"Failed to read PDF file: {str(error)}"
        }
