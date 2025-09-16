import os
import asyncio
import logging
from typing import Optional

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from fastapi.middleware.cors import CORSMiddleware
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector  # Remove SearchType import
from fastapi import FastAPI, HTTPException
from agno.tools.reasoning import ReasoningTools
from agno.knowledge.embedder.openai import OpenAIEmbedder
from agno.tools.postgres import PostgresTools

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SUPABASE_CONNECTION_STRING = os.getenv("SUPABASE_CONNECTION_STRING")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
ENV = os.getenv("ENV", "development")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in .env")

SUPABASE_DB_URL = (
    SUPABASE_CONNECTION_STRING
)

# Initialize database connections
supabase_db = PostgresDb(
    db_url=SUPABASE_DB_URL,
    id="supabase-main",
    knowledge_table="knowledge_contents",
)

# Initialize vector database without SearchType
vector_db = PgVector(
    table_name="vectors", 
    db_url=SUPABASE_DB_URL,
    embedder=OpenAIEmbedder(),
)

# Initialize knowledge base
knowledge = Knowledge(
    name="SwimBench AI knowledge base",
    description="Comprehensive knowledge base for SwimBench AI",
    contents_db=supabase_db,
    vector_db=vector_db
)

# Initialize PostgresTools with connection details
postgres_tools = PostgresTools(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    db_name=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    table_schema="ai",
)

# Initialize Agent with corrected model and improved instructions
swimbench_ai_agent = Agent(
    name="SWIMBENCH AI",
    model=OpenAIChat(
        id="gpt-4o", 
        temperature=0.1
    ),
    instructions=[
        "You are SWIMBENCH AI, an assistant that benchmarks swim performance times by event, age, gender, and ability.",
        "Always start by checking if the user has provided the required inputs: event, age, and swim time. Gender and pool course (yards/meters) are optional but useful.",
        "If required parameters are missing, ask the user a short, clear follow-up question to get the information. Do not guess silently.",
        "When parameters are complete, call the appropriate Postgres tool to fetch standards and performance data from the Supabase database.",
        "Use that data to calculate percentile ranking, skill level category (Beginner → Elite), and comparisons to USA Swimming standards (B, A, AA, AAA, AAAA).",
        "If the sample size in the database is too small, broaden the search (e.g., nearby ages or both genders) and clearly explain this adjustment to the user.",
        "Respond in a chat-style format with clear, encouraging explanations. Include key insights such as percentile rank, standard achieved, time needed for next standard, and college readiness indicators.",
        "If a user asks a general question (not swim-related), answer politely but guide the conversation back to swim performance benchmarking.",
        "Always provide outputs in markdown for readability, using short sections, emojis, and tables/charts if available."
    ],
    description="SWIMBENCH AI: Benchmarks swim times, calculates percentiles, and provides insights for athletes, coaches, and recruiters.",
    user_id="swimbench_user",
    db=supabase_db,
    knowledge=knowledge,
    add_history_to_context=True,
    num_history_runs=20,
    search_knowledge=True,
    markdown=True,
    tools=[ReasoningTools(), postgres_tools],
)

# Initialize AgentOS
agent_os = AgentOS(
    os_id="swimbench-os",
    description="SwimBench AI",
    agents=[swimbench_ai_agent],
)

app = agent_os.get_app()

if ENV == "production":
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

@app.post("/loadknowledge")
async def load_knowledge():
    """Load knowledge into the database"""
    try:
        logger.info("Starting knowledge loading process...")
        await knowledge.clear()

        # Load the Thai recipes PDF
        result1 = await knowledge.add_content_async(
            name="Thai Recipes Collection",
            url="https://agno-public.s3.amazonaws.com/recipes/ThaiRecipes.pdf",
            metadata={"user_tag": "Thai Recipes", "content_type": "recipes", "source": "PDF"}
        )
        
        logger.info("Knowledge loading completed successfully")
        
        return {
            "status": "success", 
            "message": "Knowledge base loaded successfully",
        }
        
    except Exception as e:
        logger.error(f"Error loading knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading knowledge: {str(e)}")

# If you need to run locally, use this:
if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment (Render sets this automatically)
    port = int(os.getenv("PORT", 8000))
    
    # Only use reload in development
    use_reload = ENV == "development"
    
    uvicorn.run(
        "main:app",  # Use import string instead of app object when using reload
        host="0.0.0.0", 
        port=port,
        reload=use_reload
    )
