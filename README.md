# 🧠 Mental Health Bot - Technical Documentation

## 📋 Table of Contents
1. [Project Overview](#project-overview)
2. [Architecture](#architecture)
3. [Technology Stack](#technology-stack)
4. [Database Schema](#database-schema)
5. [API Endpoints](#api-endpoints)
6. [WebSocket Implementation](#websocket-implementation)
7. [Services](#services)
8. [Authentication & Security](#authentication--security)
9. [Configuration](#configuration)
10. [Deployment](#deployment)
11. [Testing](#testing)
12. [Troubleshooting](#troubleshooting)

---

## 🎯 Project Overview

The Mental Health Bot is an AI-powered conversational agent designed to provide mental health support through daily check-ins and ongoing conversations. The system uses GPT-4o for natural language processing and maintains conversation context using Redis for real-time interactions.

### Key Features
- **Daily Check-ins**: Morning and evening emotional assessments
- **AI Conversation Agent**: Personalized mental health support using LLM
- **Real-time WebSocket Communication**: Instant messaging interface
- **Context-Aware Responses**: Memory of user history and check-in data
- **JWT Authentication**: Secure user access and session management
- **Redis Caching**: Efficient conversation storage and retrieval

---

## 🏗️ Architecture

### System Architecture Diagram
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   FastAPI       │    │   Database      │
│   (HTML/JS)     │◄──►│   Backend       │◄──►│   (PostgreSQL)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   WebSocket     │    │   Redis Cache   │    │   OpenAI API    │
│   Connection    │    │   Service       │    │   (GPT-4o)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Flow
1. **User Authentication**: JWT token validation
2. **Check-in Data**: Daily emotional assessments stored in PostgreSQL
3. **Context Building**: User data + check-in data + conversation history
4. **LLM Processing**: GPT-4o generates personalized responses
5. **Response Delivery**: Real-time WebSocket communication
6. **Context Storage**: Redis maintains conversation memory

---

## 🛠️ Technology Stack

### Backend
- **Framework**: FastAPI (Python 3.8+)
- **Database**: PostgreSQL with SQLAlchemy ORM
- **Cache**: Redis for conversation storage
- **Authentication**: JWT with PyJWT
- **LLM Integration**: OpenAI GPT-4o via LangChain
- **WebSocket**: FastAPI WebSocket support

### Frontend
- **Interface**: HTML5 + CSS3 + JavaScript
- **Styling**: Modern CSS with gradients and animations
- **Real-time**: WebSocket API for instant messaging

### Infrastructure
- **Database Migration**: Alembic
- **Environment**: Python virtual environment
- **Deployment**: ZIP packaging for deployment

---

## 🗄️ Database Schema

### Users Table
```sql
CREATE TABLE users (
    id SERIAL PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    first_name VARCHAR(100),
    last_name VARCHAR(100),
    age INTEGER,
    gender INTEGER CHECK (gender IN (0, 1, 2)), -- 0: Male, 1: Female, 2: Third gender
    is_active BOOLEAN DEFAULT true,
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Checkins Table
```sql
CREATE TABLE checkins (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    checkin_type VARCHAR(20) CHECK (checkin_type IN ('morning', 'evening')),
    checkin_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    -- Morning checkin fields
    sleep_quality VARCHAR(50),
    body_sensation VARCHAR(100),
    energy_level VARCHAR(50),
    mental_state VARCHAR(100),
    executive_task TEXT,
    
    -- Evening checkin fields
    emotion_category VARCHAR(50),
    overwhelm_amount VARCHAR(50),
    emotion_in_moment VARCHAR(100),
    surroundings_impact VARCHAR(100),
    meaningful_moments_quantity INTEGER,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Chat Summaries Table
```sql
CREATE TABLE chat_summaries (
    id SERIAL PRIMARY KEY,
    user_id INTEGER REFERENCES users(id),
    chat_id VARCHAR(255) NOT NULL,
    summary TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### Indexes
```sql
-- Performance indexes
CREATE INDEX idx_checkins_user_type_time ON checkins(user_id, checkin_type, checkin_time);
CREATE INDEX idx_checkins_user_time ON checkins(user_id, checkin_time);
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_chat_summaries_user_chat ON chat_summaries(user_id, chat_id);
CREATE INDEX idx_chat_summaries_chat_id ON chat_summaries(chat_id);
```

---

## 🔌 API Endpoints

### Authentication Routes (`/auth`)
```python
POST /auth/register          # User registration
POST /auth/login            # User authentication
POST /auth/refresh          # Token refresh
GET  /auth/me               # Get current user info
```

### Check-in Routes (`/checkin`)
```python
POST /checkin/morning       # Submit morning check-in
POST /checkin/evening       # Submit evening check-in
GET  /checkin/today         # Get today's check-ins
GET  /checkin/history       # Get check-in history
```

### Chat Summary Routes (`/chat_summary`)
```python
POST /chat_summary/create   # Create a new chat summary
GET  /chat_summary/user/{user_id} # Get all chat summaries for a user
GET  /chat_summary/chat/{chat_id} # Get a specific chat summary by ID
```

### Agent Routes (`/agent`)
```python
WebSocket /agent/chat/{chat_id}  # Real-time conversation
GET       /agent/chat/summary/{chat_id}  # Get chat summary (auto-generated and saved)
```

---

## 🔌 WebSocket Implementation

### Connection URL Format
```
ws://localhost:8000/agent/chat/{user_id}_{session_id}_{checkin_type}?token={jwt_token}
```

### Chat ID Structure
- **Format**: `{user_id}_{session_id}_{checkin_type}`
- **Examples**:
  - `2_5_0` = User 2, Session 5, Morning check-in
  - `2_5_1` = User 2, Session 5, Evening check-in

### Message Flow
1. **Connection**: WebSocket handshake with JWT validation
2. **Context Retrieval**: Database fetch for user and check-in data
3. **Agent Selection**: 
   - **Greeting Agent**: First-time connections
   - **Conversation Agent**: Ongoing conversations
4. **Response Generation**: LLM processes context and generates response
5. **Message Delivery**: Complete response sent via WebSocket
6. **Context Storage**: Conversation stored in Redis with TTL

### WebSocket States
- **Connecting**: Initial connection attempt
- **Connected**: Active conversation
- **Disconnected**: Connection closed
- **Error**: Connection or processing error

---

## 📝 Chat Summary Management

### Automatic Summary Generation
The system automatically generates and stores chat summaries for every conversation session:

1. **Summary Creation**: When a user requests a chat summary via `/agent/chat/summary/{chat_id}`
2. **LLM Processing**: GPT-4o generates a comprehensive summary based on:
   - User's check-in context (morning/evening data)
   - Complete conversation history from Redis
3. **Database Storage**: Summary is automatically saved to `chat_summaries` table
4. **Upsert Logic**: If a summary already exists for a `chat_id`, it updates the existing record

### Summary Data Structure
```json
{
  "id": 1,
  "user_id": 2,
  "chat_id": "2_5_0",
  "summary": "User reported feeling anxious in the morning...",
  "created_at": "2025-01-27T10:00:00Z",
  "updated_at": "2025-01-27T10:00:00Z"
}
```

### Summary Benefits
- **Persistent Storage**: Summaries are permanently stored in PostgreSQL
- **Quick Retrieval**: No need to regenerate summaries from conversation history
- **User Privacy**: Users can only access their own summaries
- **Analytics Ready**: Summaries can be used for mental health trend analysis
- **Efficient Storage**: Text summaries are much smaller than full conversation logs

### Summary Generation Process
```
User Request → Context Retrieval → LLM Processing → Summary Generation → Database Storage → Response
     ↓              ↓                ↓                ↓                ↓              ↓
  /summary      Check-in +      GPT-4o API      AI-generated    PostgreSQL      JSON Response
  endpoint      Conversation     Call           Summary         Insert/Update
```

---

## 🔧 Services

### Database Service (`DatabaseService`)
```python
class DatabaseService:
    @staticmethod
    def get_last_daily_checkin(db: Session, user_id: int, is_morning: bool)
    @staticmethod
    def get_today_checkins(db: Session, user_id: int)
    @staticmethod
    def get_checkin_history(db: Session, user_id: int, checkin_type: str, limit: int)
    @staticmethod
    def save_chat_summary(db: Session, user_id: int, chat_id: str, summary: str)
    @staticmethod
    def get_chat_summary(db: Session, chat_id: str)
    @staticmethod
    def get_user_chat_summaries(db: Session, user_id: int, limit: int)
    @staticmethod
    def delete_chat_summary(db: Session, chat_id: str, user_id: int)
```

**Key Features**:
- User context retrieval with JOIN operations
- Gender conversion (0→Male, 1→Female, 2→Third gender)
- Optimized queries with proper indexing
- Error handling and logging
- **Chat summary management with upsert functionality**
- **User-specific summary retrieval and deletion**

### Redis Service (`RedisService`)
```python
class RedisService:
    def append_conversation(self, key: str, user_message: str, agent_response: str, expire_seconds: int)
    def get_conversation_context(self, key: str) -> str
    def key_exists(self, key: str) -> bool
```

**Key Features**:
- Sliding window conversation storage (max 20 conversations)
- Automatic TTL expiration (4 hours default)
- Conversation context retrieval
- Connection health monitoring

### LLM Service (`LLMService`)
```python
class LLMService:
    async def chatbot_response(self, messages)
```

**Key Features**:
- OpenAI GPT-4o integration via LangChain
- Async response handling
- Comprehensive error logging
- Fallback error messages

### WebSocket Service (`WebSocketService`)
```python
class WebSocketService:
    async def connect(self, websocket: WebSocket, chat_id: str, user: User)
    def disconnect(self, chat_id: str)
    def is_connected(self, chat_id: str) -> bool
```

**Key Features**:
- Connection management
- User session tracking
- Connection health monitoring

### Authentication Service (`AuthService`)
```python
class AuthService:
    def verify_password(self, plain_password: str, hashed_password: str) -> bool
    def get_password_hash(self, password: str) -> str
    def create_access_token(self, data: dict, expires_delta: timedelta)
    def verify_token(self, token: str) -> dict
```

**Key Features**:
- Password hashing with bcrypt
- JWT token generation and validation
- Secure password verification

---

## 🔐 Authentication & Security

### JWT Token Structure
```json
{
  "sub": "user@example.com",
  "exp": 1755239430,
  "iat": 1755153030
}
```

### Security Features
- **Password Hashing**: bcrypt with salt
- **JWT Tokens**: Secure session management
- **Token Expiration**: Configurable TTL
- **Input Validation**: Comprehensive request validation
- **SQL Injection Protection**: SQLAlchemy ORM
- **CORS Configuration**: Configurable cross-origin settings

### Authentication Flow
1. **Login**: User credentials → JWT token
2. **WebSocket Connection**: Token validation in query parameters
3. **Session Management**: Token-based user identification
4. **Access Control**: Role-based permissions (user/admin/provider)

---

## ⚙️ Configuration

### Environment Variables
```bash
# Database
DATABASE_URL=postgresql://user:password@localhost/mentalhealthbot

# Redis
REDIS_URL=redis://localhost:6379
REDIS_MAX_CONNECTIONS=10
REDIS_SOCKET_TIMEOUT=5
REDIS_SOCKET_CONNECT_TIMEOUT=5

# OpenAI
OPENAI_API_KEY=your_openai_api_key

# JWT
SECRET_KEY=your_secret_key
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Server
HOST=0.0.0.0
PORT=8000
```

### Configuration Class
```python
class Settings(BaseSettings):
    database_url: str
    redis_url: str
    openai_api_key: str
    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
```

---

## 🚀 Deployment

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Redis 6+
- OpenAI API key

### Installation Steps
```bash
# 1. Clone repository
git clone <repository_url>
cd MentalHealthBot

# 2. Create virtual environment
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or
.venv\Scripts\activate     # Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Set environment variables
export DATABASE_URL="postgresql://..."
export OPENAI_API_KEY="..."

# 5. Run database migrations
alembic upgrade head

# 6. Start the server
uvicorn main:app --host 0.0.0.0 --port 8000
```

**Note**: The latest migration (`create_chat_summaries_table`) creates the new `chat_summaries` table for storing conversation summaries. Make sure to run `alembic upgrade head` to apply all migrations.

### Docker Deployment
```dockerfile
FROM python:3.9-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## 🧪 Testing

### Manual Testing
1. **WebSocket Connection**: Use online WebSocket testers
2. **API Endpoints**: Test with Postman or curl
3. **Frontend Interface**: Use the provided HTML interface

### Test Commands
```bash
# Test database service
python -m services.db_service

# Test WebSocket connection
# Use: ws://localhost:8000/agent/chat/2_5_0?token={jwt_token}

# Test API endpoints
curl -X POST "http://localhost:8000/auth/login" \
     -H "Content-Type: application/json" \
     -d '{"email":"user@example.com","password":"password"}'
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. WebSocket Connection Errors
**Symptoms**: `Cannot call "send" once a close message has been sent`
**Solution**: Added WebSocket state checking before sending messages

#### 2. Prompt Formatting Errors
**Symptoms**: `Error formatting greeting prompt: '\n  "first_name"'`
**Solution**: Replaced `.format()` with string replacement to avoid conflicts

#### 3. Import Issues
**Symptoms**: `RuntimeWarning: 'services.db_service' found in sys.modules`
**Solution**: Fixed import paths and removed sys.path manipulation

#### 4. LLM Streaming Issues
**Symptoms**: Word-by-word message delivery
**Solution**: Changed from streaming to single response delivery

### Debug Logging
The system includes comprehensive logging with:
- **Agent identification**: 🤖 [GREETING AGENT], 🤖 [CONVERSATION AGENT]
- **Status indicators**: ✅ Success, ❌ Error, ⚠️ Warning, 🔄 Processing
- **Context information**: User data, check-in context, conversation history
- **Performance metrics**: Response times, character counts

### Log Levels
- **INFO**: Normal operations and status updates
- **WARNING**: Non-critical issues and fallbacks
- **ERROR**: Critical errors and exceptions
- **DEBUG**: Detailed debugging information

---

## ⚡ Performance & Scalability

### Performance Optimizations
- **Database Indexing**: Optimized queries for user and check-in data
- **Redis Caching**: Fast conversation context retrieval
- **Connection Pooling**: Efficient database and Redis connections
- **Async Processing**: Non-blocking WebSocket and LLM operations

### Scalability Considerations
- **Horizontal Scaling**: Stateless design allows multiple instances
- **Load Balancing**: WebSocket connections can be distributed
- **Database Sharding**: User data can be partitioned by user ID
- **Redis Clustering**: Multiple Redis instances for high availability

---

## 🔮 Future Enhancements

### Planned Features
- **Multi-language Support**: Internationalization for global users
- **Advanced Analytics**: User engagement and mental health trends
- **Integration APIs**: Third-party mental health service connections
- **Mobile App**: Native iOS and Android applications
- **Voice Support**: Speech-to-text and text-to-speech capabilities
- **Chat Summary Analytics**: Trend analysis and insights from conversation summaries
- **Summary Export**: PDF/CSV export of chat summaries for users and providers

### Technical Improvements
- **GraphQL API**: More flexible data querying
- **Microservices**: Service decomposition for better scalability
- **Event Streaming**: Real-time analytics and monitoring
- **Machine Learning**: Custom model training for better responses

---

## 📚 Additional Resources

### Documentation
- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Redis Documentation**: https://redis.io/documentation
- **OpenAI API Documentation**: https://platform.openai.com/docs

### Code Structure
```
MentalHealthBot/
├── alembic/                 # Database migrations
├── models/                  # Data models
├── routers/                 # API endpoints
├── services/                # Business logic
├── config.py               # Configuration
├── main.py                 # Application entry point
├── prompt_registry.py      # LLM prompts
└── requirements.txt        # Dependencies
```

---

## 🎯 Quick Start Guide

### 1. Setup Environment
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure Database
```bash
# Set environment variables
export DATABASE_URL="postgresql://user:password@localhost/mentalhealthbot"
export OPENAI_API_KEY="your_openai_api_key"

# Run migrations
alembic upgrade head
```

### 3. Start Server
```bash
# Start the application
uvicorn main:app --reload
```

### 4. Test WebSocket
```bash
# Use WebSocket URL
ws://localhost:8000/agent/chat/2_5_0?token={jwt_token}
```

### 5. Use Frontend
- Open `websocket_test.html` in your browser
- Enter your JWT token
- Start chatting with the mental health bot!

---

This documentation provides a comprehensive overview of the Mental Health Bot project, covering all technical aspects from architecture to deployment. The system is designed to be scalable, maintainable, and secure while providing a seamless user experience for mental health support.
