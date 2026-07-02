import os
import json
import asyncio
import streamlit as st
from typing import List, Dict, Any
from src.state.job_state import JobState
from src.nodes.job_schemas import JobListing

class JobRetrieverNode:
    def __init__(self):
        pass

    def parse_posted_at_to_hours(self, posted_at_str: str) -> float:
        if not posted_at_str:
            return 9999.0
        s = posted_at_str.lower().strip()
        try:
            digits = [int(word) for word in s.split() if word.isdigit()]
            val = float(digits[0]) if digits else 1.0
        except Exception:
            val = 1.0

        if "hour" in s:
            return val
        elif "day" in s:
            return val * 24.0
        elif "yesterday" in s:
            return 24.0
        elif "week" in s:
            return val * 7.0 * 24.0
        elif "month" in s:
            return val * 30.0 * 24.0
        elif "minute" in s:
            return val / 60.0
        elif "just now" in s or "online" in s or "active" in s:
            return 0.1
        else:
            if "yesterday" in s:
                return 24.0
            return 9999.0

    def process(self, state: JobState) -> dict:
        profile = state.get("extracted_profile", {})
        keywords = profile.get("job_search_keyword", state.get("job_type", "Software Engineer"))
        location = state.get("job_location", "") or profile.get("preferred_location", "Remote")
        date_posted_filter = state.get("date_posted_filter", "Last 24 hours")
        
        api_keys = state.get("api_keys", {})
        api_key = api_keys.get("SERPAPI_API_KEY", "").strip()
        if not api_key:
            api_key = os.environ.get("SERPAPI_API_KEY", "").strip()

        jobs: List[Dict[str, Any]] = []

        if api_key:
            try:
                st.info(f"Fetching jobs from Google Jobs API via SerpAPI for query '{keywords}' in '{location}'...")
                jobs = self.fetch_jobs_via_serpapi(keywords, location, api_key, date_posted_filter)
                if jobs:
                    st.success(f"Successfully retrieved {len(jobs)} jobs via SerpAPI!")
                else:
                    st.warning("No jobs returned from SerpAPI. Falling back to mock dataset.")
                    jobs = self.get_mock_jobs()
            except Exception as e:
                import traceback
                print("\n=== SERPAPI ERROR DETAILS ===")
                traceback.print_exc()
                print("==============================\n")
                st.warning(f"Failed to fetch jobs via SerpAPI: {e}. Falling back to mock dataset.")
                jobs = self.get_mock_jobs()
        else:
            st.info("No SerpAPI API Key supplied. Using offline mock jobs database.")
            jobs = self.get_mock_jobs()


        target_loc = state.get("job_location", "").strip().lower()
        if target_loc:
            filtered_jobs = []
            for job in jobs:
                job_loc = job.get("location", "").lower()
                if target_loc in job_loc or job_loc in target_loc:
                    filtered_jobs.append(job)
                elif target_loc == "sf" and "san francisco" in job_loc:
                    filtered_jobs.append(job)
                elif target_loc == "ny" and "new york" in job_loc:
                    filtered_jobs.append(job)
                elif "remote" in target_loc and "remote" in job_loc:
                    filtered_jobs.append(job)
            
            if filtered_jobs:
                jobs = filtered_jobs
                st.success(f"📍 Filtered {len(jobs)} jobs matching location: '{state.get('job_location')}'")
            else:
                st.warning(f"⚠️ No jobs matched location '{state.get('job_location')}'. Showing all available jobs.")



        # Filter jobs by date posted
        if date_posted_filter and date_posted_filter != "Anytime":
            max_hours = 9999.0
            if date_posted_filter == "Last 24 hours":
                max_hours = 24.0
            elif date_posted_filter == "Last 2 days":
                max_hours = 48.0
            elif date_posted_filter == "Last week":
                max_hours = 168.0
            elif date_posted_filter == "Last month":
                max_hours = 720.0
                
            filtered_by_date = []
            for job in jobs:
                posted_at = job.get("posted_at", "")
                hours = self.parse_posted_at_to_hours(posted_at)
                if hours <= max_hours:
                    filtered_by_date.append(job)
            
            if filtered_by_date:
                jobs = filtered_by_date
                st.success(f"📅 Filtered {len(jobs)} jobs matching date posted: '{date_posted_filter}'")
            else:
                st.warning(f"⚠️ No jobs matched date posted filter '{date_posted_filter}'. Showing all available jobs as fallback.")

        # Validate with JobListing Pydantic schema
        validated_jobs = []
        for job in jobs:
            try:
                validated_job = JobListing(
                    title=job.get("title", "Untitled Job"),
                    company=job.get("company", "Unknown Company"),
                    location=job.get("location", "Remote/Varies"),
                    link=job.get("link", "https://google.com/search"),
                    description=job.get("description", job.get("snippet", "No description provided.")),
                    snippet=job.get("snippet", job.get("description", "")[:150]),
                    posted_at=job.get("posted_at", "")
                )
                validated_jobs.append(validated_job.dict())
            except Exception:
                # If validation fails for a single record, append it directly
                validated_jobs.append({
                    "title": job.get("title", "Untitled Job"),
                    "company": job.get("company", "Unknown Company"),
                    "location": job.get("location", "Remote/Varies"),
                    "link": job.get("link", "https://google.com/search"),
                    "description": job.get("description", "No description."),
                    "snippet": job.get("snippet", ""),
                    "posted_at": job.get("posted_at", "")
                })

        return {"raw_jobs": validated_jobs}

    def fetch_jobs_via_serpapi(self, keywords: str, location: str, api_key: str, date_posted_filter: str = "Last 24 hours") -> List[Dict[str, Any]]:
        import requests
        
        params = {
            "engine": "google_jobs",
            "q": keywords,
            "api_key": api_key,
            "hl": "en",
            "gl": "us",
            #"num": "10"
        }
        if location:
            params["location"] = location
            
        # Map date_posted_filter to SerpAPI's date_posted chips
        chip_val = None
        if date_posted_filter == "Last 24 hours":
            chip_val = "date_posted:today"
        elif date_posted_filter == "Last 2 days":
            chip_val = "date_posted:3days"
        elif date_posted_filter == "Last week":
            chip_val = "date_posted:week"
        elif date_posted_filter == "Last month":
            chip_val = "date_posted:month"
            
        if chip_val:
            params["chips"] = chip_val
            
        url = "https://serpapi.com/search.json"
        
        response = requests.get(url, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        
        jobs_list = data.get("jobs_results", [])
        
        mapped_jobs = []
        for job in jobs_list:
            # Map SerpAPI fields (company_name, apply_options link) to internal JobListing schema
            company = job.get("company_name", "Unknown Company")
            
            link = ""
            apply_options = job.get("apply_options", [])
            if isinstance(apply_options, list) and len(apply_options) > 0:
                link = apply_options[0].get("link", "")
            if not link:
                link = job.get("link", "")
            if not link:
                link = "https://google.com/search"
                
            # Extract posted_at relative date string
            posted_at = ""
            detected_ext = job.get("detected_extensions", {})
            if isinstance(detected_ext, dict):
                posted_at = detected_ext.get("posted_at", "")
            if not posted_at:
                exts = job.get("extensions", [])
                if isinstance(exts, list):
                    for ext in exts:
                        if "ago" in ext.lower() or "yesterday" in ext.lower() or "hour" in ext.lower() or "day" in ext.lower() or "week" in ext.lower() or "month" in ext.lower():
                            posted_at = ext
                            break
                            
            mapped_jobs.append({
                "title": job.get("title", "Untitled Job"),
                "company": company,
                "location": job.get("location", "Remote/Varies"),
                "link": link,
                "description": job.get("description", "No description provided."),
                "snippet": job.get("snippet", job.get("description", "")[:150]),
                "posted_at": posted_at
            })
            
        return mapped_jobs

    def get_mock_jobs(self) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Python Software Engineer",
                "company": "InnovateTech Solutions",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/innovatetech-python-dev",
                "description": "We are seeking a Python Software Engineer with strong experience in FastAPI, Docker, and AWS. You will develop backend microservices, implement secure data models, and integrate with PostgreSQL database. Experience with langchain or LLM integrations is a big plus.",
                "snippet": "Python, FastAPI, AWS, Docker. Backend microservices.",
                "posted_at": "2 hours ago"
            },
            {
                "title": "Senior AI / Machine Learning Engineer",
                "company": "DeepMind Innovations",
                "location": "San Francisco, CA",
                "link": "https://www.linkedin.com/jobs/view/deepmind-ml-eng",
                "description": "Looking for an ML engineer to build production agents. Requirements: PyTorch, NLP pipelines, vector databases (FAISS, Pinecone), and LangGraph. You will build agentic pipelines, perform prompt tuning, and optimize inference on Gemini and Llama architectures.",
                "snippet": "PyTorch, NLP, Vector DBs, LangGraph, LLMs.",
                "posted_at": "12 hours ago"
            },
            {
                "title": "Frontend React Developer",
                "company": "Interface Labs",
                "location": "New York, NY (Hybrid)",
                "link": "https://www.linkedin.com/jobs/view/interface-labs-react-dev",
                "description": "Looking for a Frontend React Developer. Must be proficient in TypeScript, React 18, and state management (Redux, Zustand). You will create clean interfaces, implement responsive charts, and write custom utility styles using vanilla CSS or Tailwind CSS.",
                "snippet": "React, TypeScript, CSS, State management.",
                "posted_at": "1 day ago"
            },
            {
                "title": "DevOps Cloud Engineer",
                "company": "SkyHigh Tech",
                "location": "Remote (USA)",
                "link": "https://www.linkedin.com/jobs/view/skyhigh-devops-eng",
                "description": "DevOps Engineer required to manage multi-cloud infrastructure. Expertise in Terraform, Kubernetes, GitHub Actions CI/CD pipelines, and AWS configuration (IAM, ECS, RDS). Ensure high availability, containerization, and secure deployment workflows.",
                "snippet": "Terraform, Kubernetes, CI/CD, AWS, DevOps automation.",
                "posted_at": "36 hours ago"
            },
            {
                "title": "Product Manager - AI Products",
                "company": "NextGen AI Corp",
                "location": "San Jose, CA",
                "link": "https://www.linkedin.com/jobs/view/nextgen-ai-pm",
                "description": "Drive the roadmap for our AI agent developer tools. Collaborate with engineering and design to define product requirements, user stories, and feature launches. Experience with Scrum, Agile, and deep familiarity with LLM ecosystems required.",
                "snippet": "Agile, Product Roadmap, AI Developer Tools.",
                "posted_at": "3 days ago"
            },
            {
                "title": "Data Analyst",
                "company": "MetricInsights",
                "location": "Chicago, IL",
                "link": "https://www.linkedin.com/jobs/view/metrics-data-analyst",
                "description": "Analyze large datasets to drive business insights. Required: SQL expert, Python (Pandas, Numpy), and BI visualization (Tableau, PowerBI). Design reporting metrics and run A/B testing pipelines.",
                "snippet": "SQL, Python Pandas, Tableau, Data Visualization.",
                "posted_at": "5 days ago"
            },
            {
                "title": "Full Stack Engineer (Python & React)",
                "company": "Nexus Web Solutions",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/nexus-fullstack",
                "description": "Build modern web apps. Tech stack: Python, Django, React, Next.js, and PostgreSQL. Design REST APIs, manage database migrations, and construct interactive frontends with premium UX and responsive grid structures.",
                "snippet": "Django, Python, React, Next.js, PostgreSQL.",
                "posted_at": "1 week ago"
            },
            {
                "title": "Senior Backend Go Engineer",
                "company": "StreamFlow Services",
                "location": "Austin, TX (Hybrid)",
                "link": "https://www.linkedin.com/jobs/view/streamflow-go-eng",
                "description": "We are hiring a backend engineer skilled in Go (Golang) to optimize real-time streaming tools. Must be experienced with Kafka, gRPC, Redis caching, and distributed system architectures.",
                "snippet": "Go, Kafka, gRPC, Redis, Backend performance.",
                "posted_at": "2 weeks ago"
            },
            {
                "title": "Java Spring Boot Developer",
                "company": "Enterprise Tech Group",
                "location": "Dallas, TX",
                "link": "https://www.linkedin.com/jobs/view/etg-java-spring",
                "description": "Looking for Java developers with extensive Spring Boot, Spring Cloud, Hibernate, and Oracle SQL experience. Build enterprise scale, highly secure web services and REST endpoints.",
                "snippet": "Java, Spring Boot, Hibernate, Oracle database.",
                "posted_at": "3 weeks ago"
            },
            {
                "title": "Security & Penetration Tester",
                "company": "SecureNet Consulting",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/securenet-pentest",
                "description": "Conduct security assessments, code audits, and penetration testing on cloud applications and networks. Required: OWASP Top 10 knowledge, Python scripting, Kali Linux, and certifications like OSCP.",
                "snippet": "Cybersecurity, Penetration testing, Scripting, Code audit.",
                "posted_at": "4 weeks ago"
            },
            {
                "title": "QA Automation Engineer",
                "company": "TestVerify Labs",
                "location": "Boston, MA (Hybrid)",
                "link": "https://www.linkedin.com/jobs/view/qa-automation",
                "description": "Write automated test scripts using Python, Selenium, and Pytest. Build end-to-end integration tests for web systems and integrate tests into GitHub Actions pipelines.",
                "snippet": "Python, Selenium, Pytest, QA automation.",
                "posted_at": "1 month ago"
            },
            {
                "title": "Data Engineer (Spark & Python)",
                "company": "DataStreams Inc",
                "location": "Seattle, WA",
                "link": "https://www.linkedin.com/jobs/view/datastreams-data-eng",
                "description": "Build scalable data pipelines. Requirements: Apache Spark, Hadoop, Python, and SQL. Experience with Snowflake or Databricks is preferred. Optimize ETL pipelines for petabyte-scale data extraction.",
                "snippet": "Apache Spark, Snowflake, Python, SQL, ETL pipeline.",
                "posted_at": "2 months ago"
            },
            {
                "title": "Cloud Architect",
                "company": "Apex Cloud Systems",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/apex-cloud-architect",
                "description": "Design secure, cloud-native architecture solutions on AWS and Azure. Required: AWS Certified Solutions Architect, Infrastructure as Code (Terraform), and cloud network security design.",
                "snippet": "AWS, Azure, Cloud Architecture, Terraform.",
                "posted_at": "3 months ago"
            },
            {
                "title": "UI/UX Product Designer",
                "company": "CreativeVibe Studio",
                "location": "Los Angeles, CA",
                "link": "https://www.linkedin.com/jobs/view/creative-ui-ux",
                "description": "Design interactive web and mobile prototypes. Tools: Figma, Adobe XD. Experience creating harmony palettes, micro-interactions, responsive design wireframes, and validating with user testing.",
                "snippet": "Figma, UI/UX Design, Prototyping, Wireframing.",
                "posted_at": "2 hours ago"
            },
            {
                "title": "iOS Swift App Developer",
                "company": "MobileMinds Inc",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/swift-ios",
                "description": "Develop native iOS applications using Swift, SwiftUI, and Combine. Must be experienced with local storage (CoreData/Realm) and API connections. Experience publishing apps on App Store.",
                "snippet": "Swift, SwiftUI, iOS App development, API integration.",
                "posted_at": "15 hours ago"
            },
            {
                "title": "Embedded Software Developer",
                "company": "RoboSystems Solutions",
                "location": "Detroit, MI",
                "link": "https://www.linkedin.com/jobs/view/embedded-c",
                "description": "Design embedded software for robotics controls. Expertise in C/C++, RTOS, microcontrollers (STM32, ESP32), and serial communication protocols (I2C, SPI, CAN).",
                "snippet": "C/C++, RTOS, Microcontrollers, SPI/I2C/CAN.",
                "posted_at": "yesterday"
            },
            {
                "title": "Django Backend Web Developer",
                "company": "WebPower Systems",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/django-backend",
                "description": "Looking for Django developer. Solid Python foundation, Django REST Framework (DRF), Celery for background tasks, Redis, PostgreSQL, and deploying onto AWS EC2.",
                "snippet": "Python, Django, Celery, Redis, PostgreSQL.",
                "posted_at": "4 days ago"
            },
            {
                "title": "Node.js API Engineer",
                "company": "FastServer Solutions",
                "location": "San Francisco, CA (Hybrid)",
                "link": "https://www.linkedin.com/jobs/view/node-js-api",
                "description": "Build high-throughput backend services using Node.js, Express, NestJS, and MongoDB. Must have deep understanding of event loop, asynchronous code, and Redis caching layers.",
                "snippet": "Node.js, Express, NestJS, MongoDB, Caching.",
                "posted_at": "6 days ago"
            },
            {
                "title": "Machine Learning Researcher",
                "company": "NeuroLink Systems",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/ml-researcher",
                "description": "Research new deep learning models for sequence processing. Strong credentials in PyTorch, Transformer layers, attention mechanisms, and publishing at CVPR, NeurIPS or ICLR.",
                "snippet": "Kubernetes, Monitoring, Scripting, Incident response.",
                "posted_at": "1 month ago"
            },
            {
                "title": "Technical Writer",
                "company": "DocuSolutions Group",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/tech-writer",
                "description": "Write clear documentation for software libraries, developer APIs, and cloud services. Must read Python/JavaScript code, format Markdown documents, and compile structural guides.",
                "snippet": "DBT, Snowflake, SQL, Looker, Business Intelligence.",
                "posted_at": "2 hours ago"
            },
            {
                "title": "Solidity Blockchain Developer",
                "company": "CryptoNodes LLC",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/solidity-crypto",
                "description": "Seeking Solidity developer to write smart contracts for DeFi protocols. Deep understanding of Ethereum, gas optimizations, Hardhat, Ethers.js, and smart contract security audit principles.",
                "snippet": "Solidity, Ethereum, Web3, Smart Contracts, DeFi.",
                "posted_at": "yesterday"
            },
            {
                "title": "Salesforce Developer",
                "company": "CloudAdvisors Inc",
                "location": "Phoenix, AZ (Hybrid)",
                "link": "https://www.linkedin.com/jobs/view/salesforce-dev",
                "description": "Customize and develop Salesforce applications. Required: Apex, Lightning Web Components (LWC), Visualforce, and Salesforce integrations with external REST services.",
                "snippet": "Apex, LWC, Salesforce, API integrations.",
                "posted_at": "4 days ago"
            },          
            {
                "title": "Solidity Blockchain Developer",
                "company": "CryptoNodes LLC",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/solidity-crypto",
                "description": "Seeking Solidity developer to write smart contracts for DeFi protocols. Deep understanding of Ethereum, gas optimizations, Hardhat, Ethers.js, and smart contract security audit principles.",
                "snippet": "Solidity, Ethereum, Web3, Smart Contracts, DeFi.",
                "posted_at": "yesterday"
            },  
            {
                "title": "Flutter Cross-Platform Developer",
                "company": "MobilityLab Solutions",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/flutter-dart",
                "description": "Develop high-performing cross-platform mobile apps for Android and iOS using Dart and Flutter. Understand BLoC state management and native bridge integration.",
                "snippet": "Flutter, Dart, Mobile App developer, BL data.",
                "posted_at": "3 weeks ago"
            },
            {
                "title": "Flutter Cross-Platform Developer",
                "company": "MobilityLab Solutions",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/flutter-dart",
                "description": "Develop high-performing cross-platform mobile apps for Android and iOS using Dart and Flutter. Understand BLoC state management and native bridge integration.",
                "snippet": "Flutter, Dart, Mobile App developer, BLoC.",
                "posted_at": "1 week ago"
            },  
            {
                "title": "Kubernetes Orchestration Expert",
                "company": "CloudNative Systems",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/k8s-expert",
                "description": "We are seeking a Kubernetes Orchestration Engineer. Set up multi-region EKS clusters, write complex Helm charts, configure Istio Service Mesh, and implement autoscaling policies based on Prometheus alerts.",
                "snippet": "EKS, Kubernetes, Helm, Istio Service Mesh.",
                "posted_at": "1 month ago"
            },
            {
                "title": "Vue.js Frontend Specialist",
                "company": "VueWorld Services",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/vue-js-dev",
                "description": "Develop high quality reactive user panels using Vue 3, Pinia, Vite, and CSS grid structures. Ensure beautiful layout styling, interactive grids, and optimized loading times.",
                "snippet": "Vue 3, Pinia, TypeScript, Vite frontend engineering.",
                "posted_at": "2 months ago"
            },
            {
                "title": "Security Operations Center (SOC) Analyst",
                "company": "ShieldGuard Security",
                "location": "Hybrid (Miami, FL)",
                "link": "https://www.linkedin.com/jobs/view/soc-analyst",
                "description": "Monitor and analyze network traffic logs for potential security alerts. Experienced with SIEM platforms (Splunk, Sentinel), incident log reporting, and threat identification.",
                "snippet": "SIEM, Security logs monitoring, Splunk, Incident analysis.",
                "posted_at": "3 months ago"
            },
            {
                "title": "Vue.js Frontend Specialist",
                "company": "VueWorld Services",
                "location": "Remote",
                "link": "https://www.linkedin.com/jobs/view/vue-js-dev",
                "description": "Develop high quality reactive user panels using Vue 3, Pinia, Vite, and CSS grid structures. Ensure beautiful layout styling, interactive grids, and optimized loading times.",
                "snippet": "Vue 3, Pinia, TypeScript, Vite frontend engineering.",
                "posted_at": "2 months ago"
            },
            {
                "title": "Security Operations Center (SOC) Analyst",
                "company": "ShieldGuard Security",
                "location": "Hybrid (Miami, FL)",
                "link": "https://www.linkedin.com/jobs/view/soc-analyst",
                "description": "Monitor and analyze network traffic logs for potential security alerts. Experienced with SIEM platforms (Splunk, Sentinel), incident log reporting, and threat identification.",
                "snippet": "SIEM, Security logs monitoring, Splunk, Incident analysis.",
                "posted_at": "3 months ago"
            }
        ]
