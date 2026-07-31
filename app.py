import streamlit as st
import pandas as pd
import os
import json
import time
import subprocess
import sys
from datetime import datetime
from groq import Groq
from pypdf import PdfReader

# --- 1. INITIAL SETUP & MEMORY ---
st.set_page_config(page_title="StudySphere Master AI", page_icon="🎓", layout="wide")

# Function to manage long-term memory
MEMORY_FILE = "student_memory.json"

def load_memory():
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                return json.load(f)
        except: pass
    return {"user_name": "Student", "syllabus": "", "progress": [], "notes": ""}

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Extract PDF Text
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    return "".join([page.extract_text() for page in reader.pages])

# Initialize Session
if 'memory' not in st.session_state:
    st.session_state.memory = load_memory()

load_dotenv()
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# --- 2. SIDEBAR NAVIGATION ---
with st.sidebar:
    st.title("🎓 StudySphere Master")
    
    # Global User Settings
    st.session_state.memory['user_name'] = st.text_input("Student Name", st.session_state.memory['user_name'])
    
    st.markdown("---")
    # THE MASTER MENU
    menu = st.radio("Navigation", [
        "🤖 Personal AI Agent", 
        "📅 Study Planner", 
        "📝 Note Summarizer", 
        "🧠 Quiz Generator", 
        "✍️ Essay Polisher", 
        "⏳ Focus Timer"
    ])
    
    if st.button("Clear All Memory", type="primary"):
        st.session_state.memory = {"user_name": "Student", "syllabus": "", "progress": [], "notes": ""}
        save_memory(st.session_state.memory)
        st.rerun()

# --- 3. FEATURE LOGIC ---

# FEATURE: PERSONAL AGENT (The Brain)
if menu == "🤖 Personal AI Agent":
    st.header(f"🤖 Hey {st.session_state.memory['user_name']}, I'm your Study Agent.")
    
    col1, col2 = st.columns([2,1])
    with col1:
        st.write("I remember your syllabus and your progress. What's on your mind?")
        chat_input = st.chat_input("Ask me anything about your studies...")
        
        if chat_input:
            system_msg = f"User: {st.session_state.memory['user_name']}. Syllabus: {st.session_state.memory['syllabus'][:1000]}. History: {st.session_state.memory['progress'][-3:]}"
            res = client.chat.completions.create(
                messages=[{"role": "system", "content": system_msg}, {"role": "user", "content": chat_input}],
                model="llama-3.3-70b-versatile"
            )
            st.chat_message("assistant").write(res.choices[0].message.content)
            st.session_state.memory['progress'].append(f"{datetime.now().strftime('%m/%d')}: {chat_input}")
            save_memory(st.session_state.memory)

    with col2:
        st.subheader("📁 Training")
        up_syl = st.file_uploader("Upload Syllabus (PDF)", type=['pdf'])
        if st.button("Teach Agent Syllabus"):
            if up_syl:
                st.session_state.memory['syllabus'] = extract_text_from_pdf(up_syl)
                save_memory(st.session_state.memory)
                st.success("Syllabus Saved!")

# FEATURE: PLANNER
elif menu == "📅 Study Planner":
    st.header("📅 AI Study Planner")
    subject = st.text_input("What subject?")
    exam_date = st.date_input("Exam Date")
    if st.button("Create Plan"):
        prompt = f"Create a study plan for {subject} until {exam_date}. Context: {st.session_state.memory['syllabus'][:500]}"
        res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
        st.markdown(res.choices[0].message.content)

# FEATURE: SUMMARIZER
elif menu == "📝 Note Summarizer":
    st.header("📝 AI Summarizer")
    up_file = st.file_uploader("Upload PDF to Summarize", type=['pdf'])
    if st.button("Summarize"):
        if up_file:
            text = extract_text_from_pdf(up_file)
            res = client.chat.completions.create(messages=[{"role": "user", "content": f"Summarize: {text[:8000]}"}], model="llama-3.3-70b-versatile")
            st.markdown(res.choices[0].message.content)

# FEATURE: QUIZ
elif menu == "🧠 Quiz Generator":
    st.header("🧠 Quiz Generator")
    up_file = st.file_uploader("Upload PDF for Quiz", type=['pdf'])
    if st.button("Generate Quiz"):
        if up_file:
            text = extract_text_from_pdf(up_file)
            res = client.chat.completions.create(messages=[{"role": "user", "content": f"Quiz me on: {text[:8000]}"}], model="llama-3.3-70b-versatile")
            st.markdown(res.choices[0].message.content)

# FEATURE: ESSAY
elif menu == "✍️ Essay Polisher":
    st.header("✍️ Essay Polisher")
    draft = st.text_area("Paste draft:")
    if st.button("Polish"):
        res = client.chat.completions.create(messages=[{"role": "user", "content": f"Improve this: {draft}"}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)

# FEATURE: TIMER
elif menu == "⏳ Focus Timer":
    st.header("⏳ Focus Timer")
    mins = st.number_input("Minutes", 25)
    if st.button("Start"):
        ph = st.empty()
        for i in range(mins * 60, 0, -1):
            m, s = divmod(i, 60)
            ph.metric("Remaining", f"{m:02d}:{s:02d}")
            time.sleep(1)
        st.balloons()
