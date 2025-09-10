# Claude Code OpenAI Wrapper

🤖 **A production-ready OpenAI-compatible API wrapper for Claude Code CLI with dual mode system**

This project provides a FastAPI-based wrapper that makes Claude Code CLI compatible with OpenAI API format, enabling seamless integration with existing OpenAI-based applications while leveraging Claude's advanced capabilities.

## ✨ Features

### 🔄 **Dual Mode System**
- **Claude Code Mode**: Latest 2025 information, coding assistance, current events
- **Claude Regular Mode**: Image analysis, file processing, general conversations
- **Smart Auto-Switching**: Automatically selects the best model based on context

### 🚀 **Core Capabilities**
- **OpenAI API Compatible**: Drop-in replacement for OpenAI API endpoints
- **Streaming Support**: Real-time response streaming
- **Multiple Model Support**: Claude Sonnet 4, Claude 3.5 Sonnet, Haiku, Opus
- **Authentication System**: API key protection with configurable access control
- **Health Monitoring**: Built-in health checks and metrics
- **Docker Support**: Ready for containerized deployment

### 📎 **Advanced Features**
- **Image Analysis**: Process and analyze images using Claude's vision capabilities
- **File Processing**: Support for PDF, text files, and documents
- **Session Management**: Conversation context preservation
- **Error Handling**: Robust error handling with detailed logging
- **Rate Limiting**: Built-in protection against abuse

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Client App    │────│  FastAPI Wrapper │────│   Claude CLI    │
│  (OpenAI SDK)   │    │   (This Project) │    │   (Official)    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Model Mapping
| OpenAI Model | Claude Model | Use Case |
|--------------|--------------|----------|
| `gpt-4o` | Claude 3.5 Sonnet | General tasks, image analysis |
| `claude-4-sonnet` | Claude Sonnet 4 | Latest info, coding |
| `gpt-4` | Claude 3 Sonnet | Standard tasks |
| `gpt-3.5-turbo` | Claude 3 Haiku | Fast responses |

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Claude Code CLI installed and authenticated
- Node.js 16+ (for WhatsApp bot)

### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/seseegy/claude-wrapper
cd claude-ai
```

2. **Install Python dependencies:**
```bash
pip install -r requirements.txt
```

3. **Install and authenticate Claude Code CLI:**
```bash
npm install -g @anthropic-ai/claude-code
claude auth login
```

4. **Start the API server:**
```bash
python main.py
```

The API will be available at `http://localhost:8000` with documentation at `http://localhost:8000/docs`

## 📖 API Usage

### Basic Chat Completion
```python
import openai

client = openai.OpenAI(
    api_key="your-api-key",  # Set in VALID_API_KEYS env var
    base_url="http://localhost:8000/v1"
)

response = client.chat.completions.create(
    model="claude-4-sonnet",  # Latest info + coding
    messages=[
        {"role": "user", "content": "Who is the current president of Indonesia?"}
    ]
)

print(response.choices[0].message.content)
# Output: "Prabowo Subianto (2024-2029) with VP Gibran Rakabuming Raka"
```

### Image Analysis
```python
response = client.chat.completions.create(
    model="gpt-4o",  # Automatically uses Claude Regular for images
    messages=[
        {
            "role": "user", 
            "content": "Please analyze this image and describe what you see."
        }
    ]
)
```

### Streaming Response
```python
stream = client.chat.completions.create(
    model="claude-4-sonnet",
    messages=[{"role": "user", "content": "Explain quantum computing"}],
    stream=True
)

for chunk in stream:
    print(chunk.choices[0].delta.content, end="")
```

## 🤖 WhatsApp Bot Integration

This project includes a full-featured WhatsApp bot with Claude integration:

### Features
- **Dual Mode AI**: Automatic switching between Claude models
- **Media Processing**: Image analysis, PDF reading, document processing
- **Access Control**: User management and permissions
- **Session Management**: Conversation context per user
- **Admin Commands**: User management, bot status, etc.

### Setup WhatsApp Bot
```bash
cd whatsapp-bot
npm install
node bot.js
```

## ⚙️ Configuration

### Environment Variables
```bash
# Server Configuration
PORT=8000
HOST=0.0.0.0
LOG_LEVEL=INFO

# Authentication (comma-separated API keys)
VALID_API_KEYS="sk-key1,sk-key2,sk-key3"

# Claude CLI Configuration
CLAUDE_CLI_TIMEOUT=60
CLAUDE_MODEL_DEFAULT=claude-3-sonnet-20240229

# Rate Limiting
RATE_LIMIT_REQUESTS=100
RATE_LIMIT_WINDOW=60

# Monitoring
ENABLE_METRICS=true
ENABLE_LOGGING=true
```

## 🐳 Docker Deployment

### Using Docker Compose
```bash
docker-compose up -d
```

### Manual Docker Build
```bash
docker build -t claude-ai-wrapper .
docker run -p 8000:8000 -e VALID_API_KEYS="your-keys" claude-ai-wrapper
```

## 📊 Monitoring & Health Checks

### Health Endpoint
```bash
curl http://localhost:8000/health
```

### Available Models
```bash
curl http://localhost:8000/v1/models
```

## 🔧 Development

### Project Structure
```
claude-ai/
├── main.py                    # FastAPI application entry point
├── corrected_claude_client.py # Claude CLI integration
├── requirements.txt           # Python dependencies
├── docker-compose.yml         # Docker configuration
├── test.py                   # API tests
└── README.md                 # This file
```

### Testing
```bash
# Test API endpoint
python test.py

# Test with current info
python test_dual.py

# Test image analysis
python test_image.py
```

## 🛡️ Security

### Authentication
- API key-based authentication
- Configurable access control
- Rate limiting protection

### Best Practices
- Never commit API keys to version control
- Use environment variables for sensitive data
- Regularly rotate authentication credentials

## 🐛 Troubleshooting

### Common Issues

1. **Claude CLI Not Authenticated**
```bash
claude auth login
```

2. **Port Already in Use**
```bash
pkill -f "python main.py"
PORT=8001 python main.py
```

3. **Model Timeout Issues**
```bash
export CLAUDE_CLI_TIMEOUT=120
```

## 📄 API Reference

### Supported Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/v1/chat/completions` | POST | Chat completions (streaming/non-streaming) |
| `/v1/models` | GET | List available models |
| `/health` | GET | Health check |
| `/docs` | GET | Interactive API documentation |

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes and test thoroughly
4. Commit with clear messages: `git commit -m "Add feature X"`
5. Push to your fork: `git push origin feature-name`
6. Create a Pull Request

## 📝 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- [Anthropic](https://anthropic.com) for Claude AI
- [FastAPI](https://fastapi.tiangolo.com) for the excellent web framework
- [OpenAI](https://openai.com) for the API standard

---

**Made with ❤️ for the AI community**

*Transform your Claude Code CLI into a production-ready API service with advanced dual-mode capabilities!*
