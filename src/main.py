import streamlit as st
import os
from src.ui.streamlitui.loadui import LoadStreamlitUI
from src.graph.graph_builder import GraphBuilder
from src.ui.streamlitui.display_result import DisplayResultStreamlit

def load_langgraph_agenticai_app():
    """
    Loads and runs the LangGraph AgenticAI application with Streamlit UI.
    This function initializes the UI, handles user input, configures the LLM model,
    sets up the graph based on the selected use case, and displays the output while 
    implementing exception handling for robustness.

    """
    from dotenv import load_dotenv
    load_dotenv()

    ##Load UI
    ui=LoadStreamlitUI()
    user_input=ui.load_streamlit_ui()

    if not user_input:
        st.error("Error: Failed to load user input from the UI.")
        return
    trigger = st.button("Find Top 10 Matching Jobs", use_container_width=True)
    user_message = "Find jobs" if trigger else None

    if user_message:
        try:
            # Set keys in environment variables for LangChain client wrappers
            for key in ["GROQ_API_KEY", "GOOGLE_API_KEY", "MISTRAL_API_KEY", "HUGGINGFACEHUB_API_TOKEN", "SERPAPI_API_KEY"]:
                if user_input.get(key):
                    os.environ[key] = user_input[key]

            ## Configure The LLM's
            selected_llm = user_input.get("selected_llm")
            if selected_llm == "Groq":
                from src.LLMS.groqllm import GroqLLM
                obj_llm_config = GroqLLM(user_contols_input=user_input)
            elif selected_llm == "Gemini":
                from src.LLMS.geminillm import GeminiLLM
                obj_llm_config = GeminiLLM(user_controls_input=user_input)
            elif selected_llm == "Mistral":
                from src.LLMS.mistralllm import MistralLLM
                obj_llm_config = MistralLLM(user_controls_input=user_input)
            elif selected_llm == "Llama":
                from src.LLMS.llamallm import LlamaLLM
                obj_llm_config = LlamaLLM(user_controls_input=user_input)
            else:
                st.error(f"Error: Unknown LLM selection '{selected_llm}'")
                return

            model=obj_llm_config.get_llm_model()

            if not model:
                st.error("Error: LLM model could not be initialized")
                return
            
            ## Graph Builder
            graph_builder=GraphBuilder(model)
            try:
                graph=graph_builder.setup_graph()
                DisplayResultStreamlit(graph,user_message,user_input).display_result_on_ui()
            except Exception as e:
                st.error(f"Error: Graph set up failed- {e}")
                return

        except Exception as e:
            st.error(f"Error: Graph set up failed- {e}")
            return
