import os
import streamlit as st
from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint

class LlamaLLM:
    def __init__(self, user_controls_input):
        self.user_controls_input = user_controls_input

    def get_llm_model(self):
        try:
            hf_api_key = self.user_controls_input.get("HUGGINGFACEHUB_API_TOKEN", "")
            selected_llama_model = self.user_controls_input.get("selected_llama_model", "meta-llama/Meta-Llama-3-8B-Instruct")
            
            if hf_api_key == '':
                hf_api_key = os.environ.get("HUGGINGFACEHUB_API_TOKEN", "")
                
            if hf_api_key == '':
                st.error("Please Enter the HuggingFace API Token")
            else:
                os.environ["HUGGINGFACEHUB_API_TOKEN"] = hf_api_key

            llm_endpoint = HuggingFaceEndpoint(
                repo_id=selected_llama_model,
                task="text-generation",
                max_new_tokens=512,
                do_sample=False,
                huggingfacehub_api_token=hf_api_key
            )
            llm = ChatHuggingFace(llm=llm_endpoint)
        except Exception as e:
            raise ValueError(f"Error Occurred With Exception : {e}")
        return llm
