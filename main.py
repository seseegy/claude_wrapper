"""
Claude Code OpenAI Wrapper - Main Application
A production-ready OpenAI-compatible API wrapper for Claude Code CLI
"""

from fastapi import FastAPI, HTTPException, Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any, Union
import asyncio
import json
import time
import uuid
from datetime import datetime
import logging
import os
from enum import Enum
from contextlib import asynccontextmanager

# Import Claude CLI client
from corrected_claude_client import ClaudeCodeClient, Config

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load configuration
config = Config()

# Security
security = HTTPBearer(auto_error=False)

class ModelType(str, Enum):
    """Available models mapped to Claude equivalents"""
    GPT_3_5_TURBO = "gpt-3.5-turbo"
    GPT_3_5_TURBO_16K = "gpt-3.5-turbo-16k"
    GPT_4 = "gpt-4"
    GPT_4_TURBO = "gpt-4-turbo"
    GPT_4O = "gpt-4o"
    GPT_4O_MINI = "gpt-4o-mini"
    # Additional models from MODEL_MAPPING
    GPT_4_32K = "gpt-4-32k"
    CLAUDE_SONNET = "claude-sonnet"
    CLAUDE_HAIKU = "claude-haiku"
    CLAUDE_4_SONNET = "claude-4-sonnet"

class MessageRole(str, Enum):
    """Message roles"""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"

class Message(BaseModel):
    """Chat message structure"""
    role: MessageRole
    content: str
    name: Optional[str] = None

class ChatCompletionRequest(BaseModel):
    """OpenAI-compatible chat completion request"""
    model: ModelType
    messages: List[Message]
    max_tokens: Optional[int] = Field(default=4096, ge=1, le=8192)
    temperature: Optional[float] = Field(default=1.0, ge=0.0, le=2.0)
    top_p: Optional[float] = Field(default=1.0, ge=0.0, le=1.0)
    n: Optional[int] = Field(default=1, ge=1, le=1)
    stream: Optional[bool] = False
    stop: Optional[Union[str, List[str]]] = None
    presence_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: Optional[float] = Field(default=0.0, ge=-2.0, le=2.0)
    user: Optional[str] = None

class Choice(BaseModel):
    """Chat completion choice"""
    index: int
    message: Message
    finish_reason: Optional[str] = "stop"

class Usage(BaseModel):
    """Token usage information"""
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int

class ChatCompletionResponse(BaseModel):
    """OpenAI-compatible chat completion response"""
    id: str
    object: str = "chat.completion"
    created: int
    model: str
    choices: List[Choice]
    usage: Usage

class ModelInfo(BaseModel):
    """Model information"""
    id: str
    object: str = "model"
    created: int
    owned_by: str = "anthropic"

class ModelsResponse(BaseModel):
    """Available models response"""
    object: str = "list"
    data: List[ModelInfo]

class ErrorResponse(BaseModel):
    """Error response"""
    error: Dict[str, str]

# Global Claude client
claude_client = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan management"""
    global claude_client
    
    logger.info("🚀 Starting Claude Code OpenAI Wrapper")
    
    try:
        # Initialize Claude client
        claude_client = ClaudeCodeClient()
        logger.info("✅ Claude Code client initialized successfully")
        
        # Check health
        health = claude_client.check_health()
        if health.get("claude_cli") == "healthy":
            logger.info(f"✅ Claude CLI authenticated as: {health.get('user', 'unknown')}")
        else:
            logger.warning(f"⚠️ Claude CLI health check: {health}")
        
    except Exception as e:
        logger.error(f"❌ Failed to initialize Claude client: {e}")
        logger.error("Please ensure Claude Code CLI is installed and authenticated:")
        logger.error("  npm install -g @anthropic-ai/claude-code")
        logger.error("  claude auth login")
        raise
    
    yield
    
    logger.info("🛑 Shutting down Claude Code OpenAI Wrapper")

# FastAPI app
app = FastAPI(
    title="Claude Code OpenAI Wrapper",
    description="OpenAI-compatible API wrapper for Claude Code CLI",
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Authentication dependency
async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Security(security)):
    """Verify API key if authentication is enabled"""
    if not config.auth_required:
        return True
    
    if not credentials:
        raise HTTPException(
            status_code=401,
            detail="Authorization header required"
        )
    
    api_key = credentials.credentials
    if api_key not in config.VALID_API_KEYS:
        raise HTTPException(
            status_code=401,
            detail="Invalid API key"
        )
    
    return True

@app.get("/")
async def root():
    """Root health check endpoint"""
    return {
        "message": "Claude Code OpenAI Wrapper is running",
        "version": "1.0.0",
        "status": "healthy",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        # Check Claude client health
        claude_health = claude_client.check_health() if claude_client else {"claude_cli": "not_initialized"}
        
        return {
            "status": "healthy" if claude_health.get("claude_cli") == "healthy" else "degraded",
            "timestamp": datetime.utcnow().isoformat(),
            "version": "1.0.0",
            "claude_cli": claude_health,
            "config": {
                "auth_required": config.auth_required,
                "rate_limiting": {
                    "requests": config.RATE_LIMIT_REQUESTS,
                    "window": config.RATE_LIMIT_WINDOW
                }
            }
        }
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@app.get("/v1/models", response_model=ModelsResponse)
async def list_models(authorized: bool = Depends(verify_api_key)):
    """List available models"""
    try:
        models = []
        for model_type in ModelType:
            models.append(
                ModelInfo(
                    id=model_type.value,
                    created=int(time.time()),
                    owned_by="anthropic"
                )
            )
        
        return ModelsResponse(data=models)
    
    except Exception as e:
        logger.error(f"Error listing models: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    authorized: bool = Depends(verify_api_key)
):
    """Create chat completion (streaming and non-streaming)"""
    try:
        if not claude_client:
            raise HTTPException(
                status_code=503,
                detail="Claude client not initialized"
            )
        
        logger.info(f"Chat completion request: model={request.model}, messages={len(request.messages)}, stream={request.stream}")
        
        if request.stream:
            # Streaming response
            return StreamingResponse(
                claude_client.chat_completion_stream(request),
                media_type="text/plain",
                headers={
                    "Cache-Control": "no-cache",
                    "Connection": "keep-alive",
                    "X-Accel-Buffering": "no"  # Disable nginx buffering
                }
            )
        else:
            # Non-streaming response
            response = await claude_client.chat_completion(request)
            logger.info(f"Chat completion response: tokens={response.get('usage', {}).get('total_tokens', 0)}")
            return response
    
    except Exception as e:
        logger.error(f"Chat completion error: {e}")
        
        # Return OpenAI-compatible error format
        error_response = {
            "error": {
                "message": str(e),
                "type": "server_error",
                "code": "internal_error"
            }
        }
        
        if "not authenticated" in str(e).lower():
            raise HTTPException(
                status_code=401,
                detail="Claude CLI not authenticated. Please run: claude auth login"
            )
        elif "timeout" in str(e).lower():
            raise HTTPException(status_code=504, detail=error_response)
        else:
            raise HTTPException(status_code=500, detail=error_response)

@app.get("/v1/models/{model_id}")
async def get_model(model_id: str, authorized: bool = Depends(verify_api_key)):
    """Get specific model information"""
    try:
        # Check if model exists
        valid_models = [model.value for model in ModelType]
        if model_id not in valid_models:
            raise HTTPException(status_code=404, detail=f"Model {model_id} not found")
        
        return ModelInfo(
            id=model_id,
            created=int(time.time()),
            owned_by="anthropic"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting model {model_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Optional: Metrics endpoint for monitoring
@app.get("/metrics")
async def get_metrics():
    """Prometheus-style metrics endpoint"""
    try:
        metrics = []
        
        # Basic health metric
        health = claude_client.check_health() if claude_client else {"claude_cli": "not_initialized"}
        health_status = 1 if health.get("claude_cli") == "healthy" else 0
        
        metrics.append(f"claude_wrapper_healthy {health_status}")
        metrics.append(f"claude_wrapper_uptime_seconds {time.time()}")
        
        return "\n".join(metrics)
    
    except Exception as e:
        logger.error(f"Metrics error: {e}")
        return f"# Error generating metrics: {e}"

# Error handlers
@app.exception_handler(404)
async def not_found_handler(request, exc):
    return {
        "error": {
            "message": f"Not found: {request.url.path}",
            "type": "not_found_error",
            "code": "not_found"
        }
    }

@app.exception_handler(500)
async def internal_error_handler(request, exc):
    logger.error(f"Internal error: {exc}")
    return {
        "error": {
            "message": "Internal server error",
            "type": "server_error", 
            "code": "internal_error"
        }
    }

# Startup is handled by the lifespan context manager above

if __name__ == "__main__":
    import uvicorn
    
    port = config.PORT
    host = config.HOST
    log_level = config.LOG_LEVEL.lower()
    
    logger.info(f"🚀 Starting Claude Code OpenAI Wrapper on {host}:{port}")
    logger.info(f"📚 Documentation: http://{host}:{port}/docs")
    logger.info(f"🔐 Authentication required: {config.auth_required}")
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        log_level=log_level,
        reload=False  # Set to True for development
    )
