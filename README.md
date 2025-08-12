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

## Development

- The application uses FastAPI with automatic API documentation
- Access the interactive API docs at: http://localhost:8000/docs
- Access the alternative API docs at: http://localhost:8000/redoc
