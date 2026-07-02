import streamlit as st
from langchain_core.messages import HumanMessage,AIMessage,ToolMessage
import json
import os


class DisplayResultStreamlit:
    def __init__(self,graph,user_message,user_controls_input=None):
        self.graph = graph
        self.user_message = user_message
        self.user_controls_input = user_controls_input or {}

    def display_result_on_ui(self):
        graph = self.graph
        user_message = self.user_message
        print(user_message)

        st.info("🤖 Starting Job Search Agent Graph workflow...")
                    
        resume_text = self.user_controls_input.get("resume_text", "")
        job_type = self.user_controls_input.get("job_type", "")
        job_location = self.user_controls_input.get("job_location", "")
        date_posted_filter = self.user_controls_input.get("date_posted_filter", "Last 24 hours")
        serpapi_api_key = self.user_controls_input.get("SERPAPI_API_KEY", "")
        if not serpapi_api_key:
            serpapi_api_key = os.environ.get("SERPAPI_API_KEY", "")
            
        initial_state = {
            "messages": [HumanMessage(content="Find matching jobs for the candidate.")],
            "resume_text": resume_text,
            "job_type": job_type,
            "job_location": job_location,
            "date_posted_filter": date_posted_filter,
            "api_keys": {
                "SERPAPI_API_KEY": serpapi_api_key
            },
            "extracted_profile": {},
            "search_url": "",
            "raw_jobs": [],
            "matched_jobs": []
        }
        
        with st.spinner("Analyzing candidate profile, retrieving listings, and matching top 10 jobs..."):
            res = graph.invoke(initial_state)
        
        # Show extracted profile details in an expander
        extracted = res.get("extracted_profile", {})
        if extracted:
            with st.expander("Analyzed Candidate Profile", expanded=True):
                st.markdown(f"**Experience Level:** {extracted.get('experience_level', 'N/A')}")
                st.markdown(f"**Preferred Location:** {extracted.get('preferred_location', 'N/A')}")
                st.markdown(f"**Key Skills Extracted:** {', '.join(extracted.get('skills', []))}")
                st.markdown(f"**Optimal Search Keywords:** `{extracted.get('job_search_keyword', 'N/A')}`")
                st.markdown(f"**Experience Summary:** {extracted.get('experience_summary', 'N/A')}")

        # Show the generated search URL
        search_url = res.get("search_url", "")
        if search_url:
            st.markdown(f"🔗 **Constructed Search Query URL:** [Google Jobs Search Link]({search_url})")

        # Show matching jobs
        matched_jobs = res.get("matched_jobs", [])
        if matched_jobs:
            st.subheader(f"🏆 Top {len(matched_jobs)} Closest Matching Jobs")
            for index, job in enumerate(matched_jobs):
                score = job.get("match_score", 0.0)
                title = job.get("title", "Untitled Job")
                company = job.get("company", "Unknown Company")
                location = job.get("location", "Remote/Varies")
                link = job.get("link", "https://google.com/search")
                explanation = job.get("match_explanation", "")
                posted_at = job.get("posted_at", "")
                posted_str = f" &nbsp;|&nbsp; 📅 {posted_at}" if posted_at else ""

                # Dynamic color coding based on score
                if score >= 80:
                    score_badge = f'<span style="color:#00E676; font-weight:bold; font-size:18px;">{score}% Match</span>'
                elif score >= 60:
                    score_badge = f'<span style="color:#FFD600; font-weight:bold; font-size:18px;">{score}% Match</span>'
                else:
                    score_badge = f'<span style="color:#FF1744; font-weight:bold; font-size:18px;">{score}% Match</span>'

                st.markdown(
                    f"""
                    <div style="border: 1px solid #333; padding: 15px; border-radius: 8px; margin-bottom: 10px; background-color: #1E1E1E;">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <h4 style="margin: 0; color: #E0E0E0;">{index + 1}. {title}</h4>
                                <p style="margin: 3px 0; color: #9E9E9E;">🏢 {company} &nbsp;|&nbsp; 📍 {location}{posted_str}</p>
                            </div>
                            <div style="text-align: right;">
                                {score_badge}
                            </div>
                        </div>
                        <div style="margin-top: 8px; color: #B0B0B0; font-size: 14px;">
                            <strong>Match Reason:</strong> {explanation}
                        </div>
                        <div style="margin-top: 10px;">
                            <a href="{link}" target="_blank" style="text-decoration: none; color: #29B6F6; font-weight: bold;">Apply / View Job ↗</a>
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True
                )
        else:
            st.warning("⚠️ No matching jobs found. Try adjusting your search parameters or resume upload.")