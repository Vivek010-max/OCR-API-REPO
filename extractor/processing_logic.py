# extractor/processing_logic.py
import re
import io

# --- Lightweight extraction logic stays at top ---
def extract_fields(text: str) -> dict:
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

    # Student Name
    if enroll_match:
        for i, line in enumerate(lines):
            if enroll_match.group(0) in line:
                if i > 0 and lines[i-1].isupper() and len(lines[i-1].split()) > 1:
                    data["Student Name"] = lines[i-1].strip().title()

    # Course
    course_match = re.search(r"BACHELOR OF ENGINEERING", text, re.IGNORECASE)
    if course_match:
        data["Course"] = "Bachelor of Engineering"
    
    # Branch
    branch_match = re.search(r"Branch\s*[:\-]?\s*([A-Za-z\s]+)\s*\(?(?:Code[:\-]?\s*(\d+))?\)?", clean_text, re.IGNORECASE)
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

# --- Deferred heavy imports for low-memory containers ---
def process_file(file_obj):
    import pytesseract
    from PIL import Image
    import fitz  # PyMuPDF
    from pdf2image import convert_from_bytes
    import datetime

    start_time = datetime.datetime.now()
    print(f"[OCR] Processing started at {start_time}")

    pytesseract.pytesseract.tesseract_cmd = r'/usr/bin/tesseract'

    file_content = file_obj.read()
    file_type = file_obj.content_type
    text = ""

    try:
        # PDF processing
        if file_type == 'application/pdf':
            doc = fitz.open(stream=file_content, filetype="pdf")
            for page in doc:
                text += page.get_text("text") + "\n"

            if len(text.strip()) < 50:
                # Fallback to OCR
                images = convert_from_bytes(file_content)
                for img in images:
                    text += pytesseract.image_to_string(img, lang="eng") + "\n"

        # Image processing
        elif file_type in ['image/jpeg', 'image/png', 'image/tiff']:
            img = Image.open(io.BytesIO(file_content))
            text = pytesseract.image_to_string(img, lang="eng")

        else:
            raise ValueError("Unsupported file type.")

    except Exception as e:
        print(f"[OCR] Exception: {e}")
        text = ""

    end_time = datetime.datetime.now()
    print(f"[OCR] Processing finished at {end_time}, duration: {end_time - start_time}")

    return extract_fields(text)
