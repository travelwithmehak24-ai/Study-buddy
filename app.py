import streamlit as st
import pandas as pd
import os
import time
from groq import Groq
from dotenv import load_dotenv

# 1. Setup & Security
load_dotenv()
st.set_page_config(page_title="StudySphere AI", page_icon="🎓", layout="wide")

# Universal API Key Finder (Works for Local and Server)
api_key = st.secrets.get("GROQ_API_KEY") or os.getenv("GROQ_API_KEY")

if not api_key:
    st.error("⚠️ GROQ_API_KEY not found! Add it to your .env file or Streamlit Secrets.")
    st.stop()

client = Groq(api_key=api_key)

# 2. Sidebar Navigation
with st.sidebar:
    st.title("🎓 StudySphere AI")
    st.markdown("---")
    menu = st.selectbox(
        "Choose a Tool", 
        ["📅 Study Planner", "📝 Note Summarizer", "🧠 Quiz & Flashcards", "✍️ Essay Polisher", "⏳ Focus Timer"]
    )
    st.markdown("---")
    st.info("Powered by Llama-3.3-70B AI")

# --- FEATURE 1: STUDY PLANNER ---
if menu == "📅 Study Planner":
    st.header("📅 AI Study Schedule Generator")
    st.write("Tell the AI what you're studying, and it will build your calendar.")
    
    col1, col2 = st.columns(2)
    with col1:
        subject = st.text_input("What are you studying?", placeholder="e.g. Organic Chemistry")
        exam_date = st.date_input("Exam Date")
    with col2:
        hours = st.slider("Daily Study Hours", 1, 10, 3)
        style = st.selectbox("Study Style", ["Visual", "Practical", "Deep Theory", "Speed Review"])

    if st.button("Build My Plan 🚀"):
        prompt = f"Act as a professional academic coach. Create a day-by-day study plan for {subject} leading up to {exam_date}. I have {hours} hours per day. Focus on a {style} learning style. Format with bullet points and bold headings."
        
        with st.spinner("Generating your path to success..."):
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.markdown(res.choices[0].message.content)

# --- FEATURE 2: NOTE SUMMARIZER ---
elif menu == "📝 Note Summarizer":
    st.header("📝 AI Note Summarizer")
    st.write("Paste long lectures or textbook chapters to get the 'Golden Nuggets' of info.")
    
    raw_text = st.text_area("Paste text here...", height=300)
    mode = st.radio("Summary Depth", ["Bullet Points", "Executive Summary", "Explain Like I'm 5"])

    if st.button("Summarize ✨"):
        if raw_text:
            prompt = f"Task: {mode}. Text to analyze: {raw_text}"
            with st.spinner("Distilling information..."):
                res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
                st.success("Summary Complete!")
                st.write(res.choices[0].message.content)
        else:
            st.warning("Please paste some text first!")

# --- FEATURE 3: QUIZ & FLASHCARDS ---
elif menu == "🧠 Quiz & Flashcards":
    st.header("🧠 Active Recall Generator")
    st.write("Generate practice questions from your notes to test your knowledge.")
    
    context = st.text_area("Paste your study material here:", height=200)
    q_type = st.segmented_control("Question Type", options=["Multiple Choice", "True/False", "Short Answer"])

    if st.button("Generate Test 🎯"):
        prompt = f"Based on this content: {context}, create 5 {q_type} questions. Provide the questions first, then a section at the bottom called 'ANSWER KEY' with explanations."
        with st.spinner("Writing your exam..."):
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.markdown(res.choices[0].message.content)

# --- FEATURE 4: ESSAY POLISHER ---
elif menu == "✍️ Essay Polisher":
    st.header("✍️ Academic Writing Assistant")
    st.write("Paste your draft and the AI will improve your tone and grammar.")
    
    draft = st.text_area("Paste your essay draft:", height=250)
    goal = st.selectbox("Improvement Goal", ["Professional/Academic Tone", "Make it Conciser", "Fix Grammar & Flow"])

    if st.button("Polish My Writing 🪄"):
        prompt = f"Act as an expert editor. Rewrite the following text with this goal: {goal}. Keep the original meaning but make it sound significantly better: {draft}"
        with st.spinner("Editing..."):
            res = client.chat.completions.create(messages=[{"role": "user", "content": prompt}], model="llama-3.3-70b-versatile")
            st.subheader("Polished Version:")
            st.write(res.choices[0].message.content)

# --- FEATURE 5: FOCUS TIMER ---
elif menu == "⏳ Focus Timer":
    st.header("⏳ Pomodoro Productivity Zone")
    st.write("Stay focused with the 25/5 rule.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        minutes = st.number_input("Study Session (Minutes)", value=25)
        if st.button("Start Timer 🔔"):
            seconds = minutes * 60
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            for i in range(seconds, 0, -1):
                mins, secs = divmod(i, 60)
                timer_display = f"{mins:02d}:{secs:02d}"
                status_text.title(f"🔥 Focus: {timer_display}")
                # Update progress
                progress_bar.progress((seconds - i) / seconds)
                time.sleep(1)
            
            st.success("Session Complete! Take a 5-minute break. ☕")
            st.balloons()
    
    with col2:
        st.info("💡 **Did you know?** The Pomodoro technique helps prevent mental fatigue and keeps you focused for longer periods.")
        st.image("https://images.unsplash.com/photo-1434030216411-0b793f4b4173?ixlib=rb-1.2.1&auto=format&fit=crop&w=1000&q=80", caption="Focus on your goals.")