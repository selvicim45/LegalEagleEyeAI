#***********************************************************************
#*                    Program: LeagalEagleEyeAI
#*        Programmer: Arulselvi Amirrthalingam(Selvi) 
#*                         Date: 2025-04-25
#* Project Description:
#LegalEagelEye AI is a Agentic AI,
#*Which is designed to help user understand the documents,
#* and quickly review any risks or obligations in the document,
#*before signing it. For example, car rental agreements, social
#* media signing up terms ad conditions, contest rules,
#* any fine prints we usually ignore and sign.
#*This peoject also includes a HITL feature, where the user can
#*review the Risk extracted from the documwnt and ask the AI to regenerate
# the analysis.This project also includes a speech synthesis feature, where the
#*AI can read the doucument out loud to the user(accessibility). And also
#*translate the document to the user's preferred language.
#*A chatnot feature is also included where the user can ask
#*the AI any questions about the document for additional clarification.
#*This project is designed to be a web application where the user
#*can upload the document either in PDF,Image or text format.
#*The AI will then analyze the document and provide a summary of risks
#*and obligations in the document before signing it.
#*A user friendly attractive UI is also desinged for this project using
#*ReactJS,Axios, HTML,CSS  and Javascript.
#*LegalEagleEyeAI is a user friendly Agentic AI that everyone can use
#*on our daily life. It is designed to be a personal assistant.
#************************************************************************
#---------------------------------
#Import Libraries
#---------------------------------
import logging
from flask import Flask, jsonify, request, send_file
import re
import requests
import os
import openai
from flask_cors import CORS
from dotenv import load_dotenv
from io import BytesIO
import fitz
import html
from pdfminer.high_level import extract_text
import uuid

#---------------------------
#Load environment variables
#---------------------------
load_dotenv()

#---------------------------
#Setup environment variables
#---------------------------
AZURE_CV_ENDPOINT = os.getenv("AZURE_CV_ENDPOINT", "") #Azure Computer Vision endpoint
AZURE_CV_KEY = os.getenv("AZURE_CV_KEY", "")#Azure Computer Visionkey
AZURE_OPENAI_KEY = os.getenv("AZURE_OPENAI_KEY", "")# Azure OpenAI key
AZURE_OPENAI_ENDPOINT = os.getenv("AZURE_OPENAI_ENDPOINT", "")# Azure OpenAI endpoint
AZURE_OPENAI_DEPLOYMENT = os.getenv("AZURE_OPENAI_DEPLOYMENT", "")# Azure OpenAI deployment name
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")# openAI API key
SPEECH_KEY = os.getenv("SPEECH_KEY")# Azure Speech AI Service key
SPEECH_REGION = os.getenv("SPEECH_REGION")# Azure Speech AI Service Region
AZURE_TRANSLATOR_KEY = os.getenv("AZURE_TRANSLATOR_KEY")# Azure Translator API Key
AZURE_TRANSLATOR_ENDPOINT = os.getenv("AZURE_TRANSLATOR_ENDPOINT")#Azure Translatoe API endpoint
AZURE_TRANSLATOR_REGION = os.getenv("AZURE_TRANSLATOR_REGION")#Azure Translator API Region

# --------------------------------
# Initialize Flask app and logging
# ---------------------------------
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}}, supports_credentials=True)
logging.basicConfig(level=logging.DEBUG,
    format='%(asctime)s %(levelname)s %(name)s : %(message)s')

# ------------------------------
# Agent Registry & Team State
# ------------------------------
AGENTS = {}
TEAMS = {}

#---------------------
#Agent Classes
#---------------------
class Agent:
    def __init__(self, name, role, manager_id=None):
        self.id = str(uuid.uuid4()) #Unique ID for each agent
        self.name = name
        self.role = role
        self.manager_id = manager_id
        self.status = "idle" #status of the agent idle/busy
        self.memory = [] #Memory of completed agents tasks
        AGENTS[self.id] = self#Register agent in AGENTS dictionary

    #Handle task assignment
    def assign_task(self, task, data=None):
        self.memory.append(f"Assigned: {task}")
        self.status = "busy"
        try:
            if self.role == "ocr":
                result = ocr_agent_task(data)
            elif self.role == "pdf":
                result = pdf_agent_task(data)
            elif self.role == "risk_analysis":
                result = risk_agent_task(data)
            elif self.role == "translation":
                result = translation_agent_task(data)
            elif self.role == "speech":
                result = speech_agent_task(data)
            else:
                result = f"{self.role} {self.name} completed: {task}"
        except Exception as e:
            app.logger.error(f"Agent {self.name} failed task {task}: {e}", exc_info=True)
            result = f"Error: {e}"
        self.memory.append(f"Completed: {task}")
        self.status = "idle"
        return result
    
    #Return agent details as dictionary
    def to_dict(self):
        return {
            "id": self.id,
            "name": self.name,
            "role": self.role,
            "manager_id": self.manager_id,
            "status": self.status,
            "memory": self.memory,
        }

class ManagerAgent(Agent):
    #Manager Agent who can delegate tasks to other agents
    #and manage the team
    def __init__(self, name, role="manager", manager_id=None):
        super().__init__(name, role, manager_id)
        self.team = []

    def add_team_member(self, agent):
        #Add agent under manager's team
        self.team.append(agent.id)
        agent.manager_id = self.id

    def delegate_task(self, task, data=None):
        #Delegate task to the appropriate agent in the team
        eligible_agents = [AGENTS[agent_id] for agent_id in self.team 
                          if AGENTS[agent_id].role == task]
        
        for agent in eligible_agents:
            if agent.status == "idle":
                try:
                    result = agent.assign_task(task, data)
                    self.memory.append(f"Delegated '{task}' to {agent.name}")
                    return result
                except Exception as e:
                    app.logger.error(f"Manager {self.name} failed to delegate {task}: {e}", exc_info=True)
                    return f"Error: {e}"
        self.memory.append(f"No idle {task} agent available")
        return f"No idle {task} agent available"
    
    #Manager details including team members
    def to_dict(self):
        d = super().to_dict()
        d["team"] = self.team
        return d

#-----------------------------------
# Azure Service Agent Task Functions
#-----------------------------------
#OCR Agent Task (reads text from image using Azure CV)
def ocr_agent_task(image_data):
    if not AZURE_CV_ENDPOINT or not AZURE_CV_KEY:
        app.logger.error("OCR service not configured (missing endpoint/key)")
        return "OCR service not configured."
    ocr_url = AZURE_CV_ENDPOINT.rstrip('/') + "/vision/v3.2/ocr"
    headers = {"Ocp-Apim-Subscription-Key": AZURE_CV_KEY, "Content-Type": "application/octet-stream"}
    try:
        response = requests.post(ocr_url, headers=headers, data=image_data)
        response.raise_for_status()
        analysis = response.json()
        
        #Assemble text from OCR response line by line
        extracted_text = ""
        for region in analysis.get("regions", []):
            for line in region.get("lines", []):
                line_text = " ".join(word["text"] for word in line.get("words", []))
                extracted_text += line_text + "\n"
        return extracted_text.strip()
    except Exception as e:
        app.logger.error(f"Error extracting text from image: {e}", exc_info=True)
        return f"Error extracting text from image: {e}"
    
#PDF Agent Task-reads text from PDF using pdfminer and PyMuPDF
def pdf_agent_task(file):
    try:
        if isinstance(file, dict):
            raise ValueError("Invalid file format received") #Validation
            
        file_data = BytesIO(file.read())
        text = extract_text(file_data)
        file_data.seek(0)

        #if text is empty or too short use PyMuPDF(fallback)
        if not text or len(text.strip()) < 20:
            doc = fitz.open(stream=file_data, filetype="pdf")
            text = ""
            for page in doc:
                text += page.get_text("text")
        return text.strip()
    except Exception as e:
        app.logger.error(f"Error extracting text from PDF: {e}", exc_info=True)
        return f"Error extracting text from PDF: {e}"

#Translation Agent Task
def translation_agent_task(data):
    text, to_lang = data.get("text"), data.get("to_lang", "en")
    if not AZURE_TRANSLATOR_KEY or not AZURE_TRANSLATOR_ENDPOINT:
        app.logger.error("Translation service not configured (missing endpoint/key)")
        return text #Fallback to original text
    endpoint = f"https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to={to_lang}"
    headers = {
        'Ocp-Apim-Subscription-Key': AZURE_TRANSLATOR_KEY,
        'Ocp-Apim-Subscription-Region': AZURE_TRANSLATOR_REGION,
        'Content-type': 'application/json'
    }
    body = [{"Text": text}]
    try:
        response = requests.post(endpoint, headers=headers, json=body)
        response.raise_for_status()
        return response.json()[0]["translations"][0]["text"]
    except Exception as e:
        app.logger.error(f"Translation failed: {e}", exc_info=True)
        return text

#Risk Agent Task
#Extracts risks from the document using LLM
def risk_agent_task(data):
    text = data.get("text")
    filename = data.get("filename")
    return extract_and_score_risks(text, filename)

#Speech Agent Task
def speech_agent_task(data):
    summary = html.escape(data.get("summary", ""))
    risk_factors = data.get("risk_factors", [])
    target_lang = data.get("target_lang", "en")

    #For English use different voices based on severity
    english_voice_map = {
        "High Risk": ("en-US-GuyNeural", "newscast"),
        "Moderate Risk": ("en-US-AriaNeural", "chat"),
        "Informational": ("en-US-JennyNeural", "cheerful")
    }
    #For other languages use a single voice
    lang_voice_map = {
        "es": "es-ES-AlvaroNeural",
        "fr": "fr-FR-DeniseNeural",
        "it": "it-IT-DiegoNeural",
        "de": "de-DE-ConradNeural",
        "pt": "pt-PT-DuarteNeural",
        "ta": "ta-IN-ValluvarNeural",
        "zh-Hans": "zh-CN-YunxiNeural"
    }
    #Helper function to wrap clauses in SSML speech format
    def wrap_clause(clause_text, severity, lang="en"):
        clause_text = html.escape(clause_text)
        if lang == "en":
            voice, style = english_voice_map.get(severity, english_voice_map["Informational"])
            return f"""
            <voice name="{voice}">
                <mstts:express-as style="{style}">
                    <prosody rate="medium" pitch="default">
                        {clause_text}
                    </prosody>
                </mstts:express-as>
            </voice>
            """
        else:
            voice = lang_voice_map.get(lang, "en-US-JennyNeural")
            return f"""
            <voice name="{voice}">
                <prosody rate="medium" pitch="default">
                    {clause_text}
                </prosody>
            </voice>
            """
        
    #prepare summary and risk factors for speech synthesis    
    if target_lang == "en":
        summary_voice = "en-US-JennyNeural"
        summary_style = "general"
    else:
        summary_voice = lang_voice_map.get(target_lang, "en-US-JennyNeural")
        summary_style = ""
    summary_block = f"""
    <voice name="{summary_voice}">
        <mstts:express-as style="{summary_style}">""" if summary_style else f"""<voice name="{summary_voice}">"""
    summary_block += f"""
            <prosody rate="medium" pitch="default">{summary}</prosody>
        </mstts:express-as></voice>""" if summary_style else "</voice>"
    speech_body = summary_block

    #Wrap each risk factor into the speech body
    if risk_factors:
        for item in risk_factors:
            clause_text = item.get("text", "")
            severity = item.get("severity", "Informational")
            speech_body += wrap_clause(clause_text, severity, lang=target_lang)
    else:
        speech_body += wrap_clause("No legal risks or obligations were found in this document.", "Informational", lang=target_lang)
    
    #Final SSML body
    ssml = f"""
    <speak version="1.0" xml:lang="en-US"
           xmlns:mstts="http://www.w3.org/2001/mstts"
           xmlns="http://www.w3.org/2001/10/synthesis">
        {speech_body}
    </speak>
    """

    #Send request to Azure Speech service API
    tts_url = f"https://{SPEECH_REGION}.tts.speech.microsoft.com/cognitiveservices/v1"
    headers = {
        "Ocp-Apim-Subscription-Key": SPEECH_KEY,
        "Content-Type": "application/ssml+xml",
        "X-Microsoft-OutputFormat": "audio-16khz-128kbitrate-mono-mp3",
    }
    try:
        response = requests.post(tts_url, headers=headers, data=ssml.encode("utf-8"))
        response.raise_for_status()
        return response.content
    except Exception as e:
        app.logger.error(f"Speech synthesis failed: {e}", exc_info=True)
        return None

# -------------------------------------------
# Risk Extraction  with Severity Tags (LLM)
#--------------------------------------------
def extract_and_score_risks(text, filename=None):
    prompt = (
        "You are a legal document assistant. Analyze the document below and extract ONLY the clauses that include penalties/penalty, "
        "fees, user obligations, personal data usage, disqualification, or legal consequences.\n"
        "Ignore general descriptions or unrelated content.\n"
        "Format your response as follows:\n"
        "Title: [Your Title Here]\n"
        "- [High Risk] Clause in plain English\n"
        "- [Moderate Risk] Another clause...\n"
        "- [Informational] Mild clauses, optional duties, or user advice\n\n"
        "If no risks are found, return:\n"
        "Title: No risks detected\n"
        "- [Informational] No legal risks or obligations were found in this document.\n\n"
        f"{text}"
    )
    def parse_gpt_response(response_text, original_text, filename=None):
        title = ""
        risks = []
        lines = response_text.splitlines()
        for line in lines:
            line = line.strip()
            if not line:
                continue
            if line.lower().startswith("title:"):
                potential_title = line.split(":", 1)[1].strip()
                if len(potential_title) > 3:
                    title = potential_title
            elif re.match(r"^-\s+\[(High Risk|Moderate Risk|Informational)\]\s+", line):
                match = re.match(r"^-\s+\[(.*?)\]\s+(.*)", line)
                if match:
                    severity = match.group(1).strip()
                    clause_text = match.group(2).strip()
                    if clause_text:
                        risks.append({"text": clause_text, "severity": severity})
        if not title:
            original_lines = original_text.splitlines()
            for orig_line in original_lines:
                orig_line = orig_line.strip()
                if 5 < len(orig_line) < 100:
                    title = orig_line
                    break
            if not title and filename:
                name = os.path.splitext(filename)[0]
                title = f"{name.capitalize()} Document Summary"

        #To sort the risks by severity        
        severity_order = { 
            "High Risk": 0,
            "Moderate Risk": 1,
            "Informational": 2
        }
        risks.sort(key=lambda r: severity_order.get(r["severity"], 3))
        return {
            "title": title,
            "risks": risks
        }
    
    max_text_length = 12000
    processed_text = text[:max_text_length] if len(text) > max_text_length else text
    
    if AZURE_OPENAI_KEY and AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_ENDPOINT:
        try:
            openai.api_type = "azure"
            openai.api_base = AZURE_OPENAI_ENDPOINT
            openai.api_key = AZURE_OPENAI_KEY
            openai.api_version = "2023-05-15"
            response = openai.ChatCompletion.create(
                engine=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": processed_text}
                ],
                temperature=0.4,
                max_tokens=800
            )
            output = response['choices'][0]['message']['content'].strip()
            return parse_gpt_response(output, text, filename)
        except Exception as e:
            app.logger.error(f"Azure GPT failed: {e}", exc_info=True)
    
    if OPENAI_API_KEY:
        try:
            openai.api_version = ""
            openai.api_type = "openai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_key = OPENAI_API_KEY
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo-16k",
                messages=[
                    {"role": "system", "content": prompt},
                    {"role": "user", "content": processed_text}
                ],
                temperature=0.4,
                max_tokens=800
            )
            output = response['choices'][0]['message']['content'].strip()
            return parse_gpt_response(output, text, filename)
        except Exception as e:
            app.logger.error(f"OpenAI fallback failed: {e}", exc_info=True)
            return {"title": "Risk Detection Failed", "risks": [{"text": str(e), "severity": "Error"}]}
    
    return {"title": "Risk Detection Failed", "risks": [{"text": "No valid API key available.", "severity": "Error"}]}


#------------------------------
#Document Processing Endpoints
#------------------------------
@app.route("/upload", methods=["POST", "OPTIONS"])
def upload_document():
    #Handles CORS preflight requests
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    try:
        #check if the file is uploaded
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        #Determine file type(PDF,IMAGE,TEXT)
        file_extension = file.filename.rsplit('.', 1)[-1].lower()
        
        #Find manager agent
        manager_agents = [a for a in AGENTS.values() if isinstance(a, ManagerAgent)]
        
        if not manager_agents:
            return jsonify({"error": "No manager agent available"}), 500
        manager = manager_agents[0]
        
        #Process the file based on its type
        if file_extension == 'pdf':
            file_data = BytesIO(file.read())
            file.seek(0)
            text = manager.delegate_task("pdf", file_data)
        elif file_extension in ['png', 'jpg', 'jpeg']:
            image_data = file.read()
            file.seek(0)
            text = manager.delegate_task("ocr", image_data)
        else:
            text = file.read().decode('utf-8')
            file.seek(0)
        
        #Analyze the text for risks 
        result = manager.delegate_task("risk_analysis", {"text": text, "filename": file.filename})
        
        if isinstance(result, str):
            return jsonify({"error": result}), 500
        
        #Filter out empty or irrvelavant risks
        result["risks"] = [
            r for r in result["risks"]
            if r["text"].strip().lower() != "no legal risks or obligations were found in this document."
        ]
        
        #Remove duplicate risks
        seen = set()
        result["risks"] = [
            r for r in result["risks"]
            if not (r["text"] in seen or seen.add(r["text"]))
        ]
        
        #If no risks found, add a default message
        #and set summary to "No risks detected"
        if not result["risks"]:
            result["summary"] = "No risks detected"
            result["risks"] = [{
                "text": "No legal risks or obligations were found in this document.",
                "severity": "Informational"
            }]
        else:
            result["summary"] = result["title"] if result["title"].strip().lower() != "no risks detected" else "Document Summary"

        #Return the final result as JSON including summary, risks and full text    
        return jsonify({
            "summary": result["summary"],
            "risk_factors": result["risks"],
            "full_text": text
        })
    except Exception as e:
        app.logger.error(f"CRITICAL ERROR IN /upload: {e}", exc_info=True)
        return jsonify({'error': 'Internal server error'}), 500

@app.route("/translate", methods=["POST", "OPTIONS"])
def translate_risks():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    try:
        data = request.json
        summary = data.get("summary", "")
        risk_factors = data.get("risk_factors", [])
        target_lang = data.get("target_lang", "en")

        #Find manager agent
        manager_agents = [a for a in AGENTS.values() if isinstance(a, ManagerAgent)]
        if not manager_agents:
            return jsonify({"error": "No manager agent available"}), 500
        manager = manager_agents[0]

        #Translates the summary and risk factors using Azure Translator
        translated_summary = manager.delegate_task("translation", {"text": summary, "to_lang": target_lang})
        translated_risks = []
        for rf in risk_factors:
            translated_text = manager.delegate_task("translation", {"text": rf["text"], "to_lang": target_lang})
            translated_risks.append({"text": translated_text, "severity": rf["severity"]})
        return jsonify({
            "summary": translated_summary,
            "risk_factors": translated_risks
        })
    except Exception as e:
        app.logger.error(f"Error in /translate: {e}", exc_info=True)
        return jsonify({"error": f"Translation failed: {e}"}), 500

@app.route("/speak", methods=["POST", "OPTIONS"])
def speak_text():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    try:
        data = request.json
        summary = html.escape(data.get("summary", ""))
        risk_factors = data.get("risk_factors", [])
        target_lang = data.get("target_lang", "en")

        #Find the manager agent
        manager_agents = [a for a in AGENTS.values() if isinstance(a, ManagerAgent)]
        if not manager_agents:
            return jsonify({"error": "No manager agent available"}), 500
        manager = manager_agents[0]

        #Generate speech
        audio_bytes = manager.delegate_task("speech", {"summary": summary, "risk_factors": risk_factors, "target_lang": target_lang})
        if not audio_bytes:
            return jsonify({"error": "Speech synthesis failed"}), 500
        #return the audio file as a response
        #Set the content type to audio/mpeg
        return send_file(BytesIO(audio_bytes), mimetype="audio/mpeg", as_attachment=False, download_name="speech.mp3")
    except Exception as e:
        app.logger.error(f"Error in /speak: {e}", exc_info=True)
        return jsonify({"error": f"Speech synthesis failed: {e}"}), 500

@app.route("/ask", methods=["POST"])
def ask_about_clause():
    data = request.json
    user_question = data.get("question")
    risk_factors = data.get("risk_factors", [])
    full_text = data.get("full_text", "")
    target_lang = data.get("target_lang", "en")

    # Build retrieval context
    context = ""
    if risk_factors:
        context += "Key Risk Clauses:\n"
        for r in risk_factors:
            context += f"- [{r['severity']}] {r['text']}\n"
    if full_text:
        context += "\n---\nFull Document Content:\n" + full_text

    rag_prompt = f"""
You are a helpful legal assistant. Use the information below to answer the user’s legal question accurately and clearly.
If the answer is not found, respond honestly with "I'm not sure based on this document".

### Document Context:
{context}

### User Question:
{user_question}

### Answer:
"""

    answer = None

    # Try Azure first
    if AZURE_OPENAI_KEY and AZURE_OPENAI_DEPLOYMENT and AZURE_OPENAI_ENDPOINT:
        try:
            openai.api_type = "azure"
            openai.api_base = AZURE_OPENAI_ENDPOINT
            openai.api_key = AZURE_OPENAI_KEY
            openai.api_version = "2023-05-15"

            response = openai.ChatCompletion.create(
                engine=AZURE_OPENAI_DEPLOYMENT,
                messages=[
                    {"role": "system", "content": "You are a legal reasoning assistant."},
                    {"role": "user", "content": rag_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            answer = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print("⚠️ Azure GPT failed, switching to OpenAI:", e)

    # Fallback to OpenAI
    if answer is None:
        try:
            openai.api_version = ""
            openai.api_type = "openai"
            openai.api_base = "https://api.openai.com/v1"
            openai.api_key = OPENAI_API_KEY

            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a legal reasoning assistant."},
                    {"role": "user", "content": rag_prompt}
                ],
                temperature=0.3,
                max_tokens=500
            )
            answer = response['choices'][0]['message']['content'].strip()
        except Exception as e:
            print("❌ OpenAI fallback also failed:", e)
            return jsonify({"answer": "⚠️ Something went wrong."}), 500

    # Translate answer if needed
    if target_lang != "en" and answer:
        manager_agents = [a for a in AGENTS.values() if isinstance(a, ManagerAgent)]
        if manager_agents:
            manager = manager_agents[0]
            translated_answer = manager.delegate_task("translation", {"text": answer, "to_lang": target_lang})
            answer = translated_answer

    return jsonify({"answer": answer})  
         
#---------------------------------
# HITL feature (Human in the loop)
#---------------------------------
@app.route("/regenerate", methods=["POST", "OPTIONS"])
def regenerate_analysis():
    if request.method == "OPTIONS":
        return jsonify({"status": "ok"}), 200
    
    try:
        data = request.json
        text = data.get("full_text", "")
        filename = data.get("filename", "document.txt")
        
        # Get manager agent
        manager_agents = [a for a in AGENTS.values() if isinstance(a, ManagerAgent)]
        if not manager_agents:
            return jsonify({"error": "No manager agent available"}), 500
        manager = manager_agents[0]
        
        # Call risk analysis agent again
        result = manager.delegate_task("risk_analysis", {"text": text, "filename": filename})
        
        if isinstance(result, str):
            return jsonify({"error": result}), 500
        
        # Process results by removing empty or irrelevant risks
        result["risks"] = [
            r for r in result["risks"]
            if r["text"].strip().lower() != "no legal risks or obligations were found in this document."
        ]
        
        #Remove duplicate risks
        seen = set()
        result["risks"] = [
            r for r in result["risks"]
            if not (r["text"] in seen or seen.add(r["text"]))
        ]
        
        #Handle no risks found scenarios
        if not result["risks"]:
            result["summary"] = "No risks detected"
            result["risks"] = [{
                "text": "No legal risks or obligations were found in this document.",
                "severity": "Informational"
            }]
        else:
            result["summary"] = result["title"] if result["title"].strip().lower() != "no risks detected" else "Document Summary"
            
        return jsonify({
            "summary": result["summary"],
            "risk_factors": result["risks"],
            "full_text": text  # Return the full text to maintain state
        })
    except Exception as e:
        app.logger.error(f"Error in /regenerate: {e}", exc_info=True)
        return jsonify({"error": f"Regeneration failed: {e}"}), 500

#-------------------------
#Global Error Handler
#-------------------------
@app.errorhandler(Exception)
def handle_exception(e):
    app.logger.error("UNHANDLED EXCEPTION", exc_info=True)
    return jsonify(error=str(e)), 500

#--------------------------
#Initialize Default Agents
#--------------------------
def initialize_default_agents():
    manager = ManagerAgent("MainManager", "manager")
    agents = [
        Agent("PDFParser", "pdf", manager.id),
        Agent("OCRScanner", "ocr", manager.id),
        Agent("RiskAnalyzer", "risk_analysis", manager.id),
        Agent("Translator", "translation", manager.id),
        Agent("SpeechSynthesizer", "speech", manager.id)
    ]
    for agent in agents:
        manager.add_team_member(agent)
    return manager

if __name__ == "__main__":
    initialize_default_agents()
    app.run(debug=True, port=5001)
