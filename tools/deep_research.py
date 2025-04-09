import os
import asyncio
import argparse
from dotenv import load_dotenv
from gpt_researcher import GPTResearcher
from gpt_researcher.utils.enum import ReportType, Tone

# Load environment variables
load_dotenv()

# Configure OpenRouter settings
os.environ["OPENAI_BASE_URL"] = "https://openrouter.ai/api/v1"
os.environ["OPENROUTER_API_KEY"] = os.getenv("OPENROUTER_API_KEY")
os.environ["OPENROUTER_LIMIT_RPS"] = "1"  # Ratelimit requests per second
os.environ["GOOGLE_API_KEY"] = os.getenv("OPENAI_API_KEY")  # Use for embeddings

# Model configuration
FAST_LLM = "openrouter:google/gemini-2.0-flash-lite-001"
SMART_LLM = "openrouter:google/gemini-2.0-flash-001"
STRATEGIC_LLM = "openrouter:google/gemini-2.5-pro-exp-03-25"
EMBEDDING = "google_genai:models/text-embedding-004"  # OpenRouter doesn't support embeddings

class ResearchProgressTracker:
    def __init__(self):
        self.total_queries = 0
        self.completed_queries = 0
        
    async def on_progress(self, progress):
        """Callback to track research progress"""
        self.total_queries = progress.total_queries
        self.completed_queries = progress.completed_queries
        
        depth_progress = f"Depth: {progress.current_depth}/{progress.total_depth}"
        breadth_progress = f"Breadth: {progress.current_breadth}/{progress.total_breadth}"
        query_progress = f"Queries: {progress.completed_queries}/{progress.total_queries}"
        current_query = f"Current query: {progress.current_query}"
        
        progress_percentage = (progress.completed_queries / progress.total_queries) * 100 if progress.total_queries > 0 else 0
        
        print(f"Deep Research Progress: {progress_percentage:.1f}% | {depth_progress} | {breadth_progress} | {query_progress}")
        print(f"⚡ {current_query}")
        print("-" * 80)

async def perform_deep_research(
    query, 
    breadth=3, 
    depth=2, 
    concurrency=3, 
    total_words=2000, 
    tone="informative"
):
    """
    Perform deep research on a given query using the GPT Researcher library
    
    Args:
        query (str): The research query
        breadth (int): Number of parallel research paths
        depth (int): How many levels deep to explore
        concurrency (int): Maximum concurrent research operations
        total_words (int): Total words in the generated report
        tone (str): Tone of the report (informative, analytical, etc.)
    
    Returns:
        str: The full research report
    """
    # Configure environment variables for deep research
    os.environ["DEEP_RESEARCH_BREADTH"] = str(breadth)
    os.environ["DEEP_RESEARCH_DEPTH"] = str(depth)
    os.environ["DEEP_RESEARCH_CONCURRENCY"] = str(concurrency)
    os.environ["TOTAL_WORDS"] = str(total_words)
    
    # Initialize progress tracker
    progress_tracker = ResearchProgressTracker()
    
    # Initialize researcher with deep research type
    print(f"🔍 Starting Deep Research on: {query}")
    print(f"Configuration: Breadth={breadth}, Depth={depth}, Concurrency={concurrency}, Words={total_words}")
    print("-" * 80)
    
    researcher = GPTResearcher(
        query=query,
        report_type="deep",  # This triggers deep research mode
        tone=tone,
        on_progress=progress_tracker.on_progress,
        llm_config={
            "FAST_LLM": FAST_LLM,
            "SMART_LLM": SMART_LLM,
            "STRATEGIC_LLM": STRATEGIC_LLM,
            "EMBEDDING": EMBEDDING
        }
    )
    
    # Conduct the research
    print("🧠 Starting research... this may take several minutes")
    await researcher.conduct_research()
    
    # Generate report
    print("📝 Generating final report...")
    report = await researcher.write_report()
    
    # Get research costs
    costs = researcher.get_costs()
    sources = researcher.get_source_urls()
    
    return {
        "report": report,
        "costs": costs,
        "sources": sources,
        "query": query,
        "stats": {
            "breadth": breadth,
            "depth": depth,
            "total_queries": progress_tracker.total_queries,
            "completed_queries": progress_tracker.completed_queries
        }
    }

async def main():
    parser = argparse.ArgumentParser(description='Deep Research with GPT Researcher')
    parser.add_argument('--query', type=str, required=True, help='Research query')
    parser.add_argument('--breadth', type=int, default=3, help='Number of parallel research paths')
    parser.add_argument('--depth', type=int, default=2, help='How many levels deep to explore')
    parser.add_argument('--concurrency', type=int, default=3, help='Maximum concurrent research operations')
    parser.add_argument('--words', type=int, default=2000, help='Total words in the generated report')
    parser.add_argument('--tone', type=str, default='informative', 
                      choices=['informative', 'analytical', 'academic', 'professional', 'simple'],
                      help='Tone of the report')
    parser.add_argument('--output', type=str, default='report.md', help='Output file name')
    
    args = parser.parse_args()
    
    try:
        result = await perform_deep_research(
            query=args.query,
            breadth=args.breadth,
            depth=args.depth,
            concurrency=args.concurrency,
            total_words=args.words,
            tone=args.tone
        )
        
        # Save report to file
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(f"# Deep Research: {result['query']}\n\n")
            f.write(result['report'])
            f.write("\n\n## Sources\n\n")
            for i, source in enumerate(result['sources'], 1):
                f.write(f"{i}. {source}\n")
            f.write("\n\n## Research Stats\n\n")
            f.write(f"- Depth: {result['stats']['depth']}\n")
            f.write(f"- Breadth: {result['stats']['breadth']}\n")
            f.write(f"- Total Queries: {result['stats']['total_queries']}\n")
            f.write(f"- Completed Queries: {result['stats']['completed_queries']}\n")
            f.write(f"- Estimated Cost: ${result['costs']:.4f}\n")
        
        print(f"\n✅ Research complete! Report saved to {args.output}")
        print(f"📊 Research Stats:")
        print(f"   - Depth: {result['stats']['depth']}")
        print(f"   - Breadth: {result['stats']['breadth']}")
        print(f"   - Total Queries: {result['stats']['total_queries']}")
        print(f"   - Completed Queries: {result['stats']['completed_queries']}")
        print(f"   - Estimated Cost: ${result['costs']:.4f}")
        
    except Exception as e:
        print(f"❌ Error during research: {str(e)}")

if __name__ == "__main__":
    asyncio.run(main())