import streamlit as st
import pandas as pd
import requests
from dotenv import load_dotenv
import os

st.set_page_config(page_title="AI Form Generator", layout="centered")
load_dotenv()
GEMINI_API_KEY = os.getenv("API_KEY")
GAS_URL = os.getenv("BACKEND_URL", "https://script.google.com/macros/s/AKfycbwgdq5ihodg-opiJUs1MnCXKVUUcufkofAF5mqBecSjwM257TVHFkboqPRkByw1bQyErA/exec")


def generate_responses_with_gemini(prompt, count=5):
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-pro:generateContent?key={GEMINI_API_KEY}"
    headers = {"Content-Type": "application/json"}
    data = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {"temperature": 0.7}
    }
    try:
        res = requests.post(url, headers=headers, json=data)
        if res.ok:
            text = res.json()["candidates"][0]["content"]["parts"][0]["text"]
            return text.strip().split("\n")[:count]
        else:
            return [f"API error: {res.text}"]
    except Exception as e:
        return [f"Error: {e}"]

st.title("🧠 AI-Powered Google Form Generator")

form_title = st.text_input("📋 Enter Google Form Title")


if "questions" not in st.session_state:
    st.session_state.questions = []

if st.button("➕ Add Question"):
    st.session_state.questions.append({
        "text": "",
        "type": "Short Answer",
        "options": []
    })

for i, q in enumerate(st.session_state.questions):
    st.markdown(f"---\n### Question {i + 1}")

    q["text"] = st.text_input("Question Text", value=q["text"], key=f"text_{i}")
    q["type"] = st.selectbox(
        "Question Type",
        ["Short Answer", "Paragraph", "Multiple Choice", "Checkboxes", "Dropdown"],
        index=["Short Answer", "Paragraph", "Multiple Choice", "Checkboxes", "Dropdown"].index(q["type"]),
        key=f"type_{i}"
    )


    if q["type"] in ["Multiple Choice", "Checkboxes", "Dropdown"]:
        csv = st.file_uploader("Upload CSV for options (first column used)", key=f"csv_{i}")
        manual = st.text_area("Or enter comma-separated options", key=f"manual_{i}")
        num = st.number_input("🔢 Number of AI responses", 1, 20, value=5, key=f"num_{i}")

        if st.button("✨ Generate with Gemini", key=f"gen_{i}"):
            if q["text"]:
                with st.spinner("Generating..."):
                    prompt = f"Generate {num} realistic options for a form question: '{q['text']}'"
                    ai_data = generate_responses_with_gemini(prompt, count=num)
                    q["options"] = [opt.strip("•- ").strip() for opt in ai_data]
                    st.success("Generated using AI!")
                    st.write(q["options"])
            else:
                st.warning("Enter question text first.")

    
        if csv:
            df = pd.read_csv(csv)
            q["options"] = df.iloc[:, 0].dropna().astype(str).tolist()
        elif manual:
            q["options"] = [x.strip() for x in manual.split(",")]


if st.button("🚀 Generate Google Form"):
    if not form_title or not st.session_state.questions:
        st.error("Please enter a form title and at least one question.")
    else:
        form_data = {
            "title": form_title,
            "questions": st.session_state.questions
        }

        try:
            response = requests.post(GAS_URL, json=form_data)
            if response.ok:
                form_link = response.json().get("form_url", "")
                st.success("✅ Google Form created!")
                st.markdown(f"[🔗 Click to Open Form]({form_link})")
            else:
                st.error("❌ Failed to create form. Check your script or URL.")
        except Exception as e:
            st.error(f"Error occurred: {e}")
