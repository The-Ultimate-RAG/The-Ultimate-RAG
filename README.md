---
title: The Ultimate RAG
emoji: 🌍
colorFrom: pink
colorTo: indigo
sdk: docker
pinned: false
short_description: the ultimate rag
---

<a id="readme-top"></a>

<div align="center">

# <img src="docs/images/logo.svg" alt="Logo" width="25"> The Ultimate RAG

<p>
  <strong> 🏫 An Innopolis University software project that generates cited responses from a local database of your documents.</strong>
</p>

<p>
  <img alt="License" src="https://img.shields.io/badge/License-MIT-blue.svg"/>
  <img alt="Python" src="https://img.shields.io/badge/Python-3.12+-blue?logo=python&logoColor=white"/>
  <img alt="Docker" src="https://img.shields.io/badge/Docker-Required-blue?logo=docker&logoColor=white"/>
  <img alt="PostgreSQL" src="https://img.shields.io/badge/PostgreSQL-Required-blue?logo=postgresql&logoColor=white"/>
</p>

<p>
   <a href="https://the-ultimate-rag-hf-the-ultimate-rag.hf.space">🌐 Check deployed version</a>
   &middot;
   <a href="https://drive.google.com/drive/folders/1qhe6bS2l7sW1-1g0tBf0Awz1ew-popKV">🎬 View demo</a>
</p>
</div>

<details>
  <summary><strong>📑 Table of Contents</strong></summary>
  <ul>
    <li><a href="#overview">Overview</a></li>
    <li><a href="#getting-started">Getting Started</a></li>
    <li><a href="#usage">Usage</a></li>
    <li><a href="#hyperlinks-to-the-documentation">Hyperlinks to the Documentation</a></li>
    <li><a href="#license">License</a></li>
  </ul>
</details>

## <a id="overview"></a>🎯 Overview

**The Ultimate RAG** is a powerful Retrieval-Augmented Generation (RAG) system designed to provide accurate,
source-cited answers to your questions. Simply upload your documents (`.pdf`, `.docx`, `.txt`), and the application will
build a local knowledge base. You can then query this knowledge base in natural language, and the system will generate a
response, citing the specific sources from your documents.

### ✨ Features

- **📝 Multi-Format Support:** Upload documents in `.txt`, `.doc`, `.docx`, `.pdf`, and other formats.
- **🤖 LLM Integration:** Powered by Google's Gemini API (with support for other models like Mistral).
- **🔒 Secure User Authentication:** Features robust user registration and login with JWT and password hashing.
- **💾 Local Knowledge Base:** All your data is processed and stored locally using PostgreSQL.
- **🐳 Dockerized:** Easy to set up and run in an isolated environment using Docker.

### 📊 Project context diagram

<div style="text-align: center;">
  <img src="docs/images/project-context-diagram.png" alt="Project Context Diagram"/>
</div>

### 🗺️ Feature Roadmap

<div style="margin-left: auto; margin-right: auto; width: fit-content;">

| Status     | Feature                                                                 | Notes |
|------------|-------------------------------------------------------------------------|-------|
| To Do      | Deploy final product                                                    |       |
| To Do      | Implement updated UI                                                    |       |
| To Do      | Improve connection between user queries and predeclared prompts         |       |
| Completed  | Accelerate file processing                                              |       |
| Completed  | Reduce response time                                                    |       |
| Completed  | Enhance response quality and accuracy                                   |       |
| Completed  | Enhance UI/UX                                                           |       |
| Completed  | Enhance security (secret management)                                    |       |
| Completed  | Introduce CI/CD pipeline                                                |       |
| Completed  | Implement unit and integration tests                                    |       |
| Completed  | Implement response streaming                                            | Streaming responses during generation |
| Completed  | Add JSON, CSV, and MD file support                                      |       |
| Completed  | Add chat separation functionality                                      |       |
| Completed  | Add multilingual support                                                |       |
| Completed  | Add TXT, DOC, DOCX, and PDF support                                    |       |
| Completed  | Implement API with simple frontend                                      |       |
| Completed  | Establish ready-to-use RAG skeleton                                     | Core functionality: file attachment, cited responses with sources |

</div>

<p align="right">(<a href="#readme-top">🔝 back to top</a>)</p>

## <a id="getting-started"></a>🚀 Getting Started

Follow these instructions to get a copy of the project up and running on your local machine.

### ✅ Prerequisites

Ensure you have the following software installed before you begin:

- [**🐍 Python (3.12+)**](https://www.python.org/)
- [**🐋 Docker**](https://www.docker.com/get-started/)
- [**🐘 PostgreSQL**](https://www.postgresql.org/download/)

### <a id="installation"></a>🛠️ Installation

1. **📥 Clone the Repository**
   ```bash
   git clone https://github.com/The-Ultimate-RAG/The-Ultimate-RAG.git
   cd The-Ultimate-RAG
   ```

2. **⚙️ Configure Environment Variables**

   Create a file named `.env` in the root directory.
   Copy the contents of the block below into it and fill in your details.

   ```dotenv
   # .env
   DATABASE_URL=postgresql://postgres:mysecretpassword@localhost:5432/rag_db

   # --- Large Language Model API Key ---
   # 🔑 Get your key from Google AI Studio. You can swap this for Mistral if you don't have any.
   GEMINI_API_KEY=your-gemini-api-key

   # --- Security Settings ---
   # 🔐 A random string used for an extra layer of password security.
   SECRET_PEPPER=your-super-secret-pepper-string
   JWT_ALGORITHM=HS256
   ```

3. **🐍 Set Up a Python Virtual Environment**

   It's highly recommended to use a virtual environment to manage project dependencies.

    - **On macOS/Linux:**
      ```bash
      python3 -m venv env
      source env/bin/activate
      ```
    - **On Windows:**
      ```bash
      python -m venv env
      .\env\Scripts\activate
      ```

4. **📦 Install Dependencies**
   ```bash
   pip install -r ./app/requirements.txt
   ```

5. **🚀 Launch the Application**
    - Ensure the Docker daemon is running on your machine.
    - Run qdrant database
      ```bash
      docker run --publish 6333:6333 --publish 6334:6334 --volume path_to_project\database:/qdrant/storage qdrant/qdrant
      ```
    - Wait until installation complete
    - Run the main application
      ```bash
      python -m app.core.main
      ```

6. **🌐 Access the Server**

   Once the containers are up and running, open your web browser and navigate to:
   **[`http://127.0.0.1:5050`](http://127.0.0.1:5050)**

   You should see the application's welcome page.
   To stop the application, press `Ctrl+C` in the terminal where the
   script is running.

<p align="right">(<a href="#readme-top">🔝 back to top</a>)</p>

## <a id="usage"></a>📖 Usage

You can try currently deployed version of the
system [here](https://huggingface.co/spaces/The-Ultimate-RAG-HF/The-Ultimate-RAG). **Note**: you should use the
following instructions:

- 🌐 Access the cite, you should see the *main* page with the name of the system
- ➕ Press the button "+ Add new chat", wait until the *login* page is loaded
- 🔍 Find button "Register" (for now it is highly recommended to follow the instructions *strictly*) and press it
- 📝 You should be redirected to *sign up* page, here you should enter your credentials (you can use Test1@test1.com in
  all
  field for testing)
- 🖱️ Click **ONLY ONCE** on the button "Sign Up", and wait (for now it takes around 10 seconds to load *chat* page)
- 💬 Now you will be able to communicate with the system
- ❓ You can try to ask anything and attach files. Enter a query and press the *enter* button (near the input area)

<p align="right">(<a href="#readme-top">🔝 back to top</a>)</p>

## <a id="hyperlinks-to-the-documentation"></a>📚 Hyperlinks to the documentation

- 👨‍💻 [Development](CONTRIBUTING.md)
- 📊 [Quality characteristics and quality attribute scenarios](./docs/quality-assurance/quality-attribute-scenarios.md)
- 🛡️ Quality assurance
    - 🤖 [Automated tests](./docs/quality-assurance/automated-tests.md)
    - 👥 [User acceptance tests](./docs/quality-assurance/user-acceptance-tests.md)
- 🏗️ Build and deployment
    - 🔄 [Continuous integration](./docs/automation/continuous-integration.md)
    - 🚢 [Continuous deployment](./docs/automation/continuous-delivery.md)
- 🏛️ [Architecture](./docs/architecture/architecture.md)

<p align="right">(<a href="#readme-top">🔝 back to top</a>)</p>

## <a id="license"></a>📜 License

This project is licensed under the [MIT License](LICENSE).

<p align="right">(<a href="#readme-top">🔝 back to top</a>)</p>