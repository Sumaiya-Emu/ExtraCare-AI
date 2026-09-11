# Final Project Submission Brief

---

## Project Type: Real-World AI Agent / Chatbot Application

## Submission Deadline

**7 September, 11:59 PM**

---

# 1. Project Overview

For the final project, students are required to design and implement a **real-world AI-powered application** that solves a meaningful practical problem.

The goal is not simply to build a chatbot that answers questions. Your application should address a **specific real-life use case** where AI, agents, tools, retrieval, or external data can meaningfully help a user complete a task, make a decision, find information, or automate a workflow.

Possible domains include:

- Education
- Healthcare
- Finance
- E-commerce
- Career and recruitment
- Travel
- Agriculture
- Research
- Productivity
- Customer support
- Business automation
- Legal/document assistance
- Personal knowledge management
- Any other meaningful real-world problem

Students are encouraged to be creative with the problem they choose.

> **Important:** A simple general-purpose chatbot or basic ChatGPT clone will **not** be considered sufficient. The project should demonstrate a clear use case, meaningful AI workflow, and integration of multiple concepts learned throughout the course.

---

# 2. Reference Projects from Previous Batch

Three projects from the previous batch will be provided as references.

These references are intended to help students understand:

- The expected project scope
- The expected technical depth
- The quality of implementation
- How different AI components can be combined
- How to present the final application
- The expected level of code organization and explanation

### Reference Project 1

**Project:** [Adhikar AI (অধিকার) — Bangladesh Legal Advocate](https://www.youtube.com/watch?v=vLJ2aemobqA)

### Reference Project 2

**Project:** [AILITRIV: AI-Powered Academic Research Assistant](https://www.youtube.com/watch?v=ucK6pZ9THSw)

### Reference Project 3

**Project:** [FraudGuard AI – Multi-Agent Fraud Detection Chatbot](https://www.youtube.com/watch?v=JRDcEgmWeT8)

---

These projects should be used only as **quality and complexity references**.

Students are expected to build their **own original project and implementation**.

---

# 3. Project Requirements

## 3.1 Real-World Problem

Your project must begin with a clearly defined real-world problem.

You should be able to explain:

- Who the target user is
- What problem the user currently faces
- How your system solves or reduces that problem
- Why AI is useful for this particular use case

The project should have a clear purpose beyond simply demonstrating an LLM.

---

## 3.2 Front-End Application

The project must include a usable interface where users can interact with the system.

You may use:

- React
- Next.js
- JavaScript
- Streamlit
- Gradio
- Flutter
- Any other suitable framework

The interface should be functional and appropriate for your project's use case.

UI design does not need to be extremely sophisticated, but the complete user journey should be easy to understand and demonstrate.

---

## 3.3 Back-End

The project should contain a properly structured backend responsible for handling the AI workflow.

You may use frameworks such as:

- FastAPI
- Flask
- Django
- Node.js
- Next.js backend
- Streamlit backend
- Any other appropriate technology

Students should maintain proper separation between important components such as:

- API / application logic
- Agents
- Tools
- Prompts
- Retrieval
- Database
- Configuration
- Front-end

---

# 4. AI and Agent Requirements

Your application must demonstrate meaningful use of modern AI concepts.

Depending on your problem, you may use one or multiple agents.

Examples include:

- Research Agent
- Recommendation Agent
- Search Agent
- Document Analysis Agent
- Planning Agent
- Evaluation Agent
- Data Analysis Agent
- Customer Support Agent
- Supervisor / Router Agent
- Specialized domain agents

Using multiple agents is encouraged when it makes sense for the application.

However, **do not create unnecessary agents only to increase the agent count**.

Each agent should have a clear responsibility.

---

# 5. Tool Integration

Your application should integrate multiple tools or capabilities where appropriate.

The following concepts should be demonstrated across the project:

### Internet Search

The application should be capable of retrieving relevant information from the internet when the use case requires current or external information.

---

### Google Search Grounding

Students should demonstrate grounding with Google Search or another appropriate search-grounding mechanism.

The model should use retrieved information rather than relying entirely on its internal knowledge.

---

### OCR

The application should support extracting information from images or scanned documents using OCR where appropriate.

Example use cases:

- Bills
- Receipts
- Documents
- Certificates
- Notes
- Forms
- Product images
- Screenshots

OCR does not have to be the main feature of the project, but it should be meaningfully integrated into the overall workflow.

---

### RAG – Retrieval Augmented Generation

The project must contain a retrieval-based functionality.

Students may create a knowledge base from:

- PDFs
- Documents
- Websites
- Articles
- Product information
- Policies
- Research papers
- User-provided documents
- Domain-specific datasets

The application should retrieve relevant information before generating responses.

---

# 6. Vector Database

A vector database must be used for semantic search or RAG.

Students may use:

- FAISS
- Chroma
- Pinecone
- Weaviate
- Qdrant
- Supabase Vector
- Any other suitable vector database

Students should understand and be able to explain:

- What data is stored
- How documents are chunked
- How embeddings are generated
- How retrieval works
- How retrieved information is passed to the LLM

---

# 7. LangSmith Integration

The backend must be integrated with **LangSmith** for tracing and monitoring.

Important executions should be visible through LangSmith, including where applicable:

- User query
- Agent execution
- LLM calls
- Tool calls
- Retrieval
- Chains
- Agent transitions
- Final response generation

Students should be able to open a LangSmith trace and explain the complete execution flow of their system.

---

# 8. Expected Project Complexity

Your project should contain a complete workflow rather than one isolated AI feature.

A good project may look like:

**User Input → Intent / Router → Agent → Tool / Search / RAG → Processing → Final Response**

or

**User Upload → OCR → Information Extraction → Retrieval / Search → AI Analysis → Recommendation**

or

**User Request → Planner → Multiple Specialized Agents → Result Aggregation → Final Answer**

The exact architecture depends on your project.

There is **no requirement to copy these architectures exactly**.

The architecture should make sense for the problem you are solving.

---

# 9. Evaluation Criteria

Projects will be evaluated based on the following areas.

## 9.1 Problem & Use Case

- Is the problem meaningful and realistic?
- Is the target user clearly defined?
- Does the AI solution provide useful value?

---

## 9.2 Functionality

- Does the application work?
- Can the user complete the intended workflow?
- Are the implemented features connected properly?
- Are AI responses useful and relevant?

---

## 9.3 AI Implementation

Evaluation will consider the proper implementation of:

- Agents
- Tools
- RAG
- Vector database
- Search / grounding
- OCR
- LLM interactions

The quality of integration is more important than simply having many features.

---

## 9.4 Code Quality

The project should demonstrate good software engineering practices.

This includes:

- Clean code
- Meaningful function and variable names
- Proper folder structure
- Modular implementation
- Environment variables for secrets
- Documentation
- Reusable components
- Proper error handling

---

## 9.5 LangSmith Tracing

Students should demonstrate that important parts of the AI workflow can be inspected through LangSmith.

---

## 9.6 Project Presentation

Students should be able to clearly explain:

- The problem
- Their solution
- Architecture
- AI workflow
- Tools
- Codebase
- Technical decisions

Understanding your own implementation is an important part of the evaluation.

---

# 10. Submission Components

Students must submit the following components.

---

## 10.1 YouTube Video Presentation

Students must submit a YouTube video explaining and demonstrating the project.

### Language

The presentation must be in **English**.

### Video Length

There is **no strict time limit**.

The priority is to clearly demonstrate and explain the project.

The presentation should contain two major parts.

---

## Part 1 – Project Demonstration

First, demonstrate the application from the user's perspective.

Show the complete workflow of your main implemented features.

For example:

- Explain the problem
- Introduce the target user
- Demonstrate the application
- Enter realistic user queries
- Upload documents/images if supported
- Demonstrate search or retrieval
- Demonstrate agent/tool execution
- Show the final result
- Explain why the output is useful

Your demo should focus primarily on features that are **actually working**.

You may also briefly mention additional work-in-progress features or future improvements.

---

## Part 2 – Codebase & Architecture Explanation

After the demonstration, explain the technical implementation.

Your explanation should cover:

- Project architecture
- Folder structure
- Front-end
- Back-end
- LLM configuration
- Prompt design
- Agent implementation
- Agent workflow
- Tool implementation
- Internet search
- OCR
- RAG pipeline
- Embeddings
- Vector database
- Important functions
- LangSmith integration
- Environment/configuration setup

Walk through the important parts of the code and explain **how the system works**.

Simply showing code without explaining it is not sufficient.

---

# 11. GitHub Repository

Students must submit a GitHub repository containing the complete project.

The repository should include:

- Complete source code
- Proper project structure
- `README.md`
- `requirements.txt`, `pyproject.toml`, `package.json`, or equivalent dependency file
- Setup instructions
- Instructions for running the project
- Description of the project
- Architecture/workflow explanation
- Required environment variables
- Screenshots where appropriate

### Important

Do **not** upload API keys, tokens, passwords, or other credentials to GitHub.

Use `.env` files and include `.env` in `.gitignore`.

You may provide a `.env.example` showing which environment variables are required.

---

# 12. LangSmith Trace Submission

Students must also submit LangSmith trace links that demonstrate the execution of the application.

The submitted traces should clearly demonstrate important parts of the system, such as:

- Agent execution
- Tool calls
- RAG / retrieval
- Search
- LLM execution
- Agent workflow

Choose traces that represent the **main functionality of your project**.

---

# 13. Final Submission Checklist

Before submitting, make sure you have:

- [ ]  Built a real-world AI application
- [ ]  Clearly defined the problem and target user
- [ ]  Implemented a working front-end
- [ ]  Implemented a structured back-end
- [ ]  Integrated agents appropriately
- [ ]  Integrated external tools
- [ ]  Implemented Internet Search
- [ ]  Implemented search grounding
- [ ]  Implemented OCR
- [ ]  Implemented RAG
- [ ]  Used a vector database
- [ ]  Integrated LangSmith tracing
- [ ]  Uploaded the complete project to GitHub
- [ ]  Added a proper README
- [ ]  Recorded the English YouTube presentation
- [ ]  Demonstrated the working application
- [ ]  Explained the codebase
- [ ]  Submitted relevant LangSmith traces

---

# 14. Academic Integrity

All submitted projects must represent the student's own understanding and implementation.

Students are allowed and encouraged to use:

- AI assistants
- Open-source libraries
- Documentation
- Tutorials
- Frameworks
- Existing APIs

However, students must understand the code and system they submit.

During evaluation, students may be asked to explain:

- Their architecture
- Individual functions
- Agent decisions
- Prompt design
- RAG implementation
- Tool integrations
- Technical choices

Submitting a project that the student cannot explain may affect the evaluation.

Projects copied directly from another student, repository, tutorial, or previous batch submission are not acceptable.

---

# 15. Submission Deadline

## **7 September, 11:59 PM**

Please make sure that all required links and materials are submitted before the deadline.

Late submissions may be subject to penalties according to course policy.

---

## Final Note

The goal of this project is not to build the largest system or use the highest number of AI tools.

The goal is to identify a **real problem** and build a thoughtful AI application that solves that problem through a well-designed workflow.

Focus on:

**Problem → User → Workflow → AI → Useful Outcome**

Build something that you would be confident showing as a real project in your portfolio.

**Best of luck with your final project.**