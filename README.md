---
title: The Ultimate RAG
emoji: 🌍
colorFrom: pink
colorTo: yellow
sdk: docker
pinned: false
short_description: the ultimate rag
---

# The-Ultimate-RAG

## Overview

[S25] The Ultimate RAG is an Innopolis University software project that generates cited responses from a local database.

## Prerequisites

Before you begin, ensure the following is installed on your machine:
- [Python](https://www.python.org/) 
- [Docker](https://www.docker.com/get-started/)

## Installation

1. **Clone the repository**
    ```bash
   git clone https://github.com/PopovDanil/The-Ultimate-RAG
   cd The-Ultimate-RAG
   ```
2. **Set up a virtual environment (recommended)**

   To isolate project dependencies and avoid conflicts, create a virtual environment:
    - **On Unix/Linux/macOS:**
   ```bash
   python3 -m venv env
   source env/bin/activate
   ```
    - **On Windows:**
    ```bash
    python -m venv env
    env\Scripts\activate
    ```
3. **Install required libraries**

   Within the activated virtual environment, install the dependencies:
   ```bash
   pip install -r ./app/requirements.txt
   ```
   *Note:* ensure you are in the virtual environment before running the command

4. **Set up Docker**
    - Ensure Docker is running on your machine
    - Open a terminal, navigate to project directory, and run:
    ```bash 
    docker-compose up --build
    ```
   *Note:* The initial build may take 10–20 minutes, as it needs to download large language models and other
   dependencies. 
   Later launches will be much faster.
   
5. **Server access**

   Once the containers are running, visit `http://localhost:5050`. You should see the application’s welcome page

To stop the application and shut down all containers, press `Ctrl+C` in the terminal where `docker-compose` is running, 
and then run: 
```bash
   docker-compose down
```

## Usage

1. **Upload your file:** click the upload button and select a supported file (`.txt`, `.doc`, `.docx`, or `.pdf`)
2. **Ask a question**: Once the file is processed, type your question into the prompt box and submit.
3. **Receive your answer** 

**A note on performance**

Response generation is a computationally intensive task.
The time to receive an answer may vary depending on your machine's hardware and the complexity of the query.

## License

This project is licensed under the [MIT License](LICENSE).