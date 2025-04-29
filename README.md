# LegalEagleEyeAI 🦅

LegalEagleEyeAI is an agentic AI web application designed to help users understand legal documents and quickly review any risks or obligations before signing. Whether it's a car rental agreement, social media terms, contest rules, or any fine print, LegalEagleEyeAI empowers everyone to make informed decisions with accessible, AI-powered document analysis.

---

## Features

- **Document Upload & Analysis**  
  Upload PDF, image, or text files. The AI analyzes the document and extracts key clauses, risks, and obligations using advanced LLMs.

- **Risk Detection with Severity**  
  The system highlights and categorizes risk clauses as High Risk, Moderate Risk, or Informational, making it easy to spot critical issues.

- **Human-in-the-Loop Review**  
  Users can review the extracted risks, accept the AI’s analysis, or regenerate a new analysis for more confidence.

- **Text-to-Speech (TTS) Accessibility**  
  The AI can read the summary and risks out loud, using different voices for each severity level. Supports multiple languages for accessibility.

- **Translation**  
  Instantly translate the summary and risk factors into several languages, including Spanish, French, Italian, German, Portuguese, Tamil, and Chinese (Simplified).

- **Interactive Q&A Chatbot**  
  Ask questions about any clause or the full document context. The AI provides clear, context-aware answers.

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Demo / Video Presentation](#demo--video-presentation)
- [Software Stack](#software-stack)
- [Environment Variables](#environment-variables)
- [Setup & Local Development](#setup--local-development)
- [Usage Guide](#usage-guide)
- [What's Next?](#whats-next)
- [Attribution](#attribution)
- [Contact](#contact)

---

## Architecture

> _![image](https://github.com/user-attachments/assets/ab46f92d-96e5-4a78-ba1f-cc892a6fafe8)
._
>
> 
>
> _Describe the flow:_  
> - **Frontend (React)**: Handles file upload, UI, and user interactions.  
> - **Backend (Flask)**: Manages agent orchestration, document processing, risk extraction, translation, and TTS.  
> - **Azure Services**: OpenAI for LLM, Computer Vision for OCR, Translator, and Speech for TTS.

---

## Demo / Video Presentation

> https://www.youtube.com/watch?v=8bJk5qFFXPI

---

## Software Stack

- **Frontend:** React, JavaScript, SCSS, Axios
- **Backend:** Python, Flask, Flask-CORS
- **AI & Cloud:** Azure OpenAI Service, Azure Computer Vision, Azure Translator, Azure Speech
- **PDF/Image Processing:** PyMuPDF, pdfminer, requests
- **Environment Management:** python-dotenv

---

## Environment Variables

Before running the project, you must set up several environment variables for Azure and OpenAI services.

Create a `.env` file in the `server/` directory with the following keys:

---
Azure Computer Vision (OCR)
AZURE_CV_ENDPOINT=<your_azure_cv_endpoint>
AZURE_CV_KEY=<your_azure_cv_key>

Azure OpenAI
AZURE_OPENAI_KEY=<your_azure_openai_key>
AZURE_OPENAI_ENDPOINT=<your_azure_openai_endpoint>
AZURE_OPENAI_DEPLOYMENT=<your_azure_openai_deployment_name>

OpenAI Fallback (optional)
OPENAI_API_KEY=<your_openai_api_key>

Azure Speech (Text-to-Speech)
SPEECH_KEY=<your_azure_speech_key>
SPEECH_REGION=<your_azure_speech_region>

Azure Translator
AZURE_TRANSLATOR_KEY=<your_azure_translator_key>
AZURE_TRANSLATOR_ENDPOINT=<your_azure_translator_endpoint>
AZURE_TRANSLATOR_REGION=<your_azure_translator_region>

---

## Setup & Local Development

**Prerequisites:**
- Node.js >= v22.14
- Python >= 3.12
- Azure resources (OpenAI, Computer Vision, Translator, Speech)

**1. Clone the repository**

git clone (https://github.com/selvicim45/LegalEagleEyeAI)
cd LegalEagleEyeAI

**2. Install and Run the Frontend**

cd client
npm install
npm start
- The frontend will run on `http://localhost:3000` by default.

**3. Install and Run the Backend**

cd ../server
python3 -m venv venv
source venv/bin/activate # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python legal_eagleeye_ai.py
- The backend runs on `http://localhost:5001`.

**4. Environment Variables**

- Copy the `.env.example` to `.env` in the `server/` directory and fill in your Azure/OpenAI credentials.

**5. (Optional) PDF/Image Processing**

- For best results, ensure your Azure Computer Vision and Translator services are correctly set up for OCR and translation features.

---

## Usage Guide

1. **Upload a Document:**  
   - Click "Choose File" and select a PDF, image, or text file containing legal content.

2. **Analyze:**  
   - Click "Upload & Analyze". The AI will extract and summarize key risks and obligations.

3. **Review Risks:**  
   - Review the summary and risk factors. Accept or regenerate the analysis as needed.

4. **Accessibility Tools:**  
   - Use "Read Aloud" to hear the summary and risks, or translate them into your preferred language.

5. **Ask Questions:**  
   - Use the chatbot to ask about any clause or the full document.

---

## What's Next?

- **User Authentication & Profiles:**  
  Support for user accounts and saving analysis history.

- **Document History & Export:**  
  Save and export analysis reports as PDF or CSV.

- **Customizable Risk Detection:**  
  Allow users to define custom risk categories or focus areas.

- **Multi-Agent Collaboration:**  
  Enable legal teams to collaborate on document review.

---

## Attribution

- **Icons:**  
  - Lucide, Flaticon, Freepik

- **Images:**  
  - Freepik, Unsplash

- **Libraries:**  
  - React, Flask, PyMuPDF, pdfminer, OpenAI, Azure SDKs

---

## Contact

Have questions, feedback, or want to contribute?  
Contact the development team:

- Arulselvi Amirrthalingam (Selvi)
-https://www.linkedin.com/in/arulselvi-amirrthalingam-8450b0193/-


---

> _LegalEagleEyeAI is designed as a personal legal assistant for everyone. Always consult a qualified professional for critical legal decisions._
