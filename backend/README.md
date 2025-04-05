# MidPrint Backend

Backend server for the MidPrint browser automation agent using FastAPI and Playwright.

## Setup Instructions

1. Ensure Python 3.11+ is installed

2. Create a virtual environment:
   ```
   python -m venv venv
   ```

3. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`

4. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

5. Install Playwright browsers:
   ```
   playwright install
   ```

6. Configure environment variables:
   - Copy `.env.example` to `.env` (if available)
   - Edit `.env` to include your API keys and settings

## Running the Server

Start the development server:
```
cd backend
python -m app.main
```

The API will be available at http://localhost:8000

API documentation is available at:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Project Structure

```
backend/
├── app/
│   ├── api/            # API routes and endpoints
│   ├── core/           # Core application components
│   ├── services/       # Services like browser automation
│   └── main.py         # Application entry point
├── tests/              # Unit and integration tests
├── .env                # Environment variables
├── requirements.txt    # Python dependencies
└── README.md           # This file
``` 