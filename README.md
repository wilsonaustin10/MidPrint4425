# MidPrint - Browser Automation Agent

MidPrint is an AI-powered browser automation agent that performs web tasks using natural language instructions.

## Project Structure

The project consists of two main components:

- **Backend**: Python-based service with Playwright for browser automation and LangChain for LLM integration
- **Frontend**: Next.js web application with chat interface and embedded browser view

## Setup Instructions

### Prerequisites

- Python 3.11+
- Node.js 18+
- npm or yarn

### Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Install Playwright browsers:
   ```bash
   playwright install
   ```

5. Set up environment variables:
   - Copy or modify `.env` as needed
   - Ensure your Anthropic API key is set

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Set up environment variables:
   - Copy `.env.example` to `.env.local` if needed

## Running the Application

### Backend

Start the backend server:
```bash
cd backend
python -m app.main
```

The backend API will be available at http://localhost:8000

### Frontend

Start the frontend development server:
```bash
cd frontend
npm run dev
```

The frontend will be available at http://localhost:3000

## Features

- Natural language instruction processing
- Browser automation with visual feedback
- Chat interface for sending commands
- Embedded browser view
- DOM processing for intelligent interactions

## License

[MIT License](LICENSE)