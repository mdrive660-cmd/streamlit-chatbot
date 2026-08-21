# app.py
import os
import json
import requests
import streamlit as st

st.set_page_config(page_title="Groq demo", layout="centered")
st.title("Groq API demo (Streamlit)")

# Prefer environment variable, but allow entering in the UI (keeps app flexible)
env_key = os.getenv("GROQ_API_KEY", "")
api_key = st.text_input("Groq API Key", value=env_key, type="password")
st.markdown("You can also set the GROQ_API_KEY environment variable before running the app.")

prompt = st.text_area("Prompt", value="Write a short poem about Streamlit and Groq.", height=180)

# Example endpoint — replace with the actual Groq endpoint & model path
GROQ_ENDPOINT = "https://api.groq.ai/v1/models/groq-1/completions"

def call_groq_api(prompt_text: str, key: str):
    if not key:
        raise ValueError("API key is required")
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
    }
    # Example payload — adapt fields to the Groq API's required schema
    payload = {
        "prompt": prompt_text,
        "max_tokens": 150,
        # "temperature": 0.7,
        # Add any other params your Groq API expects
    }
    resp = requests.post(GROQ_ENDPOINT, headers=headers, json=payload, timeout=30)
    resp.raise_for_status()
    # Try to decode JSON, else return text
    try:
        return resp.json()
    except json.JSONDecodeError:
        return resp.text

if st.button("Generate"):
    try:
        with st.spinner("Calling Groq..."):
            result = call_groq_api(prompt, api_key)
        st.success("Done")
        st.subheader("Raw response")
        st.code(json.dumps(result, indent=2))
        # If the response contains a text/completion field, show it nicely:
        # Adjust keys below to match Groq's response shape
        completion_text = None
        if isinstance(result, dict):
            # common possibilities — adapt to actual API
            for k in ("text", "completion", "output", "generated_text"):
                if k in result:
                    completion_text = result[k]
                    break
            # sometimes completion sits in choices[0].text (OpenAI style)
            if completion_text is None and "choices" in result:
                try:
                    completion_text = result["choices"][0].get("text") or result["choices"][0].get("message", {}).get("content")
                except Exception:
                    completion_text = None
        if completion_text:
            st.subheader("Completion")
            st.write(completion_text)
        else:
            st.info("No high-level completion field found in the response; see raw output above.")
    except requests.HTTPError as e:
        st.error(f"HTTP error: {e} - {getattr(e.response, 'text', '')}")
    except Exception as e:
        st.error(f"Error: {e}")
