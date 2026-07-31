import streamlit as st
import pandas as pd
import os
import json
import time
from datetime import datetime
from groq import Groq
from pypdf import PdfReader
from dotenv import load_dotenv

load_dotenv()
st.set_page_config(page_title="StudySphere Pro", page_icon="🏆", layout="wide")

# --- 1. PERSISTENT MEMORY ---
MEMORY_FILE = "student_memory.json"

def load_memory():
    # Define the "Perfect" default structure
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
                # This line MERGES the old file with the new defaults
                # If a key (like 'date') is missing, it adds it automatically
                for key, value in defaults.items():
                    if key not in stored_data:
                        stored_data[key] = value
                    if key == 'exam_profile': # Special check for the sub-dictionary
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

if 'memory' not in st.session_state:
    st.session_state.memory = load_memory()

client = Groq(api_key=st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY"))

def extract_text(file):
    return "".join([page.extract_text() for page in PdfReader(file).pages])

# --- 2. SIDEBAR COMMAND CENTER ---
with st.sidebar:
    st.title("🏆 Exam Command Center")
    st.session_state.memory['user_name'] = st.text_input("Student Name", st.session_state.memory['user_name'])
    
    st.subheader("📊 Exam Profile")
    e_date = st.date_input("Exam Date", value=datetime.strptime(st.session_state.memory['exam_profile']['date'], "%Y-%m-%d"))
    e_marks = st.number_input("Total Marks", value=st.session_state.memory['exam_profile']['marks'])
    e_duration = st.number_input("Exam Duration (Mins)", value=st.session_state.memory['exam_profile'].get('duration', 180))
    e_pattern = st.selectbox("Exam Pattern", ["Subjective", "MCQ Only", "Mixed Case Study", "Numerical Focused"])
    
    if st.button("Save Profile"):
        st.session_state.memory['exam_profile'] = {"date": str(e_date), "marks": e_marks, "pattern": e_pattern, "duration": e_duration}
        save_memory(st.session_state.memory)
        st.success("Profile Updated!")

    menu = st.radio("Tools", ["🤖 Personal Agent", "📁 Study Materials", "🧠 Smart Quiz", "📝 Exam Simulation"])

# --- 3. EXAM SIMULATION LOGIC ---

if menu == "📝 Exam Simulation":
    st.header("📝 Full-Length Exam Simulation")
    
    if not st.session_state.memory['syllabus'] or not st.session_state.memory['past_paper_analysis']:
        st.warning("⚠️ You must upload your Syllabus and analyze Past Papers first to generate a realistic exam!")
        st.stop()

    # Session State for Exam
    if 'exam_active' not in st.session_state: st.session_state.exam_active = False
    if 'exam_paper' not in st.session_state: st.session_state.exam_paper = ""

    col1, col2 = st.columns([2,1])
    
    with col1:
        if st.button("Generate Original Sample Paper 📄"):
            with st.spinner("Agent is designing your exam..."):
                prompt = f"""
                Act as a Chief Examiner. Generate a full-length sample paper based on:
                Syllabus: {st.session_state.memory['syllabus'][:3000]}
                High Yield Patterns: {st.session_state.memory['past_paper_analysis']}
                Total Marks: {st.session_state.memory['exam_profile']['marks']}
                Format: {st.session_state.memory['exam_profile']['pattern']}
                
                Structure the paper with Sections (Section A, B, C) and clear mark allocations per question.
                DO NOT provide answers.
                """
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.session_state.exam_paper = res.choices[0].message.content
                st.session_state.exam_active = False
        
        if st.session_state.exam_paper:
            st.markdown("---")
            st.markdown(st.session_state.exam_paper)

    with col2:
        if st.session_state.exam_paper:
            st.subheader("⏱️ Exam Timer")
            if not st.session_state.exam_active:
                if st.button("START TIMED SESSION 🚀"):
                    st.session_state.exam_active = True
                    st.session_state.start_time = time.time()
                    st.rerun()
            else:
                elapsed = time.time() - st.session_state.start_time
                remaining = (st.session_state.memory['exam_profile']['duration'] * 60) - elapsed
                
                if remaining > 0:
                    mins, secs = divmod(int(remaining), 60)
                    st.metric("Time Remaining", f"{mins:02d}:{secs:02d}")
                    if st.button("End & Submit Paper"):
                        st.session_state.exam_active = False
                        st.session_state.submitted_answers = "User completed the exam." # Placeholder for real input
                else:
                    st.error("⌛ TIME IS UP!")
                    st.session_state.exam_active = False

    # ANSWER SUBMISSION
    if st.session_state.exam_paper and not st.session_state.exam_active:
        st.markdown("---")
        st.subheader("🖋️ Submit Your Answers")
        user_submission = st.text_area("Paste your full answers here for grading:", height=400)
        
        if st.button("Get Professional Grade & Feedback"):
            with st.spinner("Chief Examiner is grading your paper..."):
                grade_prompt = f"""
                You are a strict examiner. Grade this student's work.
                Exam Paper: {st.session_state.exam_paper}
                Student Answers: {user_submission}
                Target Marks: {st.session_state.memory['exam_profile']['marks']}
                
                Provide:
                1. A mark for each section.
                2. Total Percentage.
                3. Critical Mistakes: Where did they lose marks?
                4. Improvement Strategy: What topics should they study to get an A+?
                """
                res = client.chat.completions.create(messages=[{"role": "user", "content": grade_prompt}], model="llama-3.3-70b-versatile")
                st.header("📊 Official Results")
                st.markdown(res.choices[0].message.content)
                
                # Save to Progress
                timestamp = datetime.now().strftime("%Y-%m-%d")
                st.session_state.memory['progress'].append(f"{timestamp}: Mock Exam Score: {res.choices[0].message.content[:50]}")
                save_memory(st.session_state.memory)

# --- (Other features like Study Materials and Smart Quiz remain the same) ---
