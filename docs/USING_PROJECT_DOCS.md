# Using Project Documentation with LLMs

This guide explains how to effectively use the project documentation system to maintain context and improve collaboration with LLMs during development.

## Core Documentation Files

### PROJECT_CONTEXT.md
**Purpose**: Provides high-level context about the project to bring an LLM up to speed quickly.

**When to use**: Include at the beginning of a new conversation with an LLM to establish context.

**How to use**:
1. Keep this file updated with the latest project status
2. Include it as the first document when starting a new conversation
3. Update the "Last Updated" date whenever you make changes

### TESTING_ROADMAP.md
**Purpose**: Tracks the testing strategy, current coverage, and future testing priorities.

**When to use**: Include when discussing testing or requesting implementation of tests.

**How to use**:
1. Update test statuses as tests are implemented
2. Check off test cases as they are completed
3. Add new test requirements as features are added

### DEVELOPMENT_ROADMAP.md
**Purpose**: Outlines planned development tasks and priorities.

**When to use**: Include when discussing future work, planning new features, or prioritizing tasks.

**How to use**:
1. Keep priorities updated based on project needs
2. Check off completed items
3. Add new items as requirements evolve

### LLM_CHALLENGES.md
**Purpose**: Documents challenges and effective strategies when working with LLMs.

**When to use**: Reference when encountering issues with LLM-generated code or when planning complex features.

**How to use**:
1. Add new challenges and strategies as they are discovered
2. Review before implementing complex features
3. Use as a reference for effective prompting techniques

## Request Templates

The `templates` directory contains structured formats for different types of requests to LLMs:

### FEATURE_REQUEST.md
**Purpose**: Template for requesting new feature implementation.

**How to use**:
1. Copy the template to a new document or directly into your LLM prompt
2. Fill in all relevant sections
3. Be specific about requirements and acceptance criteria
4. Include examples and edge cases

### BUG_REPORT.md
**Purpose**: Template for reporting and requesting fixes for bugs.

**How to use**:
1. Include detailed reproduction steps
2. Be specific about expected vs. actual behavior
3. Include error messages and context
4. Link to relevant files and code

### CODE_REVIEW.md
**Purpose**: Template for requesting code review.

**How to use**:
1. List specific files and sections to review
2. Highlight areas of concern
3. Ask specific questions to guide the review
4. Include the checklist to ensure comprehensive review

### TEST_IMPLEMENTATION.md
**Purpose**: Template for requesting test implementation.

**How to use**:
1. Specify which functions or components need testing
2. List edge cases and error conditions
3. Define coverage goals
4. Include example test cases

## Best Practices for LLM Interaction

### Starting a New Session
When starting a fresh conversation with an LLM, include:

1. **PROJECT_CONTEXT.md** content
2. Relevant section from **DEVELOPMENT_ROADMAP.md**
3. Brief description of the current task

Example prompt:
```
I'm working on the SteamSeek project. Here's the current project context:

[Copy PROJECT_CONTEXT.md content here]

Today I'd like to work on the following task from our roadmap:

[Copy relevant section from DEVELOPMENT_ROADMAP.md]

Specifically, I need help with [specific task description].
```

### Submitting a Feature Request
1. Copy the FEATURE_REQUEST.md template
2. Fill in all relevant sections
3. Include any specific code patterns or conventions to follow

### Reporting a Bug
1. Copy the BUG_REPORT.md template
2. Fill in detailed reproduction steps
3. Include error messages and context

### Requesting Code Review
1. Copy the CODE_REVIEW.md template
2. List specific files and areas of concern
3. Ask specific questions to guide the review

### Requesting Tests
1. Copy the TEST_IMPLEMENTATION.md template
2. Specify what needs to be tested and expected coverage
3. Include examples of edge cases

## Maintaining Documentation

Keep the documentation system effective by:

1. **Regular updates**: Update status and progress at least weekly
2. **Contextual additions**: Add new challenges or strategies as they emerge
3. **Template refinement**: Improve templates based on what works best
4. **Cross-referencing**: Link between documents to maintain connections
5. **Date tracking**: Always update the "Last Updated" date at the bottom of each document

Remember: The quality of the output from LLMs directly correlates with the quality of your input. Well-structured, detailed prompts with proper context will yield better results.

---

*Last Updated: [Date]* 