import os
import asyncio
import logging
from typing import Optional, Dict, List
from datetime import datetime
import json

from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.openai import OpenAIChat
from agno.os import AgentOS
from fastapi.middleware.cors import CORSMiddleware
from agno.db.postgres import PostgresDb
from agno.knowledge.knowledge import Knowledge
from agno.vectordb.pgvector import PgVector
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
DATABASE_CONNECTION_STRING = os.getenv("DATABASE_CONNECTION_STRING")
DATABASE_HOST = os.getenv("DATABASE_HOST")
DATABASE_PORT = os.getenv("DATABASE_PORT")
DATABASE_NAME = os.getenv("DATABASE_NAME")
DATABASE_USER = os.getenv("DATABASE_USER")
DATABASE_PASSWORD = os.getenv("DATABASE_PASSWORD")
ENV = os.getenv("ENV", "development")

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY not set in .env")

DB_URL = DATABASE_CONNECTION_STRING

# Database and vector setup
db = PostgresDb(
    db_url=DB_URL,
    id="swimbench-db",
    knowledge_table="knowledge_contents",
)

vector_db = PgVector(
    table_name="vectors", 
    db_url=DB_URL,
    embedder=OpenAIEmbedder(),
)

# Initialize knowledge base for swim performance data
knowledge = Knowledge(
    name="SwimBench AI Knowledge Base",
    description="Comprehensive swim performance benchmarking knowledge including USA Swimming standards, college recruiting data, and performance analysis",
    contents_db=db,
    vector_db=vector_db
)

# PostgreSQL tools for swim data queries
postgres_tools = PostgresTools(
    host=DATABASE_HOST,
    port=DATABASE_PORT,
    db_name=DATABASE_NAME,
    user=DATABASE_USER,
    password=DATABASE_PASSWORD,
    table_schema="ai",
)

# Enhanced SwimBench AI Agent
swimbench_ai_agent = Agent(
    name="SWIMBENCH AI",
    model=OpenAIChat(
        id="gpt-4o", 
        temperature=0.1
    ),
    instructions=[
        "You are SWIMBENCH AI, a specialized swim performance benchmarking assistant that ONLY analyzes swim times and performance data.",
        
        "## Core Functionality (ONLY):",
        "- Benchmark swim times against USA Swimming motivational standards (B, BB, A, AA, AAA, AAAA)",
        "- Calculate percentile rankings within age groups",
        "- Assess college recruitment readiness across D1/D2/D3 divisions",
        "- Provide performance improvement recommendations for swimming",
        
        "## STRICT SCOPE LIMITATIONS:",
        "- ONLY respond to swim performance analysis requests",
        "- DO NOT answer general swimming technique questions",
        "- DO NOT provide training advice beyond time improvement targets", 
        "- DO NOT discuss swimming equipment, nutrition, or general fitness",
        "- DO NOT engage in casual conversation unrelated to time benchmarking",
        "- If asked about non-benchmarking topics, politely redirect to swim time analysis",
        
        "## Required Input Validation:",
        "Always collect these required parameters before analysis:",
        "1. **Event** (e.g., '100_freestyle', '200_backstroke')",
        "2. **Age** (8-18 years old)",  
        "3. **Time** (format: MM:SS.SS or SS.SS)",
        "4. **Gender** (M/F) - ask if not provided",
        "5. **Course** (SCY/SCM/LCM) - default to SCY if not specified",
        
        "## Database Query Strategy:",
        "1. First query ai.usa_swimming_standards for age group standards",
        "2. Query ai.college_recruiting_standards for recruitment benchmarks", 
        "3. Store analysis in ai.performance_analyses table",
        "4. If exact age group not found, use closest age group and explain",
        
        "## Analysis Output Format (REQUIRED):",
        "Provide results EXACTLY in this structured format:",
        "```markdown",
        "# 🏊‍♂️ Swim Performance Analysis",
        "",
        "## 📊 **Performance Summary**",
        "- **Time:** [formatted time]", 
        "- **Percentile Ranking:** [X]% (Top [X]% nationally)",
        "- **USA Swimming Standard:** [AAAA/AAA/AA/A/BB/B]",
        "- **Ability Level:** [Elite/Advanced/Intermediate/Novice/Beginner]",
        "",
        "## 🎓 **College Recruitment Analysis**",
        "- **D1 Elite Programs:** [Qualified/Not Qualified] ✅/❌",
        "- **D1 Mid-Major:** [Qualified/Not Qualified] ✅/❌", 
        "- **D2 Programs:** [Qualified/Not Qualified] ✅/❌",
        "- **D3 Programs:** [Qualified/Not Qualified] ✅/❌",
        "",
        "## 🎯 **Next Goals**",
        "- **Next Standard:** [time needed for next level]",
        "- **Time Drop Needed:** [X.XX seconds]",
        "```",
        
        "## Non-Benchmarking Query Response:",
        "If asked about anything other than swim time analysis, respond EXACTLY:",
        "\"I'm SWIMBENCH AI and I specialize exclusively in swim time benchmarking and performance analysis. Please provide your swim time, age, event, and gender for analysis. Example: '16M, 100 freestyle, 48.5 seconds'\"",
        
        "## Error Handling:",
        "- If database query fails, explain clearly and suggest trying again",
        "- If event not found, list available events from ai.swim_events table",
        "- If age out of range, explain USA Swimming age groups",
        "- If unrealistic times provided, ask for verification",
        
        "## Response Style:",
        "- Use encouraging, coach-like tone ONLY for performance analysis",
        "- Include relevant emojis for visual appeal", 
        "- Be specific with times and percentages",
        "- Focus exclusively on benchmarking data and results",
        "- NO general swimming advice beyond time targets",
        
        "## Available Events (Reference Only):",
        "50_freestyle, 100_freestyle, 200_freestyle, 500_freestyle, 1650_freestyle, 100_backstroke, 200_backstroke, 100_breaststroke, 200_breaststroke, 100_butterfly, 200_butterfly, 200_im, 400_im",
        
        "REMEMBER: Your ONLY purpose is swim time benchmarking analysis. Stay focused on this single function."
    ],
    description="SWIMBENCH AI: Advanced swim performance benchmarking system with real USA Swimming and college recruiting data",
    user_id="swimbench_user",
    db=db,
    knowledge=knowledge,
    add_history_to_context=True,
    num_history_runs=15,
    search_knowledge=True,
    markdown=True,
    tools=[ReasoningTools(), postgres_tools],
)

# Initialize AgentOS
agent_os = AgentOS(
    os_id="swimbench-os",
    description="SwimBench AI Performance Benchmarking System",
    agents=[swimbench_ai_agent],
)

app = agent_os.get_app()

# CORS for production
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
    """Load swim performance knowledge into the database"""
    try:
        logger.info("Starting SwimBench knowledge loading...")
        await knowledge.clear()

        # Load USA Swimming standards documentation
        result1 = await knowledge.add_content_async(
            name="USA Swimming Motivational Time Standards 2024-2028",
            url="https://websitedevsa.blob.core.windows.net/sitefinity/docs/default-source/timesdocuments/time-standards/2025/2028-motivational-standards-age-group.pdf",
            metadata={
                "user_tag": "USA Swimming Standards", 
                "content_type": "standards", 
                "source": "PDF",
                "year": "2024-2028"
            }
        )
        
        # Load college recruiting information
        result2 = await knowledge.add_content_async(
            name="College Swimming Recruiting Standards",
            url="https://www.ncsasports.org/mens-swimming/college-swimming-recruiting-times",
            metadata={
                "user_tag": "College Recruiting", 
                "content_type": "recruiting", 
                "source": "NCSA"
            }
        )
        
        logger.info("SwimBench knowledge loading completed successfully")
        
        return {
            "status": "success", 
            "message": "SwimBench knowledge base loaded successfully",
            "loaded_documents": [
                "USA Swimming Standards 2024-2028",
                "College Recruiting Standards"
            ]
        }
        
    except Exception as e:
        logger.error(f"Error loading SwimBench knowledge: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error loading knowledge: {str(e)}")

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": "SwimBench AI",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/events")
async def get_available_events():
    """Get list of available swim events"""
    try:
        # This would query your ai.swim_events table
        events = [
            "50_freestyle", "100_freestyle", "200_freestyle", "500_freestyle", "1650_freestyle",
            "100_backstroke", "200_backstroke", "100_breaststroke", "200_breaststroke",
            "100_butterfly", "200_butterfly", "200_im", "400_im"
        ]
        return {"events": events}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Run the application
if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", 8000))
    use_reload = ENV == "development"
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0", 
        port=port,
        reload=use_reload
    )
