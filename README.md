# Emergency SOS and ROADSoS Platform

A comprehensive, full-stack emergency response and offline assistance platform designed to dispatch emergency services, track live location, and discover nearby critical resources with or without an active internet connection.

## System Architecture

The project is structured as a monorepo containing both the frontend client and the backend API service.

*   **Frontend**: Built with React 18 and Vite. It utilizes a mobile-first, brutalist monochrome design system with custom CSS to ensure high visibility, large touch targets, and performance under critical conditions.
*   **Backend**: Built with FastAPI and Python 3.10+. It handles high-throughput geolocation data, Redis-based caching, and persistent storage via PostgreSQL and SQLite fallbacks.

## Core Features

*   **Emergency Triggers (F-01, F-02, F-03)**: Single-tap SOS triggers categorized by emergency type (Medical, Injury, Safety). Dispatches nearest ambulance, police, or trauma center data.
*   **Live Location Tracking (F-04)**: Real-time streaming of geospatial coordinates to dispatch services.
*   **Nearest Services Lookup (F-07)**: Three-tier caching system (Redis -> Google Places API -> Local Database) to identify nearby hospitals, police stations, ambulances, towing services, and puncture shops.
*   **Offline Contacts Cache (F-08)**: Persistent local storage of critical emergency numbers, ensuring tap-to-call functionality even when network connectivity is lost.

## Technology Stack

### Backend Stack
*   **Framework**: FastAPI (Python)
*   **Database**: SQLAlchemy (Async), PostgreSQL (Production), SQLite (Local Fallback)
*   **Caching**: Upstash Redis (REST-based), In-Memory Mock (Fallback)
*   **Geospatial**: Haversine distance calculations
*   **Testing**: Pytest

### Frontend Stack
*   **Framework**: React 18, Vite
*   **Routing**: React Router DOM v6
*   **Styling**: Pure CSS (Custom Design System, Zero UI Libraries)
*   **Storage**: LocalStorage API for offline caching

## Project Structure

```text
sos-app/
├── backend/
│   ├── app/
│   │   ├── models/       # Database schemas and models
│   │   ├── routes/       # API endpoints (sos, location, services, cache)
│   │   ├── schemas/      # Pydantic validation models
│   │   ├── services/     # Business logic and external API integrations
│   │   ├── db.py         # Database connection and session management
│   │   └── redis.py      # Redis client and caching logic
│   ├── tests/            # Pytest test suites
│   ├── main.py           # Application entry point
│   └── requirements.txt  # Python dependencies
└── frontend/
    ├── src/
    │   ├── api/          # Fetch wrappers and backend communication
    │   ├── components/   # Reusable UI components
    │   ├── pages/        # Application views and routing endpoints
    │   ├── App.jsx       # Root component layout
    │   ├── main.jsx      # React DOM entry point
    │   └── index.css     # Global design system tokens
    ├── package.json      # Node dependencies
    └── vite.config.js    # Vite bundler configuration
```

## Setup and Installation

### Prerequisites
*   Python 3.10 or higher
*   Node.js 18 or higher
*   Git

### Backend Setup

1.  Navigate to the backend directory:
    ```bash
    cd backend
    ```
2.  Create and activate a virtual environment:
    ```bash
    python -m venv venv
    # Windows: venv\Scripts\activate
    # Linux/Mac: source venv/bin/activate
    ```
3.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4.  Configure environment variables in a `.env` file (see Configuration section).
5.  Start the FastAPI server:
    ```bash
    uvicorn main:app --reload --port 8000
    ```

### Frontend Setup

1.  Navigate to the frontend directory:
    ```bash
    cd frontend
    ```
2.  Install dependencies:
    ```bash
    npm install
    ```
3.  Configure environment variables (if required).
4.  Start the development server:
    ```bash
    npm run dev
    ```

## Configuration

Create a `.env` file in the `backend` directory. The application includes fallbacks, but the following variables are recommended for production environments:

```ini
# Database (Defaults to local SQLite if omitted)
DATABASE_URL=postgresql+asyncpg://user:password@host:port/dbname

# Upstash Redis (Defaults to in-memory dictionary if omitted)
UPSTASH_REDIS_REST_URL=your_upstash_url
UPSTASH_REDIS_REST_TOKEN=your_upstash_token

# External APIs
GOOGLE_PLACES_API_KEY=your_google_places_api_key

# Security
CORS_ORIGIN=http://localhost:5173
```

## Testing

The backend includes a comprehensive test suite covering all major endpoints and fallback mechanisms.

To run the tests:
```bash
cd backend
pytest
```
