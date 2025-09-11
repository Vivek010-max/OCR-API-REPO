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

    # Normalize whitespace and build helpers
    clean_text = re.sub(r"\s+", " ", text)
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    # University
    if "GUJARAT TECHNOLOGICAL UNIVERSITY" in text.upper():
        data["University"] = "Gujarat Technological University"

    # Enrollment No
    enroll_match = (
        re.search(r"Enrollment\s*No\.?\s*[:\-]?\s*(\d{11,12})", text, re.IGNORECASE)
        or re.search(r"\b(\d{11,12})\b", clean_text)
    )
    if enroll_match:
        data["Enrollment No"] = enroll_match.group(1)

    # Student Name
    name_match = re.search(
        r"Student\s*Name\s*[:\-]?\s*([A-Za-z][A-Za-z\s'.-]{4,})", text, re.IGNORECASE
    )
    if name_match:
        data["Student Name"] = name_match.group(1).strip().title()
    elif data["Enrollment No"]:
        for i, line in enumerate(lines):
            if data["Enrollment No"] in line:
                if i > 0:
                    prev = lines[i - 1].strip()
                    if sum(c.isalpha() for c in prev) >= 8 and not any(
                        ch.isdigit() for ch in prev
                    ):
                        data["Student Name"] = prev.title()
                break
    if not data["Student Name"]:
        candidates = [
            l
            for l in lines
            if l.isupper()
            and len(l.split()) >= 2
            and not any(ch.isdigit() for ch in l)
        ]
        if candidates:
            data["Student Name"] = candidates[0].title()

    # Course
    if re.search(r"BACHELOR OF ENGINEERING", text, re.IGNORECASE):
        data["Course"] = "Bachelor of Engineering"

    # Branch
    branch_match = re.search(
        r"Branch\s*[:\-]?\s*([A-Za-z\s]+?)\s*(?:\(|Code|$)",
        clean_text,
        re.IGNORECASE,
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
            if "ENGINEERING" in possible_branch.upper():
                data["Branch"] = possible_branch.title()

    # Subjects
    subject_codes = set(re.findall(r"\b(314\d{4})\b", text))
    if len(subject_codes) < 4:
        subject_codes.update(re.findall(r"\b(31\d{5})\b", text))
    data["Subjects"] = sorted(list(subject_codes))

    # Date
    date_match = (
        re.search(
            r"DATE\s*[:\-]?\s*([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})", text, re.IGNORECASE
        )
        or re.search(r"\b([0-9]{1,2}-[A-Za-z]{3}-[0-9]{4})\b", text)
    )
    if date_match:
        data["Date"] = date_match.group(1)

    # Statement No
    stmt_match = (
        re.search(
            r"Statement\s*No\.?\s*[:\-]?\s*([A-Z0-9]{6,})", text, re.IGNORECASE
        )
        or re.search(r"\bS\d{9,}\b", text)
    )
    if stmt_match:
        data["Statement No"] = stmt_match.group(1)

    # Semester
    sem_match = re.search(r"Sem(?:ester)?\s*[:\-]?\s*(\d{1,2})", text, re.IGNORECASE)
    if sem_match:
        data["Semester"] = sem_match.group(1)

    return data


# --- Image-only OCR processing ---
def process_file(file_obj):
    import pytesseract
    from PIL import Image, ImageOps, ImageFilter
    import datetime
    import os

    start_time = datetime.datetime.now()
    print(f"[OCR] Processing started at {start_time}")

    pytesseract.pytesseract.tesseract_cmd = r"/usr/bin/tesseract"
    os.environ.setdefault("TESSDATA_PREFIX", "/usr/share/tesseract-ocr/5/tessdata")

    file_content = file_obj.read()
    file_type = file_obj.content_type
    text = ""

    try:
        if file_type in ["image/jpeg", "image/png", "image/tiff"]:
            img = Image.open(io.BytesIO(file_content))

            # Normalize colorspace
            if img.mode not in ("L", "RGB"):
                img = img.convert("RGB")

            # Resize if too large
            max_side = 2200
            w, h = img.size
            scale = min(1.0, max_side / float(max(w, h)))
            if scale < 1.0:
                img = img.resize((int(w * scale), int(h * scale)))

            # Preprocessing
            if img.mode != "L":
                gray = img.convert("L")
            else:
                gray = img
            gray = ImageOps.autocontrast(gray)
            gray = gray.filter(ImageFilter.SHARPEN)
            bw = gray.point(lambda x: 0 if x < 140 else 255, "1")

            # OCR
            text = pytesseract.image_to_string(
                bw, lang="eng", config="--oem 1 --psm 6", timeout=20
            )
        else:
            raise ValueError("Only image files are supported.")

    except Exception as e:
        print(f"[OCR] Exception: {e}")
        text = ""

    end_time = datetime.datetime.now()
    print(
        f"[OCR] Processing finished at {end_time}, duration: {end_time - start_time}"
    )

    return extract_fields(text)
