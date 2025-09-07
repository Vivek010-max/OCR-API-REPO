import re
import io

def extract_fields(text: str) -> dict:
    """
    Extracts structured fields from raw text.
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
        "Result": "",
        "SPI": ""
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

    # Student Name
    if enroll_match:
        for i, line in enumerate(lines):
            if enroll_match.group(0) in line:
                if i > 0 and lines[i-1].isupper() and len(lines[i-1].split()) > 1:
                    data["Student Name"] = lines[i-1].strip().title()

    # Course
    if re.search(r"BACHELOR OF ENGINEERING", text, re.IGNORECASE):
        data["Course"] = "Bachelor of Engineering"
    
    # Branch
    branch_match = re.search(
        r"Branch\s*[:\-]?\s*([A-Za-z\s]+)\s*\(?(?:Code[:\-]?\s*(\d+))?\)?",
        clean_text, re.IGNORECASE
    )
    if branch_match:
        data["Branch"] = branch_match.group(1).strip().title()
    else:
        course_line_index = -1
        for i, line in enumerate(lines):
            if "BACHELOR OF ENGINEERING" in line.upper():
                course_line_index = i
                break
        if course_line_index != -1 and course_line_index + 1 < len(lines):
            possible_branch = lines[course_line_index + 1].strip()
            if possible_branch.isupper() and "ENGINEERING" in possible_branch.upper():
                data["Branch"] = possible_branch.title()
        
    if not data["Branch"]:
        data["Branch"] = "Computer Engineering"
                
    # Subjects
    subject_codes = re.findall(r"\b(314\d{4})\b", text)
    data["Subjects"] = sorted(set(subject_codes))

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
    data["Semester"] = sem_match.group(1) if sem_match else "4"
        
    # Result
    result_match = re.search(r"Result\s*[:\-]?\s*(PASS|FAIL|ATKT)", text, re.IGNORECASE)
    if result_match:
        data["Result"] = result_match.group(1).upper()
    else:
        if "PASS" in text.upper():
            data["Result"] = "PASS"
        elif "FAIL" in text.upper():
            data["Result"] = "FAIL"
        elif "ATKT" in text.upper():
            data["Result"] = "ATKT"

    # SPI
    spi_match = re.search(r"S[\s\.]*P[\s\.]*I\s*[:\-]?\s*([0-9]+\.[0-9]+)", text, re.IGNORECASE)
    if spi_match:
        data["SPI"] = spi_match.group(1)

    return data
    

# --- Unified file processor (with lazy imports) ---
def process_file(file_obj):
    """
    Processes a file (image or PDF) and returns structured data.
    Heavy libs are imported only when needed.
    """
    file_type = file_obj.content_type

    if file_type == 'application/pdf':
        text = ""
        try:
            pdf_bytes = file_obj.read()

            import fitz  # PyMuPDF
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            for page in doc:
                text += page.get_text("text") + "\n"
        except Exception:
            from pdf2image import convert_from_bytes
            import pytesseract

            images = convert_from_bytes(pdf_bytes, first_page=1, last_page=2)
            for img in images:
                text += pytesseract.image_to_string(img, lang="eng") + "\n"

        return extract_fields(text)

    elif file_type in ['image/jpeg', 'image/png', 'image/tiff']:
        img_bytes = file_obj.read()

        from PIL import Image
        import pytesseract

        img = Image.open(io.BytesIO(img_bytes))
        text = pytesseract.image_to_string(img, lang="eng")
        return extract_fields(text)

    else:
        raise ValueError("Unsupported file type.")
