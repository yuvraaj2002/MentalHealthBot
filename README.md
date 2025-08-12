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
- `GET /api/v1/example` - Example endpoint
- `GET /api/v1/example/{item_id}` - Example endpoint with parameter

## Development

- The application uses FastAPI with automatic API documentation
- Access the interactive API docs at: http://localhost:8000/docs
- Access the alternative API docs at: http://localhost:8000/redoc
