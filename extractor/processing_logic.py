# extractor/processing_logic.py

import fitz  # PyMuPDF
from pdf2image import convert_from_bytes
import pytesseract
from PIL import Image
import re
import io

# ------------------------
# Unified file processor
# ------------------------
def process_file(file_obj):
    """
    Processes a file (PDF or image) and returns structured data.
    Acts as the bridge between Django and your core extraction logic.
    """
    file_content = file_obj.read()
    file_type = file_obj.content_type

    # -------- PDF Processing --------
    if file_type == 'application/pdf':
        doc = fitz.open(stream=file_content, filetype="pdf")
        text = ""

        try:
            # Extract text page by page
            for page in doc:
                page_text = page.get_text("text")
                text += page_text + "\n"

            # If text is minimal, fallback to OCR for scanned PDF
            if len(text.strip()) < 50:
                images = convert_from_bytes(file_content, dpi=200)  # safer memory usage
                for img in images:
                    text += pytesseract.image_to_string(img, lang="eng") + "\n"

        except Exception:
            # Fallback OCR for any unexpected PDF issues
            images = convert_from_bytes(file_content, dpi=200)
            for img in images:
                text += pytesseract.image_to_string(img, lang="eng") + "\n"

        return extract_fields(text)

    # -------- Image Processing --------
    elif file_type in ['image/jpeg', 'image/png', 'image/tiff']:
        img = Image.open(io.BytesIO(file_content))
        text = pytesseract.image_to_string(img, lang="eng")
        return extract_fields(text)

    else:
        raise ValueError("Unsupported file type.")


# ------------------------
# Text extraction logic
# ------------------------
def extract_fields(text: str) -> dict:
    """
    Extract structured fields from raw OCR text.
    """
    data = {
        "University": "",
        "Enrollment No": "",
        "Student Name": "",
        "Course": "",
        "Branch": "",
        "Subjects": [],
        "Date": "",
        "Statement No": "",
        "Semester": "",
    }

    clean_text = re.sub(r'\s+', ' ', text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # University
    if "GUJARAT TECHNOLOGICAL UNIVERSITY" in text.upper():
        data["University"] = "Gujarat Technological University"

    # Enrollment No
    enroll_match = re.search(r"\b\d{11,}\b", clean_text)
    if enroll_match:
        data["Enrollment No"] = enroll_match.group(0)

        # Student Name (line above enrollment)
        for i, line in enumerate(lines):
            if enroll_match.group(0) in line:
                if i > 0 and lines[i-1].isupper() and len(lines[i-1].split()) > 1:
                    data["Student Name"] = lines[i-1].strip().title()

    # Course
    course_match = re.search(r"BACHELOR OF ENGINEERING", text, re.IGNORECASE)
    if course_match:
        data["Course"] = "Bachelor of Engineering"

    # Branch
    branch_match = re.search(
        r"Branch\s*[:\-]?\s*([A-Za-z\s]+)\s*\(?(?:Code[:\-]?\s*(\d+))?\)?",
        clean_text, re.IGNORECASE
    )
    if branch_match:
        data["Branch"] = branch_match.group(1).strip().title()
    else:
        # fallback guess
        for i, line in enumerate(lines):
            if "BACHELOR OF ENGINEERING" in line.upper() and i+1 < len(lines):
                possible_branch = lines[i+1].strip()
                if possible_branch.isupper() and "ENGINEERING" in possible_branch.upper():
                    data["Branch"] = possible_branch.title()
        if not data["Branch"]:
            data["Branch"] = "Computer Engineering"

    # Subjects
    subject_codes = re.findall(r"\b(314\d{4})\b", text)
    data["Subjects"] = sorted(list(set(subject_codes)))

    # Date
    date_match = re.search(r"DATE\s*:\s*([0-9\-A-Za-z]+)", text)
    if date_match:
        data["Date"] = date_match.group(1)

    # Statement No
    stmt_match = re.search(r"MAY-2025\s*([A-Z0-9]+)", text, re.IGNORECASE)
    if stmt_match:
        data["Statement No"] = stmt_match.group(1)

    # Semester
    sem_match = re.search(r"Sem\w*\s*[:\-]?\s*(\d+)", text, re.IGNORECASE)
    if sem_match:
        data["Semester"] = sem_match.group(1)
    else:
        data["Semester"] = "4"

    return data
