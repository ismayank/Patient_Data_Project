from django.shortcuts import render, redirect
from supabase import create_client, Client
import PyPDF2
import io
import re

def anonymize_patient_data_in_supabase(request):
    def generate_anonymous_id(counter):
        return f"ANON{str(counter).zfill(3)}"

    def extract_text_from_pdf(file_bytes):
        text = ""
        reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        for page in reader.pages:
            text += page.extract_text()
        return text

    def parse_patient_data(text):
        patient_data = {}
        anonymized_counter = 1
        patient_id_pattern = r"Patient ID\s*:\s*(\d+)"
        patient_name_pattern = r"Patient Name\s*:\s*([\w]+)"
        patient_age_pattern = r"Patient Age\s*:\s*(\d+\s*years)"
        gender_pattern = r"Gender\s*:\s*([\w]+)"
        ga_pattern = r"GA\s*:\s*([\d\w\s]+?)(?=\s*(?=Patient Name|Gender|BMI|Head|Brain|Heart|Spine|Abdominal wall|Urinary tract|Extremities|Conclusion|$))"
        bmi_pattern = r"BMI\s*:\s*(\d+)"
        findings_pattern = {
            "head": r"Head\s*:\s*(.+)",
            "brain": r"Brain\s*:\s*(.+)",
            "heart": r"Heart\s*:\s*(.+)",
            "spine": r"Spine\s*:\s*(.+)",
            "abdominal_wall": r"Abdominal wall\s*:\s*(.+)",
            "urinary_tract": r"Urinary tract\s*:\s*(.+)",
            "extremities": r"Extremities\s*:\s*(.+)",
            "conclusion": r"Conclusion\s*(.*)"
        }

        patient_id = re.search(patient_id_pattern, text)
        patient_name = re.search(patient_name_pattern, text)
        patient_age = re.search(patient_age_pattern, text)
        gestational_age = re.search(ga_pattern, text)
        bmi = re.search(bmi_pattern, text)
        gender = re.search(gender_pattern, text)

        patient_data["anonymous_id"] = generate_anonymous_id(anonymized_counter)
        patient_data["gestational_age"] = gestational_age.group(1) if gestational_age else "N/A"
        patient_data["age"] = patient_age.group(1) if patient_age else "N/A"
        patient_data["bmi"] = bmi.group(1) if bmi else "N/A"
        patient_data["gender"] = gender.group(1) if gender else "N/A"

        findings = {}
        for key, pattern in findings_pattern.items():
            match = re.search(pattern, text)
            findings[key] = match.group(1).strip() if match else "N/A"

        patient_data["examination_findings"] = findings
        return patient_data
    

    url = "https://yanbgbevqolqihyczqei.supabase.co"
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InlhbmJnYmV2cW9scWloeWN6cWVpIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTczNDQyNzIwNSwiZXhwIjoyMDUwMDAzMjA1fQ.oLMdd3kMaDAtEZaoczV5eTX1ctwo4s4lj-5E61qqqI0"
    supabase: Client = create_client(url, key)

    try:
        bucket_name = "Patient_PDF_Reports"
        print(f"Fetching PDF files from the bucket: {bucket_name}")
        pdf_files = supabase.storage.from_(bucket_name).list()
        print(f"Found {len(pdf_files)} PDF files in the bucket.")
    except Exception as e:
        print(f"Error fetching PDF files from Supabase bucket: {e}")

    all_patient_data = []

    for pdf_file in pdf_files:
        print(f"Processing file: {pdf_file['name']}")

        try:
            file_name = pdf_file['name']
            file_data = supabase.storage.from_(bucket_name).download(file_name)
            file_bytes = file_data['data'] if isinstance(file_data, dict) and 'data' in file_data else file_data

            print(f"File {file_name} downloaded successfully.")
            pdf_text = extract_text_from_pdf(file_bytes)
            patient_data = parse_patient_data(pdf_text)
            all_patient_data.append(patient_data)

        except Exception as e:
            print(f"Error processing file {pdf_file['name']}: {e}")

    return render(request, 'patient_data_list.html', {'patients': all_patient_data})
