"""
Claude Code CLI Integration
Interfaces with Claude Code CLI instead of direct API calls
"""

import asyncio
import subprocess
import json
import tempfile
import os
import shutil
from typing import Dict, List, Optional, AsyncGenerator, Any
import uuid
import time
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class Config:
    """Configuration class for Claude wrapper"""
    
    def __init__(self):
        # Server configuration
        self.PORT = int(os.getenv("PORT", 8000))
        self.HOST = os.getenv("HOST", "0.0.0.0")
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        
        # Authentication (for the wrapper API, not Claude)
        self.VALID_API_KEYS = self._parse_api_keys(os.getenv("VALID_API_KEYS", ""))
        
        # Claude CLI configuration
        self.CLAUDE_CLI_TIMEOUT = int(os.getenv("CLAUDE_CLI_TIMEOUT", 60))
        self.CLAUDE_MODEL_DEFAULT = os.getenv("CLAUDE_MODEL_DEFAULT", "claude-3-sonnet-20240229")
        
        # Rate limiting
        self.RATE_LIMIT_REQUESTS = int(os.getenv("RATE_LIMIT_REQUESTS", 100))
        self.RATE_LIMIT_WINDOW = int(os.getenv("RATE_LIMIT_WINDOW", 60))
        
        # Monitoring
        self.ENABLE_METRICS = os.getenv("ENABLE_METRICS", "true").lower() == "true"
        self.ENABLE_LOGGING = os.getenv("ENABLE_LOGGING", "true").lower() == "true"
    
    def _parse_api_keys(self, api_keys_str: str) -> List[str]:
        """Parse comma-separated API keys"""
        if not api_keys_str:
            return []
        return [key.strip() for key in api_keys_str.split(",") if key.strip()]
    
    @property
    def auth_required(self) -> bool:
        """Check if authentication is required"""
        return len(self.VALID_API_KEYS) > 0

class ClaudeCodeClient:
    """Client that interfaces with Claude Code CLI"""
    
    # Model mapping from OpenAI names to Claude models
    MODEL_MAPPING = {
    # Model existing
    "gpt-3.5-turbo": "claude-3-haiku-20240307",
    "gpt-3.5-turbo-16k": "claude-3-haiku-20240307", 
    "gpt-4": "claude-3-sonnet-20240229",
    "gpt-4-turbo": "claude-3-sonnet-20240229",
    "gpt-4o": "claude-3-5-sonnet-20241022",
    "gpt-4o-mini": "claude-3-haiku-20240307",
    
    # Model baru yang ditambahkan
    "gpt-4-32k": "claude-3-opus-20240229",           # ← Model baru
    "claude-sonnet": "claude-3-5-sonnet-20241022",   # ← Direct mapping
    "claude-haiku": "claude-3-haiku-20240307",
    "claude-4-sonnet": "claude-4-sonnet-20250514"
}
    
    def __init__(self):
        self.config = Config()
        self.claude_cmd = self._find_claude_command()
        self.temp_dir = Path(tempfile.gettempdir()) / "claude-wrapper"
        self.temp_dir.mkdir(exist_ok=True)
        self._verify_authentication()
        logger.info("✅ Claude Code client initialized successfully")
    
    def _find_claude_command(self) -> str:
        """Find Claude Code CLI command"""
        possible_commands = [
            "claude",
            "claude-code", 
            ["npx", "@anthropic-ai/claude-code"]
        ]
        
        for cmd in possible_commands:
            try:
                if isinstance(cmd, list):
                    test_cmd = cmd + ["--version"]
                else:
                    test_cmd = cmd.split() + ["--version"]
                
                result = subprocess.run(
                    test_cmd,
                    capture_output=True, 
                    text=True, 
                    timeout=10
                )
                
                if result.returncode == 0:
                    cmd_str = " ".join(cmd) if isinstance(cmd, list) else cmd
                    logger.info(f"✅ Found Claude CLI: {cmd_str}")
                    return cmd_str
                    
            except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.CalledProcessError):
                continue
        
        raise RuntimeError(
            "❌ Claude Code CLI not found. Please install with:\n"
            "npm install -g @anthropic-ai/claude-code"
        )
    
    def _verify_authentication(self):
        """Verify Claude Code CLI authentication"""
        try:
            cmd = self.claude_cmd.split() + ["auth", "whoami"]
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                error_msg = result.stderr.strip() or "Authentication failed"
                logger.warning(f"⚠️ Claude CLI not authenticated: {error_msg}")
                logger.warning("Starting in degraded mode - authentication will be checked on first request")
                return
            
            user_info = result.stdout.strip()
            logger.info(f"✅ Claude CLI authenticated: {user_info}")
            
        except subprocess.TimeoutExpired:
            logger.warning("⚠️ Claude CLI authentication check timed out - starting in degraded mode")
            logger.warning("Authentication will be checked on first request")
        except Exception as e:
            logger.warning(f"⚠️ Authentication verification failed: {e}")
            logger.warning("Starting in degraded mode - authentication will be checked on first request")
    
    def _convert_messages_to_prompt(self, messages: List[Dict]) -> str:
        """Convert OpenAI messages format to Claude prompt"""
        prompt_parts = []
        
        for message in messages:
            role = message.get("role", "")
            content = message.get("content", "")
            
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"Human: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        # Ensure proper conversation flow
        prompt = "\n\n".join(prompt_parts)
        
        # Add Assistant: at the end if not present
        if not prompt.endswith("Assistant:") and not prompt.endswith("Assistant: "):
            prompt += "\n\nAssistant:"
        
        return prompt
    
    def _map_model_to_claude(self, openai_model: str) -> str:
        """Map OpenAI model names to Claude model identifiers"""
        return self.MODEL_MAPPING.get(openai_model, "claude-3-sonnet-20240229")
    
    def _apply_temperature_instruction(self, prompt: str, temperature: float) -> str:
        """Apply temperature as instruction since Claude CLI might not support it directly"""
        if temperature < 0.3:
            instruction = "Please be precise, focused, and concise in your response."
        elif temperature > 0.7:
            instruction = "Please be creative, varied, and expressive in your response."
        else:
            instruction = "Please provide a balanced and natural response."
        
        # Insert instruction before the final "Assistant:" if present
        if prompt.endswith("Assistant:"):
            prompt = prompt[:-10] + f"{instruction}\n\nAssistant:"
        else:
            prompt = f"{prompt}\n\n{instruction}"
        
        return prompt
    
    async def _run_claude_command(self, prompt: str, model: str, temperature: float = 1.0) -> str:
        """Run Claude CLI command asynchronously"""
        try:
            # Apply temperature as instruction
            if temperature != 1.0:
                prompt = self._apply_temperature_instruction(prompt, temperature)
            
            # Build command - let system prompt from bot determine the mode
            cmd = self.claude_cmd.split() + [
                "--print",  # Print output to stdout
                "--model", model,
                prompt  # The prompt as the last argument
            ]
            
            logger.debug(f"Executing Claude command with model: {model}")
            
            # Execute command
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=self.temp_dir
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(), 
                timeout=self.claude_cmd_timeout
            )
            
            if process.returncode != 0:
                error_msg = stderr.decode('utf-8').strip()
                logger.error(f"❌ Claude CLI error (code {process.returncode}): {error_msg}")
                
                if "not authenticated" in error_msg.lower():
                    raise RuntimeError("Claude CLI not authenticated. Please run: claude auth login")
                elif "model" in error_msg.lower():
                    raise RuntimeError(f"Invalid model or model access error: {error_msg}")
                else:
                    raise RuntimeError(f"Claude CLI failed: {error_msg}")
            
            response = stdout.decode('utf-8').strip()
            
            if not response:
                raise RuntimeError("Empty response from Claude CLI")
            
            logger.debug(f"Claude response length: {len(response)} characters")
            return response
            
        except asyncio.TimeoutError:
            logger.error(f"❌ Claude CLI command timed out after {self.claude_cmd_timeout}s")
            raise RuntimeError(f"Claude CLI timed out after {self.claude_cmd_timeout}s")
        except Exception as e:
            logger.error(f"❌ Claude CLI execution error: {e}")
            raise RuntimeError(f"Claude CLI execution failed: {e}")
    
    @property
    def claude_cmd_timeout(self) -> int:
        """Get Claude command timeout from config"""
        return self.config.CLAUDE_CLI_TIMEOUT
    
    def _estimate_tokens(self, text: str) -> int:
        """Rough token estimation (1 token ≈ 0.75 words)"""
        return max(1, int(len(text.split()) * 1.3))
    
    async def chat_completion(self, request) -> Dict[str, Any]:
        """Generate chat completion using Claude Code CLI"""
        try:
            # Convert messages to prompt
            prompt = self._convert_messages_to_prompt([msg.dict() for msg in request.messages])
            
            # Map model
            claude_model = self._map_model_to_claude(request.model)
            
            # Get temperature
            temperature = getattr(request, 'temperature', 1.0)
            
            logger.info(f"🔄 Processing request: model={claude_model}, prompt_length={len(prompt)}")
            
            # Call Claude CLI
            response_content = await self._run_claude_command(prompt, claude_model, temperature)
            
            # Estimate token usage
            prompt_tokens = self._estimate_tokens(prompt)
            completion_tokens = self._estimate_tokens(response_content)
            total_tokens = prompt_tokens + completion_tokens
            
            # Build OpenAI-compatible response
            response = {
                "id": f"chatcmpl-{uuid.uuid4().hex[:8]}",
                "object": "chat.completion",
                "created": int(time.time()),
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "message": {
                        "role": "assistant",
                        "content": response_content
                    },
                    "finish_reason": "stop"
                }],
                "usage": {
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": total_tokens
                }
            }
            
            logger.info(f"✅ Completion successful: {total_tokens} tokens")
            return response
            
        except Exception as e:
            logger.error(f"❌ Chat completion error: {e}")
            raise RuntimeError(f"Chat completion failed: {e}")
    
    async def chat_completion_stream(self, request) -> AsyncGenerator[str, None]:
        """Generate streaming chat completion (simulated)"""
        try:
            logger.info("🔄 Starting streaming completion...")
            
            # Get full response first (Claude CLI doesn't natively stream)
            response = await self.chat_completion(request)
            content = response["choices"][0]["message"]["content"]
            
            # Stream the response word by word
            words = content.split()
            chunk_id = f"chatcmpl-{uuid.uuid4().hex[:8]}"
            created = int(time.time())
            
            # Send opening chunk
            for i, word in enumerate(words):
                chunk = {
                    "id": chunk_id,
                    "object": "chat.completion.chunk",
                    "created": created,
                    "model": request.model,
                    "choices": [{
                        "index": 0,
                        "delta": {"content": word + " "},
                        "finish_reason": None
                    }]
                }
                
                yield f"data: {json.dumps(chunk)}\n\n"
                
                # Small delay for realistic streaming
                await asyncio.sleep(0.03)
            
            # Send final chunk
            final_chunk = {
                "id": chunk_id,
                "object": "chat.completion.chunk", 
                "created": created,
                "model": request.model,
                "choices": [{
                    "index": 0,
                    "delta": {},
                    "finish_reason": "stop"
                }]
            }
            
            yield f"data: {json.dumps(final_chunk)}\n\n"
            yield "data: [DONE]\n\n"
            
            logger.info("✅ Streaming completion finished")
            
        except Exception as e:
            logger.error(f"❌ Streaming completion error: {e}")
            error_chunk = {
                "error": {
                    "message": str(e),
                    "type": "server_error",
                    "code": "internal_error"
                }
            }
            yield f"data: {json.dumps(error_chunk)}\n\n"
    
    def check_health(self) -> Dict[str, Any]:
        """Check Claude CLI health and authentication status"""
        try:
            # Check command availability
            cmd = self.claude_cmd.split() + ["--version"]
            version_result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=5
            )
            
            if version_result.returncode != 0:
                return {
                    "claude_cli": "unhealthy",
                    "error": "Claude CLI not working",
                    "command": self.claude_cmd
                }
            
            # Check authentication
            auth_cmd = self.claude_cmd.split() + ["auth", "whoami"]
            auth_result = subprocess.run(
                auth_cmd,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if auth_result.returncode == 0:
                return {
                    "claude_cli": "healthy",
                    "authenticated": True,
                    "user": auth_result.stdout.strip(),
                    "command": self.claude_cmd,
                    "version": version_result.stdout.strip()
                }
            else:
                return {
                    "claude_cli": "degraded",
                    "authenticated": False,
                    "error": auth_result.stderr.strip(),
                    "command": self.claude_cmd,
                    "version": version_result.stdout.strip()
                }
                
        except Exception as e:
            return {
                "claude_cli": "unhealthy",
                "error": str(e),
                "command": self.claude_cmd
            }
    
    def __del__(self):
        """Cleanup temporary directory on deletion"""
        try:
            if hasattr(self, 'temp_dir') and self.temp_dir.exists():
                shutil.rmtree(self.temp_dir, ignore_errors=True)
        except:
            pass
