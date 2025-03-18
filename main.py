from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pdfplumber
import docx
import shutil
import os
import re
from starlette.responses import JSONResponse
import uvicorn

app = FastAPI()


@app.get("/")
def home():
    return {"message": "FastAPI is running on Render!"}

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))  # Default 10000 but overridden by Render
    uvicorn.run(app, host="0.0.0.0", port=port)


# Enable CORS for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Change this to specific frontend URL for security
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

# Predefined skill set
SKILLS_LIST = {"Python", "JavaScript", "Machine Learning", "AI", "Data Science", "React", "Django", "FastAPI"}

# Function to extract text from PDF
def extract_text_from_pdf(file_path):
    with pdfplumber.open(file_path) as pdf:
        return "\n".join([page.extract_text() for page in pdf.pages if page.extract_text()])

# Function to extract text from DOCX
def extract_text_from_docx(file_path):
    doc = docx.Document(file_path)
    return "\n".join([para.text for para in doc.paragraphs])

# Function to extract contact info (email, phone)
def extract_contact_info(text):
    email_match = re.search(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", text)
    phone_match = re.search(r"\+?\d{10,13}", text)

    email = email_match.group() if email_match else "Not found"
    phone = phone_match.group() if phone_match else "Not found"

    return {"email": email, "phone": phone}

# Function to extract skills
def extract_skills(text):
    found_skills = [skill for skill in SKILLS_LIST if skill.lower() in text.lower()]
    return found_skills
@app.post("/predict")
async def predict(data: dict):
    return {"prediction": "Your prediction result here"}


# Resume Analyzer API
@app.post("/analyze-resume")
async def analyze_resume(file: UploadFile = File(...)):
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Extract text based on file type
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
    elif file.filename.endswith(".docx"):
        text = extract_text_from_docx(file_path)
    else:
        os.remove(file_path)
        raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

    os.remove(file_path)  # Cleanup

    # Extract details
    contact_info = extract_contact_info(text)
    skills = extract_skills(text)

    # Generate feedback
    feedback = []
    if "Not found" in contact_info["email"]:
        feedback.append("Consider adding an email.")
    if "Not found" in contact_info["phone"]:
        feedback.append("Include a phone number.")
    if len(skills) < 3:
        feedback.append("Consider adding more technical skills.")

    return JSONResponse(content={
        "email": contact_info["email"],
        "phone": contact_info["phone"],
        "skills": skills,
        "feedback": feedback
    })

# Root endpoint

@app.post("/predict")
async def predict(data: dict):
    return {"prediction": "Your prediction result here"}

@app.get("/")
async def root():
    return {"message": "Welcome to the AI Resume Analyzer API!"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}


