# Ruth Frontend

React frontend for the Ruth civic engagement platform.

## Features

- **Authentication**: Login and registration with JWT tokens
- **Dashboard**: Quick access to all features
- **Representative Lookup**: Find representatives by address using Geocod.io
- **Voice Profiles**: Manage personalized writing styles
- **Letter Writing**: AI-powered letter generation
- **Delivery Management**: Send letters via fax, email, or print

## Tech Stack

- **React 18** - UI framework
- **Vite** - Build tool and dev server
- **React Router** - Client-side routing
- **Zustand** - State management
- **Axios** - HTTP client
- **Tailwind CSS** - Styling
- **Heroicons** - Icons

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env

# Edit .env and set your API URL
# VITE_API_URL=http://localhost:8000
```

### Development

```bash
# Start development server
npm run dev

# Server will run on http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Preview production build
npm run preview
```

## Project Structure

```
frontend/
├── public/              # Static assets (logo, favicon, tagline)
├── src/
│   ├── components/      # Reusable UI components
│   │   ├── Layout.jsx   # Main layout with navigation
│   │   └── PrivateRoute.jsx
│   ├── pages/           # Page components
│   │   ├── LoginPage.jsx
│   │   ├── RegisterPage.jsx
│   │   ├── DashboardPage.jsx
│   │   ├── RepresentativesPage.jsx
│   │   ├── VoiceProfilesPage.jsx
│   │   ├── NewLetterPage.jsx
│   │   ├── LettersPage.jsx
│   │   ├── LetterDetailPage.jsx
│   │   └── DeliveryPage.jsx
│   ├── services/        # API services
│   │   └── api.js       # API client and endpoints
│   ├── stores/          # Zustand stores
│   │   └── authStore.js # Authentication state
│   ├── App.jsx          # Main app component with routing
│   ├── main.jsx         # Application entry point
│   └── index.css        # Global styles
├── index.html           # HTML template
├── vite.config.js       # Vite configuration
├── tailwind.config.js   # Tailwind CSS configuration
└── package.json         # Dependencies and scripts
```

## API Integration

The frontend connects to the Ruth backend API:

- **Auth**: `/api/auth/*`
- **Representatives**: `/api/representatives/*`
- **Letters**: `/api/letters/*`
- **Delivery**: `/api/delivery/*`

API calls are handled through the centralized `services/api.js` module with automatic token refresh.

## Authentication

- JWT tokens stored in localStorage
- Automatic token refresh on 401 errors
- Protected routes redirect to login
- User state managed with Zustand

## Environment Variables

- `VITE_API_URL` - Backend API URL (default: http://localhost:8000)

## Development with Backend

Make sure the backend is running on port 8000:

```bash
# In backend directory
docker-compose up
```

The Vite dev server will proxy API requests to the backend.
