# Mental Health Bot API

A FastAPI-based application for mental health bot services.

## Project Structure

```
MentalHealthBot/
├── models/              # Data models and schemas
│   ├── __init__.py
│   └── base.py         # Base response models
├── routers/             # API route definitions
│   ├── __init__.py
│   └── api.py          # Main API router
├── services/            # Business logic layer
│   ├── __init__.py
│   └── example_service.py  # Example service implementation
├── main.py              # FastAPI application entry point
├── requirements.txt     # Python dependencies
└── README.md           # This file
```

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   python main.py
   ```

   Or using uvicorn directly:
   ```bash
   uvicorn main:app --reload
   ```

## API Endpoints

- `GET /` - Welcome message
- `GET /health` - Health check

## Authentication

The Mental Health Bot API uses JWT (JSON Web Token) based authentication. All protected endpoints require a valid JWT token in the Authorization header.

### Authentication Flow

1. **User Registration** → Get access token
2. **User Login** → Get access token  
3. **Use access token** → Access protected endpoints
4. **Token expires** → Re-authenticate

### Endpoints

#### 1. User Registration
**POST** `/auth/signup`

Creates a new user account and returns an access token.

**Request Body:**
```json
{
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "user": {
    "id": 1,
    "first_name": "John",
    "last_name": "Doe",
    "username": "johndoe",
    "email": "john.doe@example.com",
    "age": null,
    "gender": null,
    "is_active": true,
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z"
  },
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 2. User Login
**POST** `/auth/login`

Authenticates existing user and returns access token.

**Request Body:**
```json
{
  "email": "john.doe@example.com",
  "password": "securepassword123"
}
```

**Response (200):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### 3. Get Current User Info
**GET** `/auth/me`

Returns information about the currently authenticated user.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "id": 1,
  "first_name": "John",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "age": null,
  "gender": null,
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:30:00Z"
}
```

#### 4. Update User Profile
**PUT** `/auth/me`

Updates the current user's profile information.

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "first_name": "Johnny",
  "age": 25,
  "gender": "Male"
}
```

**Response (200):**
```json
{
  "id": 1,
  "first_name": "Johnny",
  "last_name": "Doe",
  "username": "johndoe",
  "email": "john.doe@example.com",
  "age": 25,
  "gender": "Male",
  "is_active": true,
  "created_at": "2024-01-15T10:30:00Z",
  "updated_at": "2024-01-15T10:35:00Z"
}
```

#### 5. User Logout
**POST** `/auth/logout`

Logs out the current user (client should discard the token).

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200):**
```json
{
  "message": "Successfully logged out"
}
```

### Using JWT Tokens

#### Setting Authorization Header
In Postman or any HTTP client, add the following header:
```
Authorization: Bearer <your_jwt_token>
```

#### Token Expiration
- **Access Token**: Expires after 30 minutes (configurable)
- **Refresh Token**: Not implemented yet (future feature)

### Error Responses

#### 400 Bad Request
```json
{
  "detail": "Email already registered"
}
```

#### 401 Unauthorized
```json
{
  "detail": "Could not validate credentials"
}
```

#### 403 Forbidden
```json
{
  "detail": "Not enough permissions"
}
```

### Postman Collection Example

**Environment Variables:**
```
base_url: http://localhost:8000
auth_token: <leave_empty_initially>
```

**Collection Setup:**
1. Create a new collection called "Mental Health Bot API"
2. Set the base URL variable
3. Add a "Pre-request Script" to automatically add the auth token:

```javascript
// Pre-request Script for protected endpoints
if (pm.environment.get("auth_token")) {
    pm.request.headers.add({
        key: "Authorization",
        value: "Bearer " + pm.environment.get("auth_token")
    });
}
```

**Test Script for Login/Register:**
```javascript
// Test Script to automatically save the token
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.access_token) {
        pm.environment.set("auth_token", response.access_token);
    }
}
```

### Security Features

- **Password Hashing**: Uses bcrypt with salt
- **JWT Signing**: HMAC-SHA256 algorithm
- **CORS Protection**: Configurable origins
- **Rate Limiting**: Configurable request limits
- **Input Validation**: Pydantic model validation
- **SQL Injection Protection**: SQLAlchemy ORM

## Daily Check-ins

The Mental Health Bot API includes a comprehensive daily check-in system to help users track their mental health patterns throughout the day.

### Check-in System Overview

The system supports two types of daily check-ins:
- **Morning Check-ins**: Track sleep quality, body sensations, energy levels, and mental state
- **Evening Check-ins**: Monitor emotional patterns, overwhelm levels, and meaningful moments

### Check-in Endpoints

#### 1. Morning Check-in
**POST** `/checkin/morning`

Records a morning mental health check-in with sleep and energy metrics.

**Request Body:**
```json
{
  "sleep_quality": "good",
  "body_sensation": "refreshed",
  "energy_level": "high",
  "mental_state": "clear",
  "executive_task": "sharp"
}
```

**Response (200):**
```json
{
  "message": "Morning check-in recorded successfully",
  "checkin_id": 1,
  "checkin_type": "morning",
  "timestamp": "2024-01-15T08:00:00Z",
  "user_id": 123
}
```

**Field Descriptions:**
- `sleep_quality`: Quality of sleep (excellent, good, fair, poor)
- `body_sensation`: How the body feels (refreshed, tired, energized, achy)
- `energy_level`: Current energy level (high, medium, low, exhausted)
- `mental_state`: Mental clarity (clear, foggy, focused, scattered)
- `executive_task`: Ability to perform tasks (sharp, struggling, capable, overwhelmed)

#### 2. Evening Check-in
**POST** `/checkin/evening`

Records an evening mental health check-in with emotional and environmental metrics.

**Request Body:**
```json
{
  "emotion_category": "contentment",
  "overwhelm_amount": "none",
  "emotion_in_moment": "grateful",
  "surroundings_impact": "positive",
  "meaningful_moments_quantity": "several"
}
```

**Response (200):**
```json
{
  "message": "Evening check-in recorded successfully",
  "checkin_id": 2,
  "checkin_type": "evening",
  "timestamp": "2024-01-15T20:00:00Z",
  "user_id": 123
}
```

**Field Descriptions:**
- `emotion_category`: Primary emotion (joy, sadness, anger, anxiety, contentment)
- `overwhelm_amount`: Level of overwhelm (none, slight, moderate, high, extreme)
- `emotion_in_moment`: Current emotion (calm, stressed, grateful, frustrated)
- `surroundings_impact`: Impact of environment (positive, negative, neutral, distracting)
- `meaningful_moments_quantity`: Number of meaningful moments (none, few, several, many)

#### 3. Get Check-in History
**GET** `/checkin/history?limit=30`

Retrieves the user's check-in history with optional limit parameter.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200):**
```json
{
  "user_id": 123,
  "checkins": [
    {
      "id": 1,
      "checkin_type": "morning",
      "checkin_time": "2024-01-15T08:00:00Z",
      "morning_data": {
        "sleep_quality": "good",
        "body_sensation": "refreshed",
        "energy_level": "high",
        "mental_state": "clear",
        "executive_task": "sharp"
      },
      "evening_data": null
    },
    {
      "id": 2,
      "checkin_type": "evening",
      "checkin_time": "2024-01-15T20:00:00Z",
      "morning_data": null,
      "evening_data": {
        "emotion_category": "contentment",
        "overwhelm_amount": "none",
        "emotion_in_moment": "grateful",
        "surroundings_impact": "positive",
        "meaningful_moments_quantity": "several"
      }
    }
  ],
  "total_count": 2
}
```

#### 4. Get Today's Check-ins
**GET** `/checkin/today`

Retrieves today's check-ins for the current user.

**Headers:**
```
Authorization: Bearer <your_jwt_token>
```

**Response (200):**
```json
{
  "user_id": 123,
  "date": "2024-01-15",
  "morning_checkin": {
    "id": 1,
    "sleep_quality": "good",
    "body_sensation": "refreshed",
    "energy_level": "high",
    "mental_state": "clear",
    "executive_task": "sharp"
  },
  "evening_checkin": {
    "id": 2,
    "emotion_category": "contentment",
    "overwhelm_amount": "none",
    "emotion_in_moment": "grateful",
    "surroundings_impact": "positive",
    "meaningful_moments_quantity": "several"
  },
  "total_checkins": 2
}
```

### Using Check-ins in Postman

#### Environment Variables
```
base_url: http://localhost:8000
auth_token: <your_jwt_token>
```

#### Collection Setup
1. Create a new collection called "Mental Health Check-ins"
2. Set the base URL variable
3. Add Authorization header with Bearer token

#### Test Scripts
```javascript
// Test Script to automatically save checkin_id
if (pm.response.code === 200) {
    const response = pm.response.json();
    if (response.checkin_id) {
        pm.environment.set("last_checkin_id", response.checkin_id);
    }
}
```

### Check-in Workflow

#### Morning Routine
1. **Wake up** and assess how you feel
2. **Record morning check-in** with sleep and energy metrics
3. **Use insights** to plan your day accordingly

#### Evening Routine
1. **Reflect** on your day
2. **Record evening check-in** with emotional patterns
3. **Review patterns** to understand your mental health trends

### Data Insights

The check-in system provides valuable insights:
- **Sleep patterns** and their impact on daily functioning
- **Energy level trends** throughout the week
- **Emotional patterns** and triggers
- **Overwhelm cycles** and stress management
- **Meaningful moments** tracking for gratitude practice

### Database Structure

The system uses a single `checkins` table with a `checkin_type` field:
- **Efficient queries** for both morning and evening data
- **Easy analytics** across different time periods
- **Flexible schema** for future check-in types
- **Data integrity** with proper foreign key relationships

## Conversational AI Agents

The Mental Health Bot features an intelligent conversational system with two specialized agents that work together to provide personalized mental health support.

### Agent Architecture

The system employs a **dual-agent approach** that adapts based on the conversation context:

1. **Greeting Agent**: Handles initial interactions and first-time conversations
2. **Conversational Agent**: Manages ongoing conversations and follow-up interactions

### How Agents Work

#### Greeting Agent
- **Trigger**: Activated when a user starts a new conversation (no existing chat context)
- **Purpose**: Creates personalized greeting messages based on the user's check-in data
- **Context**: Uses the user's most recent daily check-in information
- **Behavior**: Generates warm, contextual greetings that acknowledge the user's current mental state

#### Conversational Agent
- **Trigger**: Activated for ongoing conversations (existing chat context in Redis)
- **Purpose**: Maintains conversation flow and provides contextual responses
- **Context**: Uses both check-in data and conversation history
- **Behavior**: Responds to user messages while maintaining conversation continuity

### Sliding Window Conversational Context

The system implements an intelligent **sliding window approach** for managing conversation memory:

#### Key Features
- **Memory Limit**: Maintains only the last 20 conversation exchanges
- **Automatic Cleanup**: Old conversations are automatically removed when the limit is exceeded
- **Context Preservation**: Both user messages and agent responses are stored together
- **TTL Management**: All conversation data automatically expires after 4 hours

#### How It Works
1. **New Conversation**: Greeting agent creates initial response and stores it
2. **Ongoing Chat**: Each user message and agent response pair is appended to the context
3. **Sliding Window**: When exceeding 20 conversations, oldest exchanges are automatically removed
4. **Memory Efficiency**: Prevents unlimited memory growth while maintaining relevant context
5. **Auto-Expiration**: Redis keys automatically expire after 4 hours for cleanup

#### Context Structure
```
User: [User's message]
Agent: [Agent's response]

User: [Next user message]
Agent: [Next agent response]

... (up to 20 exchanges)
```

#### Benefits
- **Relevant Context**: Always uses the most recent and relevant conversation history
- **Memory Management**: Prevents memory leaks and excessive storage usage
- **Performance**: Maintains optimal response times with manageable context size
- **User Experience**: Provides consistent, contextual responses throughout the conversation
- **Scalability**: Efficiently handles multiple concurrent conversations

### WebSocket Communication

The conversational system operates through WebSocket connections for real-time interaction:

#### Endpoint
```
WS /chat/{chat_id}
```

#### Chat ID Format
- **Morning Check-ins**: `{user_id}_{date}_0` (e.g., `123_2024-01-15_0`)
- **Evening Check-ins**: `{user_id}_{date}_1` (e.g., `123_2024-01-15_1`)

#### Message Flow
1. **Connection**: User connects via WebSocket with chat ID
2. **Context Loading**: System loads check-in data and conversation history
3. **Agent Selection**: Greeting or conversational agent is selected based on context
4. **Response Generation**: Agent generates contextual response using LLM
5. **Streaming**: Response is streamed chunk-by-chunk to the user
6. **Context Update**: New conversation is stored with sliding window management

### Integration with Check-in System

The conversational agents seamlessly integrate with the daily check-in system:

- **Contextual Responses**: Agents use check-in data to personalize interactions
- **Time-Aware**: Different behavior for morning vs. evening conversations
- **Data-Driven**: Responses are informed by actual user mental health metrics
- **Proactive Support**: Agents can reference check-in patterns for better assistance

### Best Practices

1. **Regular Check-ins**: Complete daily check-ins for better agent context
2. **Consistent Timing**: Use similar times for check-ins to establish patterns
3. **Honest Responses**: Provide accurate check-in data for personalized support
4. **Engagement**: Regular conversation helps agents learn your patterns
5. **Context Awareness**: Agents remember your conversation style and preferences

## Conversational AI Agents

The Mental Health Bot features an intelligent conversational system with two specialized agents that work together to provide personalized mental health support.

### Agent Architecture

The system employs a **dual-agent approach** that adapts based on the conversation context:

1. **Greeting Agent**: Handles initial interactions and first-time conversations
2. **Conversational Agent**: Manages ongoing conversations and follow-up interactions

### How Agents Work

#### Greeting Agent
- **Trigger**: Activated when a user starts a new conversation (no existing chat context)
- **Purpose**: Creates personalized greeting messages based on the user's check-in data
- **Context**: Uses the user's most recent daily check-in information
- **Behavior**: Generates warm, contextual greetings that acknowledge the user's current mental state

#### Conversational Agent
- **Trigger**: Activated for ongoing conversations (existing chat context in Redis)
- **Purpose**: Maintains conversation flow and provides contextual responses
- **Context**: Uses both check-in data and conversation history
- **Behavior**: Responds to user messages while maintaining conversation continuity

### Sliding Window Conversational Context

The system implements an intelligent **sliding window approach** for managing conversation memory:

#### Key Features
- **Memory Limit**: Maintains only the last 20 conversation exchanges
- **Automatic Cleanup**: Old conversations are automatically removed when the limit is exceeded
- **Context Preservation**: Both user messages and agent responses are stored together
- **TTL Management**: All conversation data automatically expires after 4 hours

#### How It Works
1. **New Conversation**: Greeting agent creates initial response and stores it
2. **Ongoing Chat**: Each user message and agent response pair is appended to the context
3. **Sliding Window**: When exceeding 20 conversations, oldest exchanges are automatically removed
4. **Memory Efficiency**: Prevents unlimited memory growth while maintaining relevant context
5. **Auto-Expiration**: Redis keys automatically expire after 4 hours for cleanup

#### Context Structure
