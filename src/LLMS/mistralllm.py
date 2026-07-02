import os
import streamlit as st
from langchain_mistralai import ChatMistralAI

class MistralLLM:
    def __init__(self, user_controls_input):
        self.user_controls_input = user_controls_input

    def get_llm_model(self):
        try:
            mistral_api_key = self.user_controls_input.get("MISTRAL_API_KEY", "")
            selected_mistral_model = self.user_controls_input.get("selected_mistral_model", "mistral-large-latest")
            
            if mistral_api_key == '':
                mistral_api_key = os.environ.get("MISTRAL_API_KEY", "")
                
            if mistral_api_key == '':
                st.error("Please Enter the Mistral API KEY")

            llm = ChatMistralAI(api_key=mistral_api_key, model=selected_mistral_model)
        except Exception as e:
            raise ValueError(f"Error Occurred With Exception : {e}")
        return llm
