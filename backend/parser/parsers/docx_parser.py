"""
docx_parser.py
==============

WHY THIS FILE EXISTS:
    This file is responsible for extracting text from DOCX (Word) resume files.
    It uses the python-docx library to read Word documents.
    
    A DOCX file is made up of paragraphs and tables.
    We extract text from BOTH so we don't miss any resume content.

HOW IT CONNECTS:
    - main.py calls extract_text_from_docx() after file validation passes.
    - The extracted text is then sent to text_cleaner.py for cleaning.
    - After cleaning, it goes to section_detector.py and info_extractor.py.
"""

from docx import Document


def extract_text_from_docx(file_path: str) -> dict:
    """
    Extract all readable text from a DOCX file.
    
    This function reads all paragraphs and all tables from the
    Word document and combines them into a single string.
    
    Args:
        file_path (str): The path to the DOCX file.
    
    Returns:
        dict: A dictionary with three keys:
            - "success" (bool): True if text was extracted successfully.
            - "text" (str): The extracted text (empty string if failed).
            - "error" (str): Error message if extraction failed.
    """
    
    try:
        # Open the DOCX file
        document = Document(file_path)

        # This list will hold all lines of text
        all_text_lines = []

        # ----- Step 1: Extract text from paragraphs -----
        for paragraph in document.paragraphs:
            # Get the text from this paragraph
            line = paragraph.text.strip()
            
            # Only add non-empty lines
            if line:
                all_text_lines.append(line)

        # ----- Step 2: Extract text from tables -----
        # Some resumes use tables for layout (e.g., skills in columns)
        for table in document.tables:
            for row in table.rows:
                # Collect all cell text in this row
                row_text_parts = []
                for cell in row.cells:
                    cell_text = cell.text.strip()
                    if cell_text:
                        row_text_parts.append(cell_text)
                
                # Join the cells of this row with a space
                if row_text_parts:
                    row_text = " | ".join(row_text_parts)
                    all_text_lines.append(row_text)

        # Combine all lines into a single string
        full_text = "\n".join(all_text_lines)

        # Check if we got any text at all
        if full_text.strip() == "":
            return {
                "success": False,
                "text": "",
                "error": "DOCX file contains no readable text."
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
            "error": f"Failed to read DOCX file: {str(error)}"
        }
