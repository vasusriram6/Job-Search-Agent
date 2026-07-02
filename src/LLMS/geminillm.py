import os
import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI

class GeminiLLM:
    def __init__(self, user_controls_input):
        self.user_controls_input = user_controls_input

    def get_llm_model(self):
        try:
            google_api_key = self.user_controls_input.get("GOOGLE_API_KEY", "")
            selected_gemini_model = self.user_controls_input.get("selected_gemini_model", "gemini-3.1-flash-lite")
            
            if google_api_key == '':
                google_api_key = os.environ.get("GOOGLE_API_KEY", "")
                
            if google_api_key == '':
                st.error("Please Enter the Google API KEY")

            llm = ChatGoogleGenerativeAI(api_key=google_api_key, model=selected_gemini_model)
        except Exception as e:
            raise ValueError(f"Error Occurred With Exception : {e}")
        return llm
