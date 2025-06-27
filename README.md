---
title: The Ultimate RAG
emoji: 🌍
colorFrom: pink
colorTo: indigo
sdk: docker
pinned: false
short_description: the ultimate rag
---
<div align="center">

# 🌍 The Ultimate RAG

<p>
  <strong>[S25] An Innopolis University software project that generates cited responses from a local database of your documents.</strong>
</p>

<p>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg"/>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white"/>
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Required-blue?logo=docker&logoColor=white"/>
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Required-blue?logo=postgresql&logoColor=white"/>
</p>

</div>

---

## 🎯 Overview

**The Ultimate RAG** is a powerful Retrieval-Augmented Generation (RAG) system designed to provide accurate, source-cited answers to your questions. Simply upload your documents (`.pdf`, `.docx`, `.txt`), and the application will build a local knowledge base. You can then query this knowledge base in natural language, and the system will generate a response, citing the specific sources from your documents.

### ✨ Features

-   **📝 Multi-Format Support:** Upload documents in `.txt`, `.doc`, `.docx`, `.pdf`, and other formats.
-   **🤖 LLM Integration:** Powered by Google's Gemini API (with support for other models like Mistral).
-   **🔒 Secure User Authentication:** Features robust user registration and login with JWT and password hashing.
-   **📚 Local Knowledge Base:** All your data is processed and stored locally using PostgreSQL.
-   **🐳 Dockerized:** Easy to set up and run in an isolated environment using Docker.

---

## 🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### ✅ Prerequisites

Ensure you have the following software installed before you begin:

-   [**Python (3.12+)**](https://www.python.org/)
-   [**Docker & Docker Compose**](https://www.docker.com/get-started/)
-   [**PostgreSQL**](https://www.postgresql.org/download/)

### 🛠️ Installation

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/PopovDanil/The-Ultimate-RAG](https://github.com/PopovDanil/The-Ultimate-RAG)
    cd The-Ultimate-RAG
    ```

2.  **Configure Environment Variables**

    Create a file named `.env` in the root directory.
    Copy the contents of `.env.example` (or the block below) into it and fill in your details.

    ```dotenv
    # .env

    # --- Email Sending Service (for password resets, etc.) ---
    # ⚠️ For Gmail, use an "App Password" instead of your regular password.
    SMTP_HOST=smtp.gmail.com
    SMTP_PORT=587
    SMTP_EMAIL=your-email@gmail.com
    SMTP_PASSWORD=your-app-password
    APPLICATION_SERVER_URL=http://localhost:5050

    # --- PostgreSQL Database Connection ---
    # Format: postgresql://USER:PASSWORD@HOST:PORT/DATABASE_NAME
    POSTGRES_URL=postgresql://postgres:mysecretpassword@localhost:5432/rag_db

    # --- Large Language Model API Key ---
    # Get your key from Google AI Studio. You can swap this for another provider in the settings.
    GEMINI_API_KEY=your-gemini-api-key

    # --- Security Settings ---
    # A random string used for an extra layer of password security.
    SECRET_PEPPER=your-super-secret-pepper-string
    JWT_ALGORITHM=HS256
    ```
    *Note: The `app` directory might have its own `.env` file. Ensure you are creating/editing the correct one as per the project's structure.*

3.  **Set Up a Python Virtual Environment**

    It's highly recommended to use a virtual environment to manage project dependencies.

    -   **On macOS/Linux:**
        ```bash
        python3 -m venv env
        source env/bin/activate
        ```
    -   **On Windows:**
        ```bash
        python -m venv env
        .\env\Scripts\activate
        ```

4.  **Install Dependencies**
    ```bash
    pip install -r ./app/requirements.txt
    ```

5.  **Launch the Application**
    -   Ensure the Docker daemon is running on your machine.
    -   Navigate to the `app` directory.
    -   Run the `start_application.py`

6.  **Access the Server**

    Once the containers are up and running, open your web browser and navigate to:
    **[http://127.0.0.1:5050](http://127.0.0.1:5050)**

    You should see the application's welcome page. To stop the application, press `Ctrl+C` in the terminal where the script is running.

---

## 📖 Usage

1.  **👤 Register:** Create a new user account.
2.  **📤 Upload a File:** Click the upload button and select a supported file.
3.  **⏳ Wait for Processing:** The system will chunk, embed, and store your document in the database.
4.  **❓ Ask a Question:** Once the file is processed, type your question into the prompt box and submit.
5.  **💡 Receive Your Answer:** The application will generate a response based on the contents of your documents and provide citations.
---

## 🚑 Troubleshooting

-   **Registration Error / Database Connection Error:**
    -   Ensure your **PostgreSQL server is running**.
    -   Double-check that the `POSTGRES_URL` in your `.env` file is correct (username, password, host, port, dbname).
    -   Verify that the Docker containers can communicate with your PostgreSQL instance. Check firewall rules if necessary.

-   **Invalid API Key:**
    -   Ensure your `GEMINI_API_KEY` is correct and has been activated.

-   **CalledProcessError for Docker:**
    - Ensure that Docker Engine is running
---

## 📜 License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.