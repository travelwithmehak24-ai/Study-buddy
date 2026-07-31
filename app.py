import streamlit as st
import pandas as pd
import os
import json
from datetime import datetime
from groq import Groq
from pypdf import PdfReader

# --- 1. CONFIG & MEMORY ENGINE ---
st.set_page_config(page_title="StudySphere Agent", page_icon="🤖", layout="wide")
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Function to load/save student memory
MEMORY_FILE = "student_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        with open(MEMORY_FILE, "r") as f:
            return json.load(f)
    return {"user_name": "Student", "syllabus": "", "progress": [], "goals": []}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "".join([page.extract_text() for page in reader.pages])

# Initialize Memory
if 'memory' not in st.session_state:
    st.session_state.memory = load_memory()

# --- 2. SIDEBAR AGENT SETTINGS ---
with st.sidebar:
    st.title("🤖 Study Agent")
    user_name = st.text_input("What's your name?", value=st.session_state.memory['user_name'])
    if user_name != st.session_state.memory['user_name']:
        st.session_state.memory['user_name'] = user_name
        save_memory(st.session_state.memory)
    
    st.markdown("---")
    menu = st.radio("Agent Tasks", ["Daily Check-in", "Upload Syllabus", "Progress Report"])
    
    if st.button("Reset Agent Memory", type="primary"):
        st.session_state.memory = {"user_name": user_name, "syllabus": "", "progress": [], "goals": []}
        save_memory(st.session_state.memory)
        st.rerun()

# --- 3. MAIN AGENT LOGIC ---

# TASK A: UPLOAD SYLLABUS (The Agent's Knowledge)
if menu == "Upload Syllabus":
    st.header("📚 Teach the Agent your Syllabus")
    st.write("Upload your course PDF so the agent knows exactly what you need to learn.")
    
    uploaded_syllabus = st.file_uploader("Upload Syllabus (PDF)", type=['pdf'])
    if st.button("Train Agent"):
        if uploaded_syllabus:
            text = extract_text_from_pdf(uploaded_syllabus)
            st.session_state.memory['syllabus'] = text[:10000] # Save first 10k chars
            save_memory(st.session_state.memory)
            st.success("Agent has learned your syllabus!")
        else:
            st.error("Please upload a PDF.")

# TASK B: DAILY CHECK-IN (The Agent's Interaction)
elif menu == "Daily Check-in":
    st.header(f"👋 Welcome back, {st.session_state.memory['user_name']}!")
    
    # The Agent's current "State"
    last_update = st.session_state.memory['progress'][-1] if st.session_state.memory['progress'] else "No progress yet."
    st.info(f"📍 Last Update: {last_update}")

    chat_input = st.chat_input("Tell the agent what you studied today or ask for a task...")
    
    if chat_input:
        # Construct the Agent's prompt with Memory
        system_prompt = f"""
        You are a Student Success Agent. 
        User Name: {st.session_state.memory['user_name']}
        Current Syllabus: {st.session_state.memory['syllabus'][:2000]}
        Previous Progress: {st.session_state.memory['progress']}
        
        Task: 1. Acknowledge the user's progress. 2. If they finished a task, update their status. 
        3. Suggest the next logical step from the syllabus. 4. Be encouraging.
        """
        
        with st.chat_message("assistant"):
            res = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": chat_input}
                ],
                model="llama-3.3-70b-versatile"
            )
            response = res.choices[0].message.content
            st.write(response)
            
            # Save this to memory automatically
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
            st.session_state.memory['progress'].append(f"{timestamp}: {chat_input}")
            save_memory(st.session_state.memory)

# TASK C: PROGRESS REPORT
elif menu == "Progress Report":
    st.header("📊 Your Study Journey")
    if not st.session_state.memory['progress']:
        st.write("No progress recorded yet. Start a Daily Check-in!")
    else:
        df = pd.DataFrame(st.session_state.memory['progress'], columns=["Activity History"])
        st.table(df)
        
        # AI Analysis of progress
        if st.button("Analyze my consistency"):
            prompt = f"Analyze this study history and give a grade on consistency and focus: {st.session_state.memory['progress']}"
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.write(res.choices[0].message.content)
