# The-Ultimate-RAG

## Overview

[S25] The Ultimate RAG is a software project for Innopolis University, designed to make proper responses based on local
database with proper citations.

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
   ```bash
   python -m venv env
   source env/bin/activate  # On Unix/Linux/Mac
   # or
   env\Scripts\activate     # On Windows
3. **Install required libraries**
   
   Within the activated virtual environment, install the dependencies:
   ```bash
   pip install -r ./app/requirements.txt
   ```
   Note: ensure you are in the virtual environment before running the command

4. **Set up Docker**
    - Ensure Docker is running on your machine
    - Open a terminal, navigate to project directory, and run:
    ```bash 
    docker-compose up --build
    ```
    Note: This builds the Docker images and start the containers defined in docker-compose.yml. To stop them later, run:
   ```bash
   docker-compose down
   ```
5. **Wait for installation**
   
   The installation process may take around 10 minutes or more as the models and dependencies are downloaded and set up
6. **Server access**

   Once the containers are running, visit http://localhost:5050. You should see the application’s welcome page


## Usage 
1. **Upload your file**
   - Supported file formats: TXT, DOC, PDF 
2. **Write a prompt**
   - Enter a question or statement related to the uploaded file's content
3. **Wait**
   - For now, the speed is too slow. Be patient, please
