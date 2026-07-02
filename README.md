### Job Search Agent Application

The project is developed in Antigravity IDE, with CI/CD implementation using Github Actions and Docker.

### Sample app screenshots:

Idle app:

<img width="629" height="324" alt="homescreen" src="https://github.com/user-attachments/assets/4d7a5d44-10de-4690-83d4-8c403d146067" />


App output after submitting job search criteria and resume:

<img width="629" height="324" alt="jobs_retrieved" src="https://github.com/user-attachments/assets/7c9ceedd-5ead-4fe0-9b8a-a8eec2ec9ec7" />



### Steps to run the app on local device:

1. Clone the repository

2. Create and activate the project virtual environment.

3. Once the virtual environment is activated, install the dependencies.

4. To run the application:
```bash
streamlit run app.py
```
This will open the app in a web browser.

Note: When running the app with the above method, you can store any required API keys in the .env file. By doing so, you don't have to paste the API key again in the app page.

### Steps to run the app directly via Docker container:
1.	Make sure Docker Desktop is installed and is running
2.	Then in command prompt, type:
```bash
docker pull noobmlengineer/job-search-agent-app:latest
```
3.	To run the container, use any one of the following methods:
    - Open Docker Desktop window, click on “Images” on left sidebar, then click the run button of the downloaded image. In the optional settings, set the host port to “8501”.
    - Run in command prompt:
```bash
docker run -p 8501:8501 noobmlengineer/job-search-agent-app:latest
```
4.	Then in a web browser, open the website:
```bash
localhost:8501
```

