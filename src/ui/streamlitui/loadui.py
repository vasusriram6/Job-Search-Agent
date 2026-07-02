import streamlit as st
import os

from src.ui.uiconfigfile import Config

class LoadStreamlitUI:
    def __init__(self):
        self.config=Config()
        self.user_controls={}

    def load_streamlit_ui(self):

        with st.sidebar:
            # Get options from config
            llm_options = self.config.get_llm_options()

            # LLM selection
            self.user_controls["selected_llm"] = st.selectbox("Select Model Family", llm_options)


            if self.user_controls["selected_llm"] == 'Gemini':
                # Model selection
                model_options = self.config.get_gemini_model_options()
                self.user_controls["selected_gemini_model"] = st.selectbox("Select Model", model_options)
                self.user_controls["GOOGLE_API_KEY"] = st.session_state["GOOGLE_API_KEY"]=st.text_input("Gemini API Key",type="password")
                # Validate API key
                if not self.user_controls["GOOGLE_API_KEY"]:
                    st.warning("⚠️ Please enter your Gemini API key to proceed. Don't have? refer : https://aistudio.google.com/")

            elif self.user_controls["selected_llm"] == 'Groq':                
                model_options = self.config.get_groq_model_options()
                self.user_controls["selected_groq_model"] = st.selectbox("Select Model", model_options)
                self.user_controls["GROQ_API_KEY"] = st.session_state["GROQ_API_KEY"]=st.text_input("GROQ API Key",type="password")                
                if not self.user_controls["GROQ_API_KEY"]:
                    st.warning("⚠️ Please enter your GROQ API key to proceed. Don't have? refer : https://console.groq.com/keys ")

            elif self.user_controls["selected_llm"] == 'Mistral':
                model_options = self.config.get_mistral_model_options()
                self.user_controls["selected_mistral_model"] = st.selectbox("Select Model", model_options)
                self.user_controls["MISTRAL_API_KEY"] = st.session_state["MISTRAL_API_KEY"]=st.text_input("Mistral API Key",type="password")
                if not self.user_controls["MISTRAL_API_KEY"]:
                    st.warning("⚠️ Please enter your Mistral API key to proceed. Don't have? refer : https://console.mistral.ai/")

            elif self.user_controls["selected_llm"] == 'Llama':
                model_options = self.config.get_llama_model_options()
                self.user_controls["selected_llama_model"] = st.selectbox("Select Model", model_options)
                self.user_controls["HUGGINGFACEHUB_API_TOKEN"] = st.session_state["HUGGINGFACEHUB_API_TOKEN"]=st.text_input("Hugging Face API Token",type="password")
                if not self.user_controls["HUGGINGFACEHUB_API_TOKEN"]:
                    st.warning("⚠️ Please enter your Hugging Face API token to proceed. Don't have? refer : https://huggingface.co/settings/tokens")
            st.info("You can leave the LLM API key empty if you have it stored in the .env file")

            self.user_controls["SERPAPI_API_KEY"] = st.session_state["SERPAPI_API_KEY"] = st.text_input("SerpAPI API Key", type="password")
            if not self.user_controls["SERPAPI_API_KEY"]:
                st.info("Note: You can leave this field empty if you have SerpAPI API key in the .env file. Not having the key in either place will run the agent with mock jobs database stored locally.")

        st.header("Job Search AI Agent", text_alignment="center")
        st.subheader("Job Search Criteria:")
        col1, col2 = st.columns(2)
        with col1:
            uploaded_file = st.file_uploader("Upload your resume (PDF)", type=["pdf"])
            if uploaded_file is not None:
                try:
                    from pypdf import PdfReader
                    reader = PdfReader(uploaded_file)
                    text = ""
                    for page in reader.pages:
                        text += page.extract_text() or ""
                    self.user_controls["resume_text"] = text
                    st.success("✅ Resume PDF uploaded and parsed successfully!")
                except Exception as e:
                    st.error(f"❌ Failed to parse PDF: {e}")
        with col2:
            self.user_controls["job_type"] = st.text_input("Type of Job (e.g. Software Engineer, Frontend Developer)", placeholder="e.g. Machine Learning Engineer")
            self.user_controls["job_location"] = st.text_input("Job Location (e.g. Remote, San Francisco, New York)", placeholder="e.g. Remote")
            self.user_controls["date_posted_filter"] = st.selectbox(
                "Date Posted Filter",
                options=["Last 24 hours", "Last 2 days", "Last week", "Last month", "Anytime"],
                index=0
            )

        return self.user_controls