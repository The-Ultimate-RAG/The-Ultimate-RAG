### Continuous Integration

Our Continuous Integration (CI) pipeline ensures code quality by running automated checks on every pull request to the
`main` branch. The pipeline is managed using GitHub Actions and is defined in:

- [
  `.github/workflows/unit-tests.yml`](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/blob/main/.github/workflows/unit-tests.yml)

In the CI pipeline, we use the following tools:

- **Static Analysis Tools:**
    - **flake8**: A linter for Python that enforces coding style and detects programming errors.
    - **bandit**: A security vulnerability scanner for Python, identifying potential security issues in the codebase.

- **Testing Tools:**
    - **pytest**: A testing framework for Python, used to run unit tests located in [
      `app/tests/unit`](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/tree/main/app/tests/unit).

If any checks fail, the pull request cannot be merged into `main`. All CI workflow runs can be viewed at:

- [GitHub Actions - CI Workflow Runs](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/actions/workflows/unit-tests.yml)