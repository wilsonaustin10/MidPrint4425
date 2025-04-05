# MidPrint Frontend

Next.js frontend for the MidPrint browser automation agent.

## Setup Instructions

1. Ensure Node.js (v18+) is installed

2. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

3. Configure environment variables (if needed):
   - Copy `.env.example` to `.env.local` (if available)
   - Edit `.env.local` to include your API endpoints and settings

## Running the Application

Start the development server:
```bash
npm run dev
```

The application will be available at http://localhost:3000

## Build for Production

```bash
npm run build
npm run start
```

## Project Structure

```
frontend/
├── src/
│   ├── app/            # Next.js 13 App Router
│   ├── components/     # Reusable UI components
│   ├── lib/            # Utilities and helper functions
│   └── styles/         # Global styles and CSS
├── public/             # Static assets
├── next.config.js      # Next.js configuration
├── tailwind.config.js  # Tailwind CSS configuration
├── tsconfig.json       # TypeScript configuration
└── README.md           # This file
```

## Features

- Chat interface for sending instructions to the agent
- Embedded browser view for watching the agent's actions
- Real-time updates of task execution
- Responsive design for desktop and mobile 