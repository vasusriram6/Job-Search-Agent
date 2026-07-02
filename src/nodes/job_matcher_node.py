import json
import streamlit as st
from typing import List, Dict, Any
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from src.state.job_state import JobState
from src.nodes.job_schemas import JobMatchResult, JobMatchResultsList
from langchain_core.prompts import ChatPromptTemplate

class JobMatcherNode:
    def __init__(self, model):
        self.llm = model

    def process(self, state: JobState) -> dict:
        profile = state.get("extracted_profile", {})
        raw_jobs = state.get("raw_jobs", [])

        if not raw_jobs:
            return {"matched_jobs": []}

        # Step 1: Pre-filter and rank jobs using TF-IDF cosine similarity
        skills_str = " ".join(profile.get("skills", []))
        summary_str = profile.get("experience_summary", "")
        keyword_str = profile.get("job_search_keyword", "")
        candidate_text = f"{keyword_str} {skills_str} {summary_str}"

        job_texts = []
        for job in raw_jobs:
            job_texts.append(f"{job.get('title', '')} {job.get('company', '')} {job.get('description', '')}")

        vectorizer = TfidfVectorizer()
        try:
            tfidf_matrix = vectorizer.fit_transform([candidate_text] + job_texts)
            similarities = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])[0]
        except Exception:
            similarities = [0.0] * len(raw_jobs)

        scored_jobs = []
        for idx, job in enumerate(raw_jobs):
            score = float(similarities[idx] * 100)
            scored_jobs.append({
                "job": job,
                "base_score": score,
                "original_index": idx
            })

        scored_jobs.sort(key=lambda x: x["base_score"], reverse=True)
        top_10_scored = scored_jobs[:10]

        # Step 2: Use LLM to refine the match scores and provide explanations in one bulk call
        jobs_input_list = []
        for idx, item in enumerate(top_10_scored):
            job = item["job"]
            jobs_input_list.append({
                "index": idx,
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location", ""),
                "link": job.get("link", ""),
                "posted_at": job.get("posted_at", "N/A"),
                "snippet": job.get("snippet", job.get("description", "")[:150])
            })

        system_prompt = (
            "You are an AI job matcher. You will be given a candidate's profile (skills, experience summary, and target job) "
            "and a list of up to 10 potential jobs. For each job, you must evaluate the match and return a JobMatchResultsList container "
            "containing a list of JobMatchResult items. Each JobMatchResult must match the job at the corresponding index, with:\n"
            "- title: (exactly as provided in the input job)\n"
            "- company: (exactly as provided in the input job)\n"
            "- location: (exactly as provided in the input job)\n"
            "- link: (exactly as provided in the input job)\n"
            "- posted_at: (exactly as provided in the input job or N/A)\n"
            "- match_score: (float between 0 and 100, reflecting candidate fit)\n"
            "- match_explanation: (1-2 sentences explaining why this job matches or what skills are missing)"
        )

        user_template = (
            "Candidate Skills: {skills}\n"
            "Candidate Experience Summary: {summary}\n"
            "Candidate Target Job: {target_job}\n\n"
            "Jobs List:\n{jobs_list}"
        )

        refined_matches = {}
        try:
            structured_llm = self.llm.with_structured_output(JobMatchResultsList)
            prompt = ChatPromptTemplate.from_messages([
                ("system", system_prompt),
                ("user", user_template)
            ])
            chain = prompt | structured_llm
            res = chain.invoke({
                "skills": str(profile.get('skills', [])),
                "summary": summary_str,
                "target_job": profile.get('job_search_keyword', ''),
                "jobs_list": json.dumps(jobs_input_list, indent=2)
            })
            for idx, match_item in enumerate(res.matches):
                refined_matches[idx] = {
                    "match_score": match_item.match_score,
                    "match_explanation": match_item.match_explanation,
                    "posted_at": match_item.posted_at
                }
        except Exception:
            # Fallback to standard prompt extraction with JSON instructions if structured output is not supported
            instructions = (
                "\n\nReturn the output ONLY as a valid JSON object matching the following structure:\n"
                "{{\n"
                '  "matches": [\n'
                '    {{\n'
                '      "title": "Job Title",\n'
                '      "company": "Company",\n'
                '      "location": "Location",\n'
                '      "link": "Link",\n'
                '      "posted_at": "Posted date",\n'
                '      "match_score": 85.0,\n'
                '      "match_explanation": "Explanation"\n'
                '    }}\n'
                '  ]\n'
                "}}\n"
                "Do not include any markdown tags (like ```json) or explanation outside the JSON."
            )
            try:
                prompt = ChatPromptTemplate.from_messages([
                    ("system", system_prompt + instructions),
                    ("user", user_template)
                ])
                chain = prompt | self.llm
                res = chain.invoke({
                    "skills": str(profile.get('skills', [])),
                    "summary": summary_str,
                    "target_job": profile.get('job_search_keyword', ''),
                    "jobs_list": json.dumps(jobs_input_list, indent=2)
                })
                content = res.content.strip()
                if content.startswith("```"):
                    lines = content.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].strip() == "```":
                        lines = lines[:-1]
                    content = "\n".join(lines).strip()
                parsed = json.loads(content)
                validated = JobMatchResultsList(**parsed)
                for idx, match_item in enumerate(validated.matches):
                    refined_matches[idx] = {
                        "match_score": match_item.match_score,
                        "match_explanation": match_item.match_explanation,
                        "posted_at": match_item.posted_at
                    }
            except Exception:
                pass

        final_matched_jobs = []
        for idx, item in enumerate(top_10_scored):
            job = item["job"]
            refined = refined_matches.get(idx, {})
            score = refined.get("match_score", item["base_score"])
            score = round(float(score), 1)
            explanation = refined.get("match_explanation")
            if not explanation:
                skills_matched = [s for s in profile.get("skills", []) if s.lower() in job.get("description", "").lower()]
                explanation = f"Matched based on keywords. Overlapping skills: {', '.join(skills_matched[:4]) if skills_matched else 'General Match'}."

            score = max(0.0, min(100.0, score))
            if score == 0.0:
                score = round(max(10.0, item["base_score"]), 1)

            final_matched_jobs.append({
                "title": job.get("title"),
                "company": job.get("company"),
                "location": job.get("location"),
                "link": job.get("link"),
                "posted_at": refined.get("posted_at") or job.get("posted_at", ""),
                "match_score": score,
                "match_explanation": explanation
            })

        # Re-sort final list by match_score descending
        final_matched_jobs.sort(key=lambda x: x["match_score"], reverse=True)

        return {"matched_jobs": final_matched_jobs}
