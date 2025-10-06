# Chat-VRD Pipecat Backend - Technical Overview

## Project Overview

Chat-VRD is a voice conversation backend system that enables real-time multilingual voice interactions using Pipecat framework, Daily.co WebRTC infrastructure, and Google Gemini Live API for speech processing and conversation intelligence.

## Core Components

### 1. FastAPI Server (`server.py`)
**Responsibilities:**
- HTTP API endpoint management
- Daily.co room creation and token generation
- Bot lifecycle management
- Health monitoring and diagnostics

**Key Classes/Functions:**
- `ConnectRequest`: Pydantic model for connection requests with optional language parameter
- `create_daily_room()`: Async function for room creation and dual token generation (bot + client)
- `/health` endpoint: Comprehensive health check including API key validation
- `/connect` endpoint: Main orchestration endpoint for room creation and bot spawning

**Design Patterns:**
- Async/await pattern for non-blocking I/O operations
- Dependency injection through environment variables
- Error handling with structured HTTP exceptions

### 2. Pipecat Bot (`bot.py`)
**Responsibilities:**
- WebRTC transport management via Daily.co
- Speech-to-Text (STT) and Text-to-Speech (TTS) processing
- Language-specific voice configuration
- Real-time conversation pipeline orchestration

**Key Functions:**
- `run_bot()`: Main bot execution function with language-aware configuration
- Pipeline construction using Pipecat's modular architecture
- Integration with Gemini Multimodal Live LLM service

**Design Patterns:**
- Pipeline pattern for audio processing workflow
- Strategy pattern for language-specific configurations
- Event-driven architecture for real-time audio handling

### 3. Configuration Management
**Environment Variables:**
- `DAILY_API_KEY`: Daily.co API authentication
- `GOOGLE_API_KEY`: Google Gemini API access
- `PORT`: Server port configuration (Railway-managed)

## Component Interactions

### Data Flow Architecture
```
Client Request → FastAPI Server → Daily.co Room Creation → Bot Spawning → Gemini Processing
     ↓              ↓                    ↓                    ↓              ↓
  Language     Token Generation    WebRTC Transport    Pipeline      STT/LLM/TTS
  Preference   & Room Config       & Audio Stream      Creation      Integration
```

### Communication Methods
1. **HTTP REST API**: Client-server communication via FastAPI endpoints
2. **WebRTC**: Real-time audio/video streaming through Daily.co
3. **Async Task Management**: Bot lifecycle via asyncio task tracking
4. **External API Integration**: Daily.co REST API and Google Gemini API

### API Interfaces
- **Daily.co API**: Room creation, token generation, WebRTC transport
- **Google Gemini Live API**: Multilingual STT, LLM processing, TTS synthesis
- **Pipecat Framework**: Audio pipeline orchestration and VAD (Voice Activity Detection)

### Service Dependencies
- FastAPI depends on bot module availability (graceful degradation)
- Bot depends on both Daily.co and Google API keys
- Pipeline components are loosely coupled through Pipecat's modular architecture

## Deployment Architecture

### Build Configuration
- **Runtime**: Python 3.10+ with Uvicorn ASGI server
- **Dependency Management**: pip with requirements.txt
- **Containerization**: Railway NIXPACKS builder
- **Process Management**: Procfile-based startup configuration

### Environment Requirements
- **Development**: Local Python environment with virtualenv
- **Staging/Production**: Railway cloud platform with auto-scaling
- **External Dependencies**: Daily.co and Google Cloud API access

### Infrastructure Details
```
Railway Platform
├── NIXPACKS Build System
├── Automatic Port Management ($PORT)
├── Environment Variable Injection
├── Log Aggregation & Monitoring
└── Auto-restart on Failure (max 10 retries)
```

### Deployment Methods
1. **Railway CLI**: Direct deployment with `railway up`
2. **Git Push**: Remote repository deployment
3. **GitHub Integration**: Automated CI/CD pipeline

## Runtime Behavior

### Application Initialization
1. **Environment Validation**: API key presence checking
2. **Module Loading**: Conditional bot module import with error handling
3. **Server Startup**: Uvicorn ASGI server initialization
4. **Health Check**: Comprehensive system status validation

### Request Processing Flow
1. **Room Creation**: POST `/connect` → Daily.co room generation
2. **Dual Token Creation**: Separate tokens for bot (owner) and client (participant)
3. **Bot Spawning**: Async task creation with language configuration
4. **Response Delivery**: Room URL and client token return

### Business Workflows
- **Multilingual Support**: Language-specific STT/TTS configuration via BCP-47 codes
- **Room Lifecycle**: 1-hour expiration with automatic cleanup
- **Bot Management**: Task tracking with completion callbacks
- **Error Recovery**: Structured exception handling with detailed logging

### Error Handling & Background Tasks
- **Graceful Degradation**: Server operates without bot module if unavailable
- **Task Cleanup**: Automatic bot task removal on completion
- **Exception Propagation**: Structured error responses with context
- **Logging Integration**: Comprehensive logging with Loguru for bot operations

### Performance Characteristics
- **Async Architecture**: Non-blocking I/O for concurrent request handling
- **Resource Management**: Automatic task cleanup and memory management
- **Scalability**: Railway platform auto-scaling with horizontal pod management
- **Monitoring**: Built-in health checks and log aggregation

## Security Considerations
- **API Key Management**: Environment-based configuration
- **Token-based Authentication**: Daily.co meeting tokens with scoped permissions
- **CORS Configuration**: Permissive CORS for development (configurable)
- **Input Validation**: Pydantic models for request validation

## Supported Languages
- English (US): `en-US`
- Spanish: `es-ES`
- French: `fr-FR`
- German: `de-DE`
- Dutch: `nl-NL`
- Italian: `it-IT`