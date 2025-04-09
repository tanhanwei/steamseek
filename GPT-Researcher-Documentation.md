# Introduction

[![Official Website](https://img.shields.io/badge/Official%20Website-gptr.dev-teal?style=for-the-badge&logo=world&logoColor=white)](https://gptr.dev)
[![Discord Follow](https://dcbadge.vercel.app/api/server/QgZXvJAccX?style=for-the-badge&theme=clean-inverted)](https://discord.gg/QgZXvJAccX)

[![GitHub Repo stars](https://img.shields.io/github/stars/assafelovic/gpt-researcher?style=social)](https://github.com/assafelovic/gpt-researcher)
[![Twitter Follow](https://img.shields.io/twitter/follow/assaf_elovic?style=social)](https://twitter.com/assaf_elovic)
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)

**[GPT Researcher](https://gptr.dev) is an autonomous agent designed for comprehensive online research on a variety of tasks.** 

The agent can produce detailed, factual and unbiased research reports, with customization options for focusing on relevant resources, outlines, and lessons. Inspired by the recent [Plan-and-Solve](https://arxiv.org/abs/2305.04091) and [RAG](https://arxiv.org/abs/2005.11401) papers, GPT Researcher addresses issues of speed, determinism and reliability, offering a more stable performance and increased speed through parallelized agent work, as opposed to synchronous operations.

## Why GPT Researcher?

- To form objective conclusions for manual research tasks can take time, sometimes weeks to find the right resources and information.
- Current LLMs are trained on past and outdated information, with heavy risks of hallucinations, making them almost irrelevant for research tasks.
- Current LLMs are limited to short token outputs which are not sufficient for long detailed research reports (2k+ words).
- Solutions that enable web search (such as ChatGPT + Web Plugin), only consider limited resources and content that in some cases result in superficial conclusions or biased answers.
- Using only a selection of resources can create bias in determining the right conclusions for research questions or tasks. 

## Architecture
The main idea is to run "planner" and "execution" agents, whereas the planner generates questions to research, and the execution agents seek the most related information based on each generated research question. Finally, the planner filters and aggregates all related information and creates a research report. <br /> <br /> 
The agents leverage both gpt-4o-mini and gpt-4o (128K context) to complete a research task. We optimize for costs using each only when necessary. **The average research task takes around 3 minutes to complete, and costs ~$0.1.**

<div align="center">
<img align="center" height="600" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/4ac896fd-63ab-4b77-9688-ff62aafcc527" />
</div>


More specifically:
* Create a domain specific agent based on research query or task.
* Generate a set of research questions that together form an objective opinion on any given task. 
* For each research question, trigger a crawler agent that scrapes online resources for information relevant to the given task.
* For each scraped resources, summarize based on relevant information and keep track of its sources.
* Finally, filter and aggregate all summarized sources and generate a final research report.

## Demo
<iframe height="400" width="700" src="https://github.com/assafelovic/gpt-researcher/assets/13554167/a00c89a6-a295-4dd0-b58d-098a31c40fda" frameborder="0" allow="autoplay; encrypted-media" allowfullscreen></iframe>

## Tutorials
 - [Video Tutorial Series](https://www.youtube.com/playlist?list=PLUGOUZPIB0F-qv6MvKq3HGr0M_b3U2ATv)
 - [How it Works](https://medium.com/better-programming/how-i-built-an-autonomous-ai-agent-for-online-research-93435a97c6c)
 - [How to Install](https://www.loom.com/share/04ebffb6ed2a4520a27c3e3addcdde20?sid=da1848e8-b1f1-42d1-93c3-5b0b9c3b24ea)
 - [Live Demo](https://www.loom.com/share/6a3385db4e8747a1913dd85a7834846f?sid=a740fd5b-2aa3-457e-8fb7-86976f59f9b8)
 - [Homepage](https://gptr.dev)

## Features
- 📝 Generate research, outlines, resources and lessons reports
- 📜 Can generate long and detailed research reports (over 2K words)
- 🌐 Aggregates over 20 web sources per research to form objective and factual conclusions
- 🖥️ Includes an easy-to-use web interface (HTML/CSS/JS)
- 🔍 Scrapes web sources with javascript support
- 📂 Keeps track and context of visited and used web sources
- 📄 Export research reports to PDF, Word and more...

Let's get started [here](/docs/gpt-researcher/getting-started/getting-started)!


# How to Choose

GPT Researcher is a powerful autonomous research agent designed to enhance and streamline your research processes. Whether you're a developer looking to integrate research capabilities into your project or an end-user seeking a comprehensive research solution, GPT Researcher offers flexible options to meet your needs.

We envision a future where AI agents collaborate to complete complex tasks, with research being a critical step in the process. GPT Researcher aims to be your go-to agent for any research task, regardless of complexity. It can be easily integrated into existing agent workflows, eliminating the need to create your own research agent from scratch.

## Options

GPT Researcher offers multiple ways to leverage its capabilities:

<img src="https://github.com/user-attachments/assets/305fa3b9-60fa-42b6-a4b0-84740ab6c665" alt="Logo" width="568"></img>
<br></br>

1. **GPT Researcher PIP agent**: Ideal for integrating GPT Researcher into your existing projects and workflows.
2. **Backend**: A backend service to interact with the frontend user interfaces, offering advanced features like detailed reports.
3. **Multi Agent System**: An advanced setup using LangGraph, offering the most comprehensive research capabilities.
4. **Frontend**: Several front-end solutions depending on your needs, including a simple HTML/JS version and a more advanced NextJS version.

## Usage Options

### 1. PIP Package

The PIP package is ideal for leveraging GPT Researcher as an agent in your preferred environment and code.

**Pros:**
- Easy integration into existing projects
- Flexible usage in multi-agent systems, chains, or workflows
- Optimized for production performance

**Cons:**
- Requires some coding knowledge
- May need additional setup for advanced features

**Installation:**
```
pip install gpt-researcher
```

**System Requirements:**
- Python 3.10+
- pip package manager

**Learn More:** [PIP Documentation](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

### 2. End-to-End Application

For a complete out-of-the-box experience, including a sleek frontend, you can clone our repository.

**Pros:**
- Ready-to-use frontend and backend services
- Includes advanced use cases like detailed report generation
- Optimal user experience

**Cons:**
- Less flexible than the PIP package for custom integrations
- Requires setting up the entire application

**Getting Started:**
1. Clone the repository: `git clone https://github.com/assafelovic/gpt-researcher.git`
2. Follow the [installation instructions](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started)

**System Requirements:**
- Git
- Python 3.10+
- Node.js and npm (for frontend)

**Advanced Usage Example:** [Detailed Report Implementation](https://github.com/assafelovic/gpt-researcher/tree/master/backend/report_type/detailed_report)

### 3. Multi Agent System with LangGraph

We've collaborated with LangChain to support multi-agents with LangGraph and GPT Researcher, offering the most complex and comprehensive version of GPT Researcher.

**Pros:**
- Very detailed, customized research reports
- Inner AI agent loops and reasoning

**Cons:**
- More expensive and time-consuming
- Heavyweight for production use

This version is recommended for local, experimental, and educational use. We're working on providing a lighter version soon!

**System Requirements:**
- Python 3.10+
- LangGraph library

**Learn More:** [GPT Researcher x LangGraph](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)

## Comparison Table

| Feature | PIP Package | End-to-End Application | Multi Agent System |
|---------|-------------|------------------------|---------------------|
| Ease of Integration | High | Medium | Low |
| Customization | High | Medium | High |
| Out-of-the-box UI | No | Yes | No |
| Complexity | Low | Medium | High |
| Best for | Developers | End-users | Researchers/Experimenters |

Please note that all options have been optimized and refined for production use.

## Deep Dive

To learn more about each of the options, check out these docs and code snippets:

1. **PIP Package**: 
   - Install: `pip install gpt-researcher`
   - [Integration guide](https://docs.gptr.dev/docs/gpt-researcher/gptr/pip-package)

2. **End-to-End Application**: 
   - Clone the repository: `git clone https://github.com/assafelovic/gpt-researcher.git`
   - [Installation instructions](https://docs.gptr.dev/docs/gpt-researcher/getting-started/getting-started)

3. **Multi-Agent System**: 
   - [Multi-Agents code](https://github.com/assafelovic/gpt-researcher/tree/master/multi_agents)
   - [LangGraph documentation](https://docs.gptr.dev/docs/gpt-researcher/multi_agents/langgraph)
   - [Blog](https://docs.gptr.dev/blog/gptr-langgraph)

## Versioning and Updates

GPT Researcher is actively maintained and updated. To ensure you're using the latest version:

- For the PIP package: `pip install --upgrade gpt-researcher`
- For the End-to-End Application: Pull the latest changes from the GitHub repository
- For the Multi-Agent System: Check the documentation for compatibility with the latest LangChain and LangGraph versions

## Troubleshooting and FAQs

For common issues and questions, please refer to our [FAQ section](https://docs.gptr.dev/docs/faq) in the documentation.

# Deep Research ✨ NEW ✨

With the latest "Deep Research" trend in the AI community, we're excited to implement our own Open source deep research capability! Introducing GPT Researcher's Deep Research - an advanced recursive research system that explores topics with unprecedented depth and breadth. 

Each deep research takes around 5 minutes to complete and costs around $0.4 (using `o3-mini` on `"high" `reasoning effort)

## How It Works

Deep Research employs a fascinating tree-like exploration pattern:

1. **Breadth**: At each level, it generates multiple search queries to explore different aspects of your topic
2. **Depth**: For each branch, it recursively dives deeper, following leads and uncovering connections
3. **Concurrent Processing**: Utilizes async/await patterns to run multiple research paths simultaneously
4. **Smart Context Management**: Automatically aggregates and synthesizes findings across all branches
5. **Progress Tracking**: Real-time updates on research progress across both breadth and depth dimensions

Think of it as deploying a team of AI researchers, each following their own research path while collaborating to build a comprehensive understanding of your topic.

## Process Flow
<img src="https://github.com/user-attachments/assets/eba2d94b-bef3-4f8d-bbc0-f15bd0a40968" alt="Logo" width="568"></img>
<br></br>

## Quick Start

```python
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone
import asyncio

async def main():
    # Initialize researcher with deep research type
    researcher = GPTResearcher(
        query="What are the latest developments in quantum computing?",
        report_type="deep",  # This triggers deep research modd
    )
    
    # Run research
    research_data = await researcher.conduct_research()
    
    # Generate report
    report = await researcher.write_report()
    print(report)

if __name__ == "__main__":
    asyncio.run(main())
```

## Configuration

Deep Research behavior can be customized through several parameters:

- `deep_research_breadth`: Number of parallel research paths at each level (default: 4)
- `deep_research_depth`: How many levels deep to explore (default: 2)
- `deep_research_concurrency`: Maximum number of concurrent research operations (default: 4)
- `total_words`: Total words in the generated report (recommended: 2000)

You can configure these parameters in multiple ways:

1. **Environment Variables**:
```bash
export DEEP_RESEARCH_BREADTH=4
export DEEP_RESEARCH_DEPTH=2
export DEEP_RESEARCH_CONCURRENCY=4
export TOTAL_WORDS=2500
```

2. **Config File**:
```yaml
deep_research_breadth: 4
deep_research_depth: 2
deep_research_concurrency: 4
total_words: 2500
```

```python
researcher = GPTResearcher(
    query="your query",
    report_type="deep",
    config_path="path/to/config.yaml"  # Configure deep research parameters here
)
```

## Progress Tracking

The `on_progress` callback provides real-time insights into the research process:

```python
class ResearchProgress:
    current_depth: int       # Current depth level
    total_depth: int         # Maximum depth to explore
    current_breadth: int     # Current number of parallel paths
    total_breadth: int       # Maximum breadth at each level
    current_query: str       # Currently processing query
    completed_queries: int   # Number of completed queries
    total_queries: int       # Total queries to process
```

## Error Handling

The deep research workflow is designed to be resilient:

- Failed queries are automatically skipped
- Research continues even if some branches fail
- Progress tracking helps identify any issues

## Best Practices

1. **Start Broad**: Begin with a general query and let the system explore specifics
2. **Monitor Progress**: Use the progress callback to understand the research flow
3. **Adjust Parameters**: Tune breadth and depth based on your needs:
   - More breadth = wider coverage
   - More depth = deeper insights
4. **Resource Management**: Consider concurrency limits based on your system capabilities

## Limitations

- Usage of reasoning LLM models such as `o3-mini`
- Deep research may take longer than standard research
- Higher API usage and costs due to multiple concurrent queries
- May require more system resources for parallel processing

Happy researching! 🎉 

# Agent Example

If you're interested in using GPT Researcher as a standalone agent, you can easily import it into any existing Python project. Below, is an example of calling the agent to generate a research report:

```python
from gpt_researcher import GPTResearcher
import asyncio

async def fetch_report(query):
    """
    Fetch a research report based on the provided query and report type.
    """
    researcher = GPTResearcher(query=query)
    await researcher.conduct_research()
    report = await researcher.write_report()
    return report

async def generate_research_report(query):
    """
    This is a sample script that executes an async main function to run a research report.
    """
    report = await fetch_report(query)
    print(report)

if __name__ == "__main__":
    QUERY = "What happened in the latest burning man floods?"
    asyncio.run(generate_research_report(query=QUERY))
```

You can further enhance this example to use the returned report as context for generating valuable content such as news article, marketing content, email templates, newsletters, etc.

You can also use GPT Researcher to gather information about code documentation, business analysis, financial information and more. All of which can be used to complete much more complex tasks that require factual and high quality realtime information.

---
# PIP Package
[![PyPI version](https://badge.fury.io/py/gpt-researcher.svg)](https://badge.fury.io/py/gpt-researcher)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/assafelovic/gpt-researcher/blob/master/docs/docs/examples/pip-run.ipynb)

🌟 **Exciting News!** Now, you can integrate `gpt-researcher` with your apps seamlessly!

## Steps to Install GPT Researcher

Follow these easy steps to get started:

0. **Pre-requisite**: Ensure Python 3.10+ is installed on your machine 💻
1. **Install gpt-researcher**: Grab the official package from [PyPi](https://pypi.org/project/gpt-researcher/).

```bash
pip install gpt-researcher
```

2. **Environment Variables:** Create a .env file with your OpenAI API key or simply export it

```bash
export OPENAI_API_KEY={Your OpenAI API Key here}
```

```bash
export TAVILY_API_KEY={Your Tavily API Key here}
```

3. **Start using GPT Researcher in your own codebase**

## Example Usage

```python
from gpt_researcher import GPTResearcher
import asyncio

async def get_report(query: str, report_type: str):
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    # Get additional information
    research_context = researcher.get_research_context()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return report, research_context, research_costs, research_images, research_sources

if __name__ == "__main__":
    query = "what team may win the NBA finals?"
    report_type = "research_report"

    report, context, costs, images, sources = asyncio.run(get_report(query, report_type))
    
    print("Report:")
    print(report)
    print("\nResearch Costs:")
    print(costs)
    print("\nNumber of Research Images:")
    print(len(images))
    print("\nNumber of Research Sources:")
    print(len(sources))
```

## Specific Examples

### Example 1: Research Report

```python
query = "Latest developments in renewable energy technologies"
report_type = "research_report"
```

### Example 2: Resource Report

```python
query = "List of top AI conferences in 2023"
report_type = "resource_report"
```

### Example 3: Outline Report

```python
query = "Outline for an article on the impact of AI in education"
report_type = "outline_report"
```

## Integration with Web Frameworks

### FastAPI Example

```python
from fastapi import FastAPI
from gpt_researcher import GPTResearcher
import asyncio

app = FastAPI()

@app.get("/report/{report_type}")
async def get_report(query: str, report_type: str) -> dict:
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    source_urls = researcher.get_source_urls()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return {
        "report": report,
        "source_urls": source_urls,
        "research_costs": research_costs,
        "num_images": len(research_images),
        "num_sources": len(research_sources)
    }

# Run the server
# uvicorn main:app --reload
```

### Flask Example

**Pre-requisite**: Install flask with the async extra.

```bash
pip install 'flask[async]'
```

```python
from flask import Flask, request, jsonify
from gpt_researcher import GPTResearcher

app = Flask(__name__)

@app.route('/report/<report_type>', methods=['GET'])
async def get_report(report_type):
    query = request.args.get('query')
    researcher = GPTResearcher(query, report_type)
    research_result = await researcher.conduct_research()
    report = await researcher.write_report()
    
    source_urls = researcher.get_source_urls()
    research_costs = researcher.get_costs()
    research_images = researcher.get_research_images()
    research_sources = researcher.get_research_sources()
    
    return jsonify({
        "report": report,
        "source_urls": source_urls,
        "research_costs": research_costs,
        "num_images": len(research_images),
        "num_sources": len(research_sources)
    })

# Run the server
# flask run
```

**Run the server**

```bash
flask run
```

**Example Request**

```bash
curl -X GET "http://localhost:5000/report/research_report?query=what team may win the nba finals?"
```

## Getters and Setters
GPT Researcher provides several methods to retrieve additional information about the research process:

### Get Research Sources
Sources are the URLs that were used to gather information for the research.
```python
source_urls = researcher.get_source_urls()
```

### Get Research Context
Context is all the retrieved information from the research. It includes the sources and their corresponding content.
```python
research_context = researcher.get_research_context()
```

### Get Research Costs
Costs are the number of tokens consumed during the research process.
```python
research_costs = researcher.get_costs()
```

### Get Research Images
Retrieves a list of images found during the research process.
```python
research_images = researcher.get_research_images()
```

### Get Research Sources
Retrieves a list of research sources, including title, content, and images.
```python
research_sources = researcher.get_research_sources()
```

### Set Verbose
You can set the verbose mode to get more detailed logs.
```python
researcher.set_verbose(True)
```

### Add Costs
You can also add costs to the research process if you want to track the costs from external usage.
```python
researcher.add_costs(0.22)
```

## Advanced Usage

### Customizing the Research Process

You can customize various aspects of the research process by passing additional parameters when initializing the GPTResearcher:

```python
researcher = GPTResearcher(
    query="Your research query",
    report_type="research_report",
    report_format="APA",
    tone="formal and objective",
    max_subtopics=5,
    verbose=True
)
```

### Handling Research Results

After conducting research, you can process the results in various ways:

```python
# Conduct research
research_result = await researcher.conduct_research()

# Generate a standard report
report = await researcher.write_report()

# Generate a customized report with specific formatting requirements
custom_report = await researcher.write_report(custom_prompt="Answer in short, 2 paragraphs max without citations.")

# Generate a focused report for a specific audience
executive_summary = await researcher.write_report(custom_prompt="Create an executive summary focused on business impact and ROI. Keep it under 500 words.")

# Generate a report with specific structure requirements
technical_report = await researcher.write_report(custom_prompt="Create a technical report with problem statement, methodology, findings, and recommendations sections.")

# Generate a conclusion
conclusion = await researcher.write_report_conclusion(report)

# Get subtopics
subtopics = await researcher.get_subtopics()

# Get draft section titles for a subtopic
draft_titles = await researcher.get_draft_section_titles("Subtopic name")
```

### Customizing Report Generation with Custom Prompts

The `write_report` method accepts a `custom_prompt` parameter that gives you complete control over how your research is presented:

```python
# After conducting research
research_result = await researcher.conduct_research()

# Generate a report with a custom prompt
report = await researcher.write_report(
    custom_prompt="Based on the research, provide a bullet-point summary of the key findings."
)
```

Custom prompts can be used for various purposes:

1. **Format Control**: Specify the structure, length, or style of your report
   ```python
   report = await researcher.write_report(
       custom_prompt="Write a blog post in a conversational tone using the research. Include headings and a conclusion."
   )
   ```

2. **Audience Targeting**: Tailor the content for specific readers
   ```python
   report = await researcher.write_report(
       custom_prompt="Create a report for technical stakeholders, focusing on methodologies and implementation details."
   )
   ```

3. **Specialized Outputs**: Generate specific types of content
   ```python
   report = await researcher.write_report(
       custom_prompt="Create a FAQ section based on the research with at least 5 questions and detailed answers."
   )
   ```

The custom prompt will be combined with the research context to generate your customized report.

### Working with Research Context

You can use the research context for further processing or analysis:

```python
# Get the full research context
context = researcher.get_research_context()

# Get similar written contents based on draft section titles
similar_contents = await researcher.get_similar_written_contents_by_draft_section_titles(
    current_subtopic="Subtopic name",
    draft_section_titles=["Title 1", "Title 2"],
    written_contents=some_written_contents,
    max_results=10
)
```

This comprehensive documentation should help users understand and utilize the full capabilities of the GPT Researcher package.

---

# Scraping Options

GPT Researcher now offers various methods for web scraping: static scraping with BeautifulSoup, dynamic scraping with Selenium, and High scale scraping with Tavily Extract. This document explains how to switch between these methods and the benefits of each approach.

## Configuring Scraping Method

You can choose your preferred scraping method by setting the `SCRAPER` environment variable:

1. For BeautifulSoup (static scraping):
   ```
   export SCRAPER="bs"
   ```

2. For dynamic browser scraping, either with Selenium:
   ```
   export SCRAPER="browser"
   ```
   Or with NoDriver (ZenDriver):
   ```
   export SCRAPER="nodriver"
   ```

3. For **production** use cases, you can set the Scraper to `tavily_extract` or `firecrawl`. [Tavily](https://tavily.com) allows you to scrape sites at scale without the hassle of setting up proxies, managing cookies, or dealing with CAPTCHAs. Please note that you need to have a Tavily account and [API key](https://app.tavily.com) to use this option. To learn more about Tavily Extract [see here](https://docs.tavily.com/docs/python-sdk/tavily-extract/getting-started).
    Make sure to first install the pip package `tavily-python`. Then:
   ```
   export SCRAPER="tavily_extract"
   ```
   [FireCrawl](https://firecrawl.dev) is also allows you to scrape sites at scale. FireCrawl also provides open source code to self hosted server which provided better scrape quality compared to BeautifulSoup by passing markdown version of the scraped sites to LLMs. You will needs to have FireCrawl account (official service) to get API key or you needs self host URL and API key (if you set for your self host server) to use this option.
   Make sure to install the pip package `firecrawl-py`. Then:
   ```bash
   export SCRAPER="firecrawl"
   ```

Note: If not set, GPT Researcher will default to BeautifulSoup for scraping.

## Scraping Methods Explained

### BeautifulSoup (Static Scraping)

When `SCRAPER="bs"`, GPT Researcher uses BeautifulSoup for static scraping. This method:

- Sends a single HTTP request to fetch the page content
- Parses the static HTML content
- Extracts text and data from the parsed HTML

Benefits:
- Faster and more lightweight
- Doesn't require additional setup
- Works well for simple, static websites

Limitations:
- Cannot handle dynamic content loaded by JavaScript
- May miss content that requires user interaction to display

### Selenium (Browser Scraping)

When `SCRAPER="browser"`, GPT Researcher uses Selenium for dynamic scraping. This method:

- Opens a real browser instance (Chrome by default)
- Loads the page and executes JavaScript
- Waits for dynamic content to load
- Extracts text and data from the fully rendered page

Benefits:
- Can scrape dynamically loaded content
- Simulates real user interactions (scrolling, clicking, etc.)
- Works well for complex, JavaScript-heavy websites

Limitations:
- Slower than static scraping
- Requires more system resources
- Requires additional setup (Selenium and WebDriver installation)

### NoDriver (Browser Scraping)

Alternative to Selenium for potentially better performance.

Setup:
```bash
pip install zendriver
```

### Tavily Extract (Recommended for Production)

When `SCRAPER="tavily_extract"`, GPT Researcher uses Tavily's Extract API for web scraping. This method:

- Uses Tavily's robust infrastructure to handle web scraping at scale
- Automatically handles CAPTCHAs, JavaScript rendering, and anti-bot measures
- Provides clean, structured content extraction

Benefits:
- Production-ready and highly reliable
- No need to manage proxies or handle rate limiting
- Excellent success rate on most websites
- Handles both static and dynamic content
- Built-in content cleaning and formatting
- Fast response times through Tavily's distributed infrastructure

Setup:
1. Create a Tavily account at [app.tavily.com](https://app.tavily.com)
2. Get your API key from the dashboard
3. Install the Tavily Python SDK:
   ```bash
   pip install tavily-python
   ```
4. Set your Tavily API key:
   ```bash
   export TAVILY_API_KEY="your-api-key"
   ```

Usage Considerations:
- Requires a Tavily API key and account
- API calls are metered based on your Tavily plan
- Best for production environments where reliability is crucial
- Ideal for businesses and applications that need consistent scraping results

### FireCrawl (Recommended for Production)
When `SCRAPER="firecrawl"`, GPT Researcher uses FireCrawl Scrape API for web scraping in markdown format. This method:

- Uses FireCrawl's robust infrastructure to handle web scraping at scale
- Or uses self-hosted FireCrawl server.
- Automatically handles CAPTCHAs, JavaScript rendering, and anti-bot measures
- Provides clean, structured content extraction in markdown format.

Benefits:
- Production-ready and highly reliable
- No need to manage proxies or handle rate limiting
- Excellent success rate on most websites
- Handles both static and dynamic content
- Built-in content cleaning and formatting
- Fast response times through FireCrawl's distributed infrastructure
- Ease of setup with FireCrawl self-hosted

Setup (official service by FireCrawl):
1. Create a FireCrawl account at [firecrawl.dev/app](https://www.firecrawl.dev/app)
2. Get your API key from the dashboard
3. Install the FireCrawl Python SDK:
   ```bash
   pip install firecrawl-py
   ```
4. Set your FireCrawl API key:
   ```bash
   export FIRECRAWL_API_KEY=<your-firecrawl-api>
   ```
Setup (with self-hosted server):
1. Host your FireCrawl. Read their [self-hosted guidelines](https://docs.firecrawl.dev/contributing/self-host) or [run locally guidelines](https://docs.firecrawl.dev/contributing/guide)
2. Get your server URL and API key (if you set it).
3. Install the FireCrawl Python SDK:
   ```bash
   pip install firecrawl-py
   ```
4. Set your FireCrawl API key:
   ```bash
   export FIRECRAWL_API_KEY=<your-firecrawl-api>
   ```

Note: `FIRECRAWL_API_KEY` can be empty if you not setup authentication for your self host server (`FIRECRAWL_API_KEY=""`).
There will be some difference between their cloud service and open source service. To understand differences between FireCrawl option read [here](https://docs.firecrawl.dev/contributing/open-source-or-cloud).

Usage Considerations:
- Requires a FireCrawl API key and account or self-hosted server
- API calls are metered based on your FireCrawl plan (it can be basically free with self-hosted FireCrawl method)
- Best for production environments where reliability is crucial (for their cloud service)
- Ideal for businesses and applications that need consistent scraping results
- Need robust scraping option for personal use

## Additional Setup for Selenium

If you choose to use Selenium (SCRAPER="browser"), you'll need to:

1. Install the Selenium package:
   ```
   pip install selenium
   ```

2. Download the appropriate WebDriver for your browser:
   - For Chrome: [ChromeDriver](https://sites.google.com/a/chromium.org/chromedriver/downloads)
   - For Firefox: [GeckoDriver](https://github.com/mozilla/geckodriver/releases)
   - For Safari: Built-in, no download required

   Ensure the WebDriver is in your system's PATH.

## Choosing the Right Method

- Use BeautifulSoup (static) for:
  - Simple websites with mostly static content
  - Scenarios where speed is a priority
  - When you don't need to interact with the page

- Use Selenium (dynamic) for:
  - Websites with content loaded via JavaScript
  - Sites that require scrolling or clicking to load more content
  - When you need to simulate user interactions

## Troubleshooting

- If Selenium fails to start, ensure you have the correct WebDriver installed and it's in your system's PATH.
- If you encounter an `ImportError` related to Selenium, make sure you've installed the Selenium package.
- If the scraper misses expected content, try switching between static and dynamic scraping to see which works better for your target website.

Remember, the choice between static and dynamic scraping can significantly impact the quality and completeness of the data GPT Researcher can gather. Choose the method that best suits your research needs and the websites you're targeting.






---












# Configure LLM

As described in the [introduction](/docs/gpt-researcher/gptr/config), the default LLM and embedding is OpenAI due to its superior performance and speed. 
With that said, GPT Researcher supports various open/closed source LLMs and embeddings, and you can easily switch between them by updating the `SMART_LLM`, `FAST_LLM` and `EMBEDDING` env variables. You might also need to include the provider API key and corresponding configuration params.

Current supported LLMs are `openai`, `anthropic`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `groq`, `bedrock` and `litellm`.

Current supported embeddings are `openai`, `azure_openai`, `cohere`, `google_vertexai`, `google_genai`, `fireworks`, `ollama`, `together`, `mistralai`, `huggingface`, `nomic` ,`voyageai` and `bedrock`.

To learn more about support customization options see [here](/gpt-researcher/gptr/config).

**Please note**: GPT Researcher is optimized and heavily tested on GPT models. Some other models might run into context limit errors, and unexpected responses.
Please provide any feedback in our [Discord community](https://discord.gg/DUmbTebB) channel, so we can better improve the experience and performance.

Below you can find examples for how to configure the various supported LLMs.

## OpenAI

```bash
# set the custom OpenAI API key
OPENAI_API_KEY=[Your Key]

# specify llms
FAST_LLM="openai:gpt-4o-mini"
SMART_LLM="openai:gpt-4o"
STRATEGIC_LLM="openai:o1-preview"

# specify embedding
EMBEDDING="openai:text-embedding-3-small"
```


## Custom LLM

Create a local OpenAI API using [llama.cpp Server](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md#quick-start).

For custom LLM, specify "openai:{your-llm}"
```bash
# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="dummy_key"

# specify custom llms  
FAST_LLM="openai:your_fast_llm"
SMART_LLM="openai:your_smart_llm"
STRATEGIC_LLM="openai:your_strategic_llm"
```

For custom embedding, set "custom:{your-embedding}"
```bash
# set the custom OpenAI API url
OPENAI_BASE_URL="http://localhost:1234/v1"
# set the custom OpenAI API key
OPENAI_API_KEY="dummy_key"

# specify the custom embedding model   
EMBEDDING="custom:your_embedding"
```


## Azure OpenAI

In Azure OpenAI you have to chose which models you want to use and make deployments for each model. You do this on the [Azure OpenAI Portal](https://portal.azure.com/). 

In January 2025 the models that are recommended to use are: 

- gpt-4o-mini
- gpt-4o
- o1-preview or o1-mini (You might need to request access to these models before you can deploy them).

Please then specify the model names/deployment names in your `.env` file.

**Required Precondition** 

- Ypur endpoint can have any valid name.
- A model's deployment name *must be the same* as the model name.
- You need to deploy an *Embedding Model*: To ensure optimal performance, GPT Researcher requires the 'text-embedding-3-large' model. Please deploy this specific model to your Azure Endpoint.

**Recommended**:

- Quota increase: You should also request a quota increase especially for the embedding model, as the default quota is not sufficient. 

```bash
# set the azure api key and deployment as you have configured it in Azure Portal. There is no default access point unless you configure it yourself!
AZURE_OPENAI_API_KEY="[Your Key]"
AZURE_OPENAI_ENDPOINT="https://{your-endpoint}.openai.azure.com/"
OPENAI_API_VERSION="2024-05-01-preview"

# each string is "azure_openai:deployment_name". ensure that your deployment have the same name as the model you use!
FAST_LLM="azure_openai:gpt-4o-mini" 
SMART_LLM="azure_openai:gpt-4o"
STRATEGIC_LLM="azure_openai:o1-preview"

# specify embedding
EMBEDDING="azure_openai:text-embedding-3-large"
```

```
## Openrouter.ai

```bash
OPENROUTER_API_KEY=[Your openrouter.ai key]
OPENAI_BASE_URL=https://openrouter.ai/api/v1
FAST_LLM="openrouter:google/gemini-2.0-flash-lite-001"
SMART_LLM="openrouter:google/gemini-2.0-flash-001"
STRATEGIC_LLM="openrouter:google/gemini-2.5-pro-exp-03-25"
OPENROUTER_LIMIT_RPS=1  # Ratelimit request per secound
EMBEDDING=google_genai:models/text-embedding-004 # openrouter doesn't support embedding models, use google instead its free
GOOGLE_API_KEY=[Your *google gemini* key]  
```


## Other Embedding Models

### Nomic

```bash
EMBEDDING="nomic:nomic-embed-text-v1.5"
```

### VoyageAI

```bash
VOYAGE_API_KEY=[Your Key]
EMBEDDING="voyageai:voyage-law-2"
```

Add `langchain-voyageai` to [requirements.txt](https://github.com/assafelovic/gpt-researcher/blob/master/requirements.txt) for Docker Support or `pip install` it