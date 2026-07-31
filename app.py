import streamlit as st
import pandas as pd
import os
from groq import Groq
from dotenv import load_dotenv
from pypdf import PdfReader # <--- New library for PDFs

load_dotenv()
st.set_page_config(page_title="StudySphere AI", page_icon="🎓", layout="wide")

api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")
client = Groq(api_key=api_key)

# Helper function to read PDFs
def extract_text_from_pdf(file):
    reader = PdfReader(file)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

with st.sidebar:
    st.title("🎓 StudySphere AI")
    menu = st.selectbox("Choose a Tool", ["📅 Study Planner", "📝 AI Summarizer", "🧠 Quiz Generator"])

# --- FEATURE 1: PLANNER --- (Same as before)
if menu == "📅 Study Planner":
    st.header("📅 AI Study Schedule Generator")
    subject = st.text_input("Subject")
    if st.button("Generate"):
        res = client.chat.completions.create(messages=[{"role": "user", "content": f"Plan for {subject}"}], model="llama-3.3-70b-versatile")
        st.write(res.choices[0].message.content)

# --- FEATURE 2: SUMMARIZER (NOW WITH FILE UPLOAD) ---
elif menu == "📝 AI Summarizer":
    st.header("📝 AI Document Summarizer")
    st.write("Upload a PDF or paste text to get a summary.")
    
    uploaded_file = st.file_uploader("Upload your notes (PDF)", type=['pdf'])
    raw_text = st.text_area("OR Paste text here:")
    
    if st.button("Summarize ✨"):
        context = ""
        if uploaded_file:
            with st.spinner("Reading PDF..."):
                context = extract_text_from_pdf(uploaded_file)
        elif raw_text:
            context = raw_text
            
        if context:
            with st.spinner("Analyzing content..."):
                prompt = f"Summarize this study material into key concepts: {context[:8000]}"
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.markdown(res.choices[0].message.content)
        else:
            st.warning("Please upload a file or paste text!")

# --- FEATURE 3: QUIZ (NOW WITH FILE UPLOAD) ---
elif menu == "🧠 Quiz Generator":
    st.header("🧠 Instant Practice Quiz")
    st.write("Turn your documents into a practice test.")
    
    uploaded_file = st.file_uploader("Upload study material (PDF)", type=['pdf'], key="quiz_upload")
    
    if st.button("Generate Quiz 🎯"):
        if uploaded_file:
            with st.spinner("Reading document..."):
                context = extract_text_from_pdf(uploaded_file)
                prompt = f"Create a 5-question quiz based on this text: {context[:8000]}. Include an answer key at the bottom."
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.markdown(res.choices[0].message.content)
        else:
            st.warning("Please upload a PDF file first!")
