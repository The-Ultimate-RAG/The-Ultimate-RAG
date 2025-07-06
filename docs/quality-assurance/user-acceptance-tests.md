## Tests
### 1. Registration test

**Description**: Check if a new user can successfully sign up to save the history of his chats.
**How to test**: The new user should access the registration page (/new_user) manually or via pressing button "+ Add new chat" and enter (valid) credentials.
**Acceptance criteria**:
**GIVEN** an unauthenticated user on the *registration page* **WHEN** the user enters a valid
email (proper format) and password (at least on latter in uppercase, at least one special symbol, at least one digit, at least 8 characters in length), confirms the password (enters the same password) **THEN** registration is successful, the user is redirected to the main (chat) page, and able to communicate.

---

### 2. Response seed test

**Description**: Check if a authorized user can receive an answer to the query with attached document(s) within a minute.
**How to test**: Authorize the user (register a new one, or log in with an existing one), enter any query (at least written in human understandable manner) and attach relevant documents (content of the file should be logically suitable for the query), wait a response.
**Acceptance criteria**:
**GIVEN** the authorized user on the *chat page* **WHEN** the user attaches file (file extension should be in the list .pdf, .doc, .docx, .txt, .json, .csv, .md, file content should suit the query) and asks a
question (in any language, but language of attached files is preferred) **THEN** the user gets a valid response (comprehensive answer for the initial query  with at least one cited file from the attached ones in the language of initial query) within a minute.

---

### 3. Multiple chat creation test

**Description**: Check if the authorized user is able to create multiple chats in one section and the message history is saved.
**How to test**: Authorize the user (register a new one, or log in with an existing one), enter any query (at least written in human understandable manner) and attach relevant documents (content of the file should be logically suitable for the query), wait a response. Click on the button "+ Add new chat". Repeat first instruction. Return to the previous chat.
**Acceptance criteria**:
**GIVEN** the authorized user on the *chat page* **WHEN** the user attaches *any* file and enters *any* query, or just enters *any* query, waits the response, repeats this ones more time in a *new* chat, and returns back to the *any old* chat **THEN** the user is able to see *previously* asked questions and system responses with *clickable* and *valid* citations (after a click the document can be seen by the user).

---

### 4. Response streaming test

**Description**: Check if the authorized user is able to receive an answer from the system chunk by chunk and do not have to wait until the full response is ready.
**How to test**: Authorize the user (register a new one, or log in with an existing one), enter any query (at least written in human understandable manner) and attach relevant documents (content of the file should be logically suitable for the query), hit the "ask" button, and check if the response is sent part by part.
**Acceptance criteria**:
**GIVEN** the authorized user on the *chat page* **WHEN** the user attaches file (file extension should be in the list .pdf, .doc, .docx, .txt, .json, .csv, .md, file content should suit the query) and asks a
question (in any language, but language of attached files is preferred) **THEN** the user can see how a valid response (comprehensive answer for the initial query  with at least one cited file from the attached ones in the language of initial query) is being received part by part (user can already see its parts and start to read the response).

---

### 5. Response language test

**Description**: Check if the authorized user is able to receive an answer from the system in the language, defined by the query. Additionally, checks if the system is able to cite documents written in different languages.
**How to test**: Authorize the user (register a new one, or log in with an existing one), enter any query (in any language, but language of attached files is preferred) and attach relevant documents (content of the file should be logically suitable for the query, can be written in any language), hit the "ask" button, and wait for the response.
**Acceptance criteria**:
**GIVEN** the authorized user on the *chat page* **WHEN** the user attaches file (file extension should be in the list .pdf, .doc, .docx, .txt, .json, .csv, .md, file content should suit the query), written in *any* language and asks a question (in *any* language, but language of attached files is preferred) **THEN** the user can see the generated valid response (comprehensive answer for the initial query with at least one cited file from the attached ones) in the language, defined by the initial query, and click on cited documents, after that the user should be *redirected* to the document viewer with loaded document in the language, defined by the initial file, and see the cited place.

---