### Automated tests

We've implemented a comprehensive automated testing suite using the following tools:

- 🐍 [pytest](https://docs.pytest.org/) - Primary test runner and framework
- ⚡ [httpx](https://www.python-httpx.org/) - Async HTTP client for API testing

| Test Type         | Location                 | Description                                                                                                | Tools Used     |
|-------------------|--------------------------|------------------------------------------------------------------------------------------------------------|----------------|
| Unit Tests        | `app/tests/unit/`        | Tests for individual components and utility functions                                                      | pytest         |
| Integration Tests | `app/tests/integration/` | Tests for component interactions and, API and RAG systems integrations                                     | pytest + httpx |
| Performance Tests | `app/tests/performance/` | *Will be added soon.* Will collect the statistical information of time, speed, and correctness evaluations | pytest + httpx |
