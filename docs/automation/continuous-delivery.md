### Continuous Deployment

Our Continuous Deployment (CD) pipeline automatically deploys the application after a successful merge into `main`. The
pipeline is defined in:

- [
  `.github/workflows/sync-to-hf.yml`](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/blob/main/.github/workflows/sync-to-hf.yml)

The CD pipeline performs the following steps:

1. Pushes the updated code to a **Hugging Face Space** (test environment) using `git`, where it is automatically
   deployed.
2. Runs **integration tests** on the test server with a test PostgreSQL database (hosted on a separate service), using
   tests located in [
   `app/tests/integration`](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/tree/main/app/tests/integration).
3. If integration tests pass, deploys to a separate **Hugging Face Space** (production environment) with a production
   PostgreSQL database (also hosted on a separate service). Deployment takes approximately 2–3 minutes.
4. If any tests fail, the production server remains unaffected.

In the CD pipeline, we use the following tools:

- **Deployment Tools:**
    - **Docker**: Builds and packages the application as a container.
    - **git**: Pushes the application to Hugging Face Spaces for deployment.
- **Testing Tools:**
    - **pytest**: Runs integration tests on the test server.

All CD workflow runs can be viewed at:

- [GitHub Actions - CD Workflow Runs](https://github.com/The-Ultimate-RAG/The-Ultimate-RAG/actions/workflows/sync-to-hf.yml)