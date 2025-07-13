# Changelog

All notable changes to this project will be documented in this file.

## [MVPv2.5] - current version

- Updated README with deployment view
- Added ID for artificial user in tests
- Added more integration tests and proper pytest configuration
- Accelerated file processing


## [MVPv2] - up to 2025-07-07

- Significantly reduced response time
- Enhanced response quality and accuracy
- Enhanced UI/UX
- Enhanced security: confidential information now stored in .env, single .py file
- Implemented unit and integration tests
- Introduced CI/CD pipeline
- Implemented response streaming (The response provided to the user when generating chunks)
- The information now accompanies a link where it was found
- Added JSON, CSV, and MD file types support
- Added a draft version of user and chat separation
- Addressed message saving bug
- Corrected prompt to align with task requirements
- Updated README and documentation


## [MVPv1] - up to 2025-06-23

- Established a ready-to-use RAG skeleton\
  *(The core function allows you to attach files and ask questions about their contents. You will receive a response that includes the information, the file name, the page number, and the exact location where the information is found.)*
- Multilingual support was added
- Added TXT, DOC, DOCX, and PDF file types support
- Implemented API with a simple frontend
- Added user registration and draft authentication backend logic
- Improved README and added License
