import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

# --- 1. INITIAL SETUP ---
load_dotenv()
st.set_page_config(page_title="StudySphere Pro", page_icon="🏆", layout="wide")

MEMORY_FILE = "student_memory.json"

# Robust Memory Loader: Prevents crashes by merging old data with new templates
def load_memory():
    defaults = {
        "user_name": "Student", 
        "exam_profile": {"date": str(datetime.now().date()), "marks": 100, "pattern": "Mixed", "duration": 180},
        "syllabus": "", 
        "past_paper_analysis": "", 
        "progress": []
    }
    
    if os.path.exists(MEMORY_FILE):
        try:
            with open(MEMORY_FILE, "r") as f:
                stored_data = json.load(f)
                # Merge top-level keys
                for key, value in defaults.items():
                    if key not in stored_data:
                        stored_data[key] = value
                # Merge exam_profile sub-keys
                for subkey, subval in defaults['exam_profile'].items():
                    if subkey not in stored_data['exam_profile']:
                        stored_data['exam_profile'][subkey] = subval
                return stored_data
        except:
            return defaults
    return defaults

def save_memory(data):
    with open(MEMORY_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Initialize Session State
if 'memory' not in st.session_state:
    st.session_state.memory = load_memory()

# API Key handling
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
if not api_key:
    st.error("⚠️ GROQ_API_KEY not found in Secrets!")
    st.stop()

client = Groq(api_key=api_key)

def extract_text(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text() or ""
    return text

# --- 2. SIDEBAR COMMAND CENTER ---
with st.sidebar:
    st.title("🏆 Exam Command Center")
    st.session_state.memory['user_name'] = st.text_input("Student Name", st.session_state.memory['user_name'])
    
    st.subheader("📊 Exam Profile")
    saved_date = st.session_state.memory['exam_profile'].get('date', str(datetime.now().date()))
    e_date = st.date_input("Exam Date", value=datetime.strptime(saved_date, "%Y-%m-%d"))
    e_marks = st.number_input("Total Marks", value=st.session_state.memory['exam_profile'].get('marks', 100))
    e_duration = st.number_input("Exam Duration (Mins)", value=st.session_state.memory['exam_profile'].get('duration', 180))
    e_pattern = st.selectbox("Exam Pattern", ["Subjective", "MCQ Only", "Mixed Case Study", "Numerical Focused"])
    
    days_left = (e_date - datetime.now().date()).days
    st.metric("Countdown", f"{max(0, days_left)} Days Left")
    
    if st.button("💾 Save Profile & Progress"):
        st.session_state.memory['exam_profile'] = {"date": str(e_date), "marks": e_marks, "pattern": e_pattern, "duration": e_duration}
        save_memory(st.session_state.memory)
        st.success("Memory Updated!")

    st.markdown("---")
    menu = st.radio("Navigation", ["🤖 Personal Agent", "📁 Study Materials", "🧠 Smart Quiz", "📝 Exam Simulation"])

# --- 3. FEATURE LOGIC ---

# FEATURE: DATA HUB
if menu == "📁 Study Materials":
    st.header("📁 Material Analysis Hub")
    tab1, tab2 = st.tabs(["Syllabus", "Past Paper Analysis"])
    
    with tab1:
        st.write("Upload your syllabus to teach the Agent your course structure.")
        syl_file = st.file_uploader("Upload Syllabus (PDF)", type=['pdf'], key="syl")
        if st.button("Train on Syllabus"):
            if syl_file:
                st.session_state.memory['syllabus'] = extract_text(syl_file)
                save_memory(st.session_state.memory)
                st.success("Agent is now syllabus-aware.")

    with tab2:
        st.write("Identify high-yield topics from past papers.")
        past_files = st.file_uploader("Upload Past Papers (PDFs)", type=['pdf'], accept_multiple_files=True, key="past")
        if st.button("Run Pattern Analysis"):
            if past_files:
                combined_text = "".join([extract_text(f) for f in past_files])
                prompt = f"Analyze these past exams: {combined_text[:10000]}. List the top 5 most frequent topics and how many marks they usually carry."
                with st.spinner("Finding patterns..."):
                    res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                    st.session_state.memory['past_paper_analysis'] = res.choices[0].message.content
                    save_memory(st.session_state.memory)
                    st.markdown(st.session_state.memory['past_paper_analysis'])

# FEATURE: SMART QUIZ
elif menu == "🧠 Smart Quiz":
    st.header("🧠 Diagnostic Smart Quiz")
    if not st.session_state.memory['syllabus']:
        st.warning("Upload a syllabus first!")
    else:
        if st.button("Generate Targeted Quiz"):
            prompt = f"Context: {st.session_state.memory['past_paper_analysis']}. Syllabus: {st.session_state.memory['syllabus'][:2000]}. Generate 5 challenging questions based on high-yield topics."
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.session_state.current_quiz = res.choices[0].message.content
            st.rerun()
            
        if 'current_quiz' in st.session_state:
            st.markdown(st.session_state.current_quiz)
            with st.form("quiz_form"):
                ans = st.text_area("Your Answers:")
                if st.form_submit_button("Submit for Grading"):
                    eval_p = f"Grade these answers: {ans} against this quiz: {st.session_state.current_quiz}. Be strict."
                    grade = client.chat.completions.create(messages=[{"role": "user", "content": eval_p}], model="llama-3.3-70b-versatile")
                    st.markdown(grade.choices[0].message.content)

# FEATURE: EXAM SIMULATION
elif menu == "📝 Exam Simulation":
    st.header("📝 Full-Length Exam Simulation")
    
    if 'exam_active' not in st.session_state: st.session_state.exam_active = False
    
    col1, col2 = st.columns([2,1])
    with col1:
        if st.button("Generate Original Sample Paper"):
            prompt = f"Create a full {st.session_state.memory['exam_profile']['marks']} mark exam paper for {st.session_state.memory['exam_profile']['pattern']} style using: {st.session_state.memory['syllabus'][:2000]}"
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.session_state.exam_paper = res.choices[0].message.content
            st.session_state.exam_active = False

        if 'exam_paper' in st.session_state:
            st.markdown(st.session_state.exam_paper)

    with col2:
        if 'exam_paper' in st.session_state:
            if not st.session_state.exam_active:
                if st.button("START TIMER 🚀"):
                    st.session_state.exam_active = True
                    st.session_state.start_time = time.time()
                    st.rerun()
            else:
                elapsed = time.time() - st.session_state.start_time
                rem = (st.session_state.memory['exam_profile']['duration'] * 60) - elapsed
                if rem > 0:
                    st.metric("Time Remaining", f"{int(rem//60)}m {int(rem%60)}s")
                    if st.button("Finish Exam"):
                        st.session_state.exam_active = False
                        st.success("Paper submitted! Paste answers below to grade.")
                else:
                    st.error("TIME UP!")
                    st.session_state.exam_active = False

# FEATURE: PERSONAL AGENT
elif menu == "🤖 Personal Agent":
    st.header(f"👋 Welcome, {st.session_state.memory['user_name']}")
    st.write(f"The exam is on {saved_date}. What are we focusing on today?")
    
    chat = st.chat_input("Ask the agent...")
    if chat:
        context = f"Syllabus: {st.session_state.memory['syllabus'][:500]}. Profile: {st.session_state.memory['exam_profile']}"
        res = client.chat.completions.create(
            messages=[{"role": "system", "content": f"You are a study coach. Context: {context}"}, {"role": "user", "content": chat}],
            model="llama-3.3-70b-versatile"
        )
        st.chat_message("assistant").write(res.choices[0].message.content)
