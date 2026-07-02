import json
from src.nodes.job_schemas import JobQueryExtractor
from src.state.job_state import JobState
from langchain_core.prompts import ChatPromptTemplate

class JobAnalyzerNode:
    def __init__(self, model):
        self.llm = model

    def process(self, state: JobState) -> dict:
        resume_text = state.get("resume_text", "")
        job_type = state.get("job_type", "")

        if not resume_text and not job_type:
            resume_text = "Candidate with skills in Python development, FastAPI, SQL, and AWS."
            job_type = "Python Developer"

        system_prompt = (
            "You are an expert technical recruiter. Analyze the candidate's resume text and/or target job type "
            "to extract structured candidate profile metadata. Make sure to identify primary skills, experience level, "
            "preferred location, experience summary, and generate an optimal search query string for job boards."
        )
        
        user_content = f"Resume Content:\n{resume_text}\n\nTarget Job Type:\n{job_type}"
        
        profile_dict = None
        try:
            structured_llm = self.llm.with_structured_output(JobQueryExtractor)
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_content)
            ])
            chain = prompt | structured_llm
            extracted = chain.invoke({})
            profile_dict = extracted.dict()
        except Exception:
            # Fallback to standard prompt extraction with JSON instructions
            instructions = (
                "\n\nReturn the output ONLY as a valid JSON object matching the following structure:\n"
                "{{\n"
                '  "skills": ["skill1", "skill2"],\n'
                '  "experience_level": "Junior/Mid/Senior/Lead",\n'
                '  "preferred_location": "Remote/Hybrid/CityName",\n'
                '  "job_search_keyword": "software engineer",\n'
                '  "experience_summary": "Summary text"\n'
                "}}\n"
                "Do not include any markdown tags (like ```json) or explanation outside the JSON."
            )
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt + instructions),
                ("user", "Resume Content:\n{resume_text}\n\nTarget Job Type:\n{job_type}")
            ])
            chain = prompt | self.llm
            res = chain.invoke({"resume_text": resume_text, "job_type": job_type})
            content = res.content.strip()
            if content.startswith("```"):
                lines = content.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines[-1].strip() == "```":
                    lines = lines[:-1]
                content = "\n".join(lines).strip()
            try:
                data = json.loads(content)
                extracted = JobQueryExtractor(**data)
                profile_dict = extracted.dict()
            except Exception:
                profile_dict = {
                    "skills": [s.strip() for s in job_type.split()] if job_type else ["Python", "FastAPI"],
                    "experience_level": "Mid-Senior",
                    "preferred_location": "Remote",
                    "job_search_keyword": job_type if job_type else "Python Developer",
                    "experience_summary": resume_text[:150]
                }
        
        return {"extracted_profile": profile_dict}
