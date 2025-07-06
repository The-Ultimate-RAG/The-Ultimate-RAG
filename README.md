---
title: The Ultimate RAG
emoji: 🌍
colorFrom: pink
colorTo: indigo
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

You can try currently deployed version of the system [here](https://huggingface.co/spaces/The-Ultimate-RAG-HF/The-Ultimate-RAG). **Note**: you should use the following instructions:
- Access the cite, you should see the *main* page with the name of the system
- Press the button "+ Add new chat", wait until the *login* page is loaded
- Find button "Register" (for now it is highly recommended to follow the instructions *strictly*) and press it
- You should be redirected to *sing up* page, here you should enter your credentials (you can use Test1@test1.com in all field for testing)
- Click **ONLY ONCE** on the button "Sign Up", and wait (for now it takes around 10 seconds to load *chat* page)
- Now you will be able to communicate with the system
- You can try to ask any thing and attach files. Enter a query and press the *enter* button (near the input area)

## Architecture

### Static view

The following **diagram** depicts the current state of our codebase organization.
![Diagram description](./docs/architecture/static-view/static-view.png)

We have decided to adapt this architecture to enhance the *maintainability* of the product for the following reasons:
- [x] A **modular** system, which is reflected by the use of subsystems in our code increases the **reusability** of the components.
- [x] Individual subsystems can be easily **analyzed** in conjunction with monolith products.
- [x] This approach ensures the ease and speed of **testing**.
- [x] Additionally, each part can be **easily modified** without affecting the rest of the codebase.

### Dynamic view

The following **diagram** depicts the one non-trivial case of the system use: user queries the system and attach file. This diagram can halp in understating the pipeline of file processing and response generation:
![Diagram description](./docs/architecture/dynamic-view/dynamic-view.jpeg)

## Development

### Kanban board
**Link to the board**: [Kanban board](https://github.com/orgs/The-Ultimate-RAG/projects/3/views/2)

#### Column Entry Criteria

##### 1. **To Do**
- [x] Issue is created using the project’s issue templates.
- [x] Issue is **estimated** (story points) by the Team.
- [x] Issue is **prioritized** by the Team.
- [x] Issue is **assigned**.

##### 2. **In Progress**
- [x] **Merge Request (MR)** is created and linked to the issue.
- [x] **Reviewer(s)** are assigned.
- [x] Code passes **automated checks** (unit&integration testing, linting).

##### 4. **Ready to Deploy**
- [x] MR is **approved** by at least one reviewer.
- [x] All **review comments** are resolved.
- [x] Code is **merged** into target branch (`main`).

##### 5. **User Testing** *(Optional)*
- [x] Feature is deployed to **testing** server.
- [x] Testers/stakeholders are **notified**

#### 6. **Done**
- [x] Feature is deployed to **production** server.
- [x] User testing (if needed) is **approved**.
- [x] Issue is **closed**.

### Git Workflow

#### Base Workflow
We have developed our **custom** workflow due to CI/CD integration issues and features of the development process. Key principles:
- `main` is always deployable.
- Feature branches are created from `main` and merged back via Pull Requests (PRs).
- No long-lived branches except `for_testing`, which serves for deploy to the testing server.

---

#### Rules

##### **1. Issues**
- Use the one of the Issue Templates.
- Include: **Description**, **Labels**, and **Milestone**.
- Assign the most logically suitable *label* from the list of [labels](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/issues/labels) (read their description first).
- Assign the issue to yourself, and contact [PM](https://github.com/PopovDanil) to re-assign if needed.

##### **2. Branching**
- For developing new feature create a new branch.
- There are now strict rules for naming, but each name should logically depict the changes on code (e.g. add response streaming &rarr; response_stream).
- For each merge mention the reason why branches were merged.

##### **3. Commit Messages**
- Template: `<type>(<scope>): <description>`.
- Examples:
```
feat(auth): add login button
fix(api): resolve null pointer in user endpoint
```

##### **4. Pull Requests (PRs) and Reviews**
- Use the [PR Template](/.github/PULL_REQUEST_TEMPLATE/standart.md).
- Target branch - `main`, but for testing `for_testing` can be used.
- Contact [PM](https://github.com/PopovDanil) to assign Reviewers.
- Merge pull request if the code passes **review**, **tests** and **linter** (in other case you will be unable to do it).
- Delete branch after merge.

##### **5. Resolving Issues**
- Close manually only after:
   - [x] PR is merged.
   - [x] Feature is verified in production (if applicable).


#### **Basic workflow example**
```mermaid
flowchart LR
    A[Create Issue] --> B[Create Branch]
    B --> C[Commit & Push]
    C --> D[Open PR]
    D --> E{Code Review}
    E -->|Approved| F[Squash Merge]
    E -->|Rejected| C
    F --> G[Verify in Prod]
    G --> H[Close Issue]

    %% Detailed Annotations
    subgraph "Issue Creation"
    A
    end

    subgraph "Development"
    B
    C
    end

    subgraph "Collaboration"
    D
    E
    end

    subgraph "Release"
    F
    G
    H
    end
```

---

### Secrets management
Contact [DevOps lead](https://github.com/Andrchest) for more information.
All the secrets are stored in `.env` file. Its content will be provided after request to DevOps lead.

## Quality assurance

### Quality attribute scenarios
You can find scenarios in the [docs/quality-assurance/quality-attribute-scenarios.md](./docs/quality-assurance/quality-attribute-scenarios.md)

### Automated tests
We've implemented a comprehensive automated testing suite using the following tools:
- 🐍 [pytest](https://docs.pytest.org/) - Primary test runner and framework
- ⚡ [httpx](https://www.python-httpx.org/) - Async HTTP client for API testing

| Test Type          | Location                      | Description                                                                 | Tools Used          |
|--------------------|-------------------------------|-----------------------------------------------------------------------------|---------------------|
| Unit Tests         | `app/tests/unit/`             | Tests for individual components and utility functions                       | pytest              |
| Integration Tests  | `app/tests/integration/`      | Tests for component interactions and, API and RAG systems integrations      | pytest + httpx      |
| Performance Tests  | `app/tests/performance/`      | *Will be added soon.* Will collect the statistical information of time, speed, and correctness evaluations  | pytest + httpx      |


### User acceptance tests
See [acceptance test](./docs/quality-assurance/user-acceptance-tests.md) for the formal definition of system readiness.


## License

This project is licensed under the [MIT License](LICENSE).