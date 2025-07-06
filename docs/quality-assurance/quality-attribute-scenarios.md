# Quality Attribute Scenarios

## Performance Efficiency

### Time behavior

**Importance to Customer:**
The customer wants the system to work fast, as slow response times would negatively impact user experience and productivity. For a RAG system, quick retrieval and generation are critical for usability.

**Quality Attribute Scenarios:**
1. **Scenario:** System response time for queries
   - **Stimulus:** User submits a query through the web interface **without** files
   - **Source:** End user
   - **Artifact:** Response generation pipeline
   - **Environment:** Normal operation
   - **Response:** System returns answer with citations within 10 seconds
   - **Response Measure:** 95% of queries should complete within 10 seconds
   - **Test Execution:**
     - Use request generating tools (httpx, postman api) for multiple concurrent user simulation
     - Measure time from query submission to full response display
     - Test with various query lengths and complexities

2. **Scenario:** Document ingestion processing time
   - **Stimulus:** User uploads a new document
   - **Source:** End user
   - **Artifact:** Document processing pipeline
   - **Environment:** Normal operation
   - **Response:** Document is processed and available for queries within a 50 seconds
   - **Response Measure:** 90% of documents under 5MB should process within 50 seconds
   - **Test Execution:**
     - Upload sample documents of various sizes and types
     - Measure time from upload request receiving to the appearance of a document in corresponding folder
     - Validate the content of the saved document by comparing with the sample one

## Functional Suitability

### Functional completeness

**Importance to Customer:**
The customer requires comprehensive documents format support (.pdf, .txt, .doc, .docx, .json, .csv) and the ability to directly examine citation sources. This ensures users can work with their existing documents and verify information accuracy through proper source examination.

**Quality Attribute Scenarios:**
1. **Scenario:** Supported documents extensions
   - **Stimulus:** User uploads a document
   - **Source:** End user
   - **Artifact:** Document processing pipeline
   - **Environment:** Normal operation
   - **Response:** System accepts and properly processes the document
   - **Response Measure:** 100% success rate for supported extensions (.pdf, .txt, .doc, .json, .csv, .docx)
   - **Test Execution:**
     - Upload test documents of various extensions from the defined list
     - Validate the content of the saved document by comparing with the sample one

2. **Scenario:** Citation source examination
   - **Stimulus:** User clicks on a citation in the response
   - **Source:** End user
   - **Artifact:** Document viewer system
   - **Environment:** Normal operation
   - **Response:** System opens the source document at the exact citation location
   - **Response Measure:** 100% of citations should link to correct document location
   - **Test Execution:**
     - For each supported file type:
       - Upload sample document
       - Generate queries that produce citations
       - Click each citation link
       - Verify:
         - Correct document opens
         - View is focused on cited section
         - Highlighting/indication of exact citation location is visible (not supported for pdfs)

### Functional correctness

**Importance to Customer:**
The customer wants the system to cite only relevant information. Accurate citations are crucial for the system's credibility and usefulness in research or decision-making scenarios (especially, for *EAP-2*).

**Quality Attribute Scenarios:**
1. **Scenario:** Citation relevance
   - **Stimulus:** User submits a query
   - **Source:** End user
   - **Artifact:** Retrieval component
   - **Environment:** Normal operation
   - **Response:** All provided citations directly support the generated response
   - **Response Measure:** At least 90% of citations should be judged relevant by domain experts
   - **Test Execution:**
     - Prepare a set of test queries with known correct answers or integrate LLM
     - Generate response for each test query and validate (use LLM or domain-experts)
     - Calculate percentage of relevant citations

2. **Scenario:** Answer accuracy
   - **Stimulus:** User submits a factual query
   - **Source:** End user
   - **Artifact:** LLM component
   - **Environment:** Normal operation
   - **Response:** Generated answer matches known correct information
   - **Response Measure:** 95% of factual queries should return correct answers
   - **Test Execution:**
     - Use a validation set of questions with verified answers
     - Compare system output to ground truth (via LLM)
     - Calculate accuracy percentage