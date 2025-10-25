# Ruth - AI-Powered Civic Engagement Platform

A comprehensive web application that empowers citizens to effectively communicate with their elected representatives through AI-generated letters, with support for multiple delivery methods (print, fax, email).

## Features

- **Smart Representative Lookup**: Find federal and state representatives using address geocoding
- **AI-Powered Letter Generation**: Create compelling, personalized letters based on news articles
- **Multiple Delivery Options**: Send letters via print (PDF), fax (SignalWire), or email (Mailgun)
- **Intelligent Caching**: Reduce API costs with smart caching of geocoding and representative data
- **User Account Management**: Secure authentication with JWT tokens
- **Responsive Web Interface**: Modern React frontend for seamless user experience

## Project Structure

```
ruth/
├── backend/               # FastAPI backend application
│   ├── app/
│   │   ├── api/          # API endpoints
│   │   ├── core/         # Core configuration and security
│   │   ├── models/       # SQLAlchemy database models
│   │   ├── services/     # External service integrations
│   │   └── main.py       # Application entry point
│   ├── migrations/       # Alembic database migrations
│   ├── requirements.txt  # Python dependencies
│   └── .env.example      # Environment variables template
├── frontend/             # React frontend application
├── docker/               # Docker configuration files
├── docker-compose.yml    # Docker Compose orchestration
└── README.md            # This file
```

## Prerequisites

- Docker and Docker Compose
- Python 3.11+ (for local development)
- Node.js 18+ (for frontend development)
- PostgreSQL 16 (or use Docker)
- Redis 7 (or use Docker)

## Quick Start with Docker

1. **Clone the repository**
   ```bash
   cd ruth
   ```

2. **Set up environment variables**
   ```bash
   cp backend/.env.example backend/.env
   # Edit backend/.env with your API keys and configuration
   ```

3. **Start the application with Docker Compose**
   ```bash
   docker-compose up -d
   ```

4. **Initialize the database**
   ```bash
   docker-compose exec backend alembic upgrade head
   ```

5. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/api/docs (development only)

## Local Development Setup

### Backend Setup

1. **Create Python virtual environment**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

4. **Start PostgreSQL and Redis**
   ```bash
   docker-compose up -d postgres redis
   ```

5. **Run database migrations**
   ```bash
   alembic upgrade head
   ```

6. **Start the development server**
   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

### Frontend Setup

1. **Install Node dependencies**
   ```bash
   cd frontend
   npm install
   ```

2. **Start the development server**
   ```bash
   npm start
   ```

## Environment Configuration

Key environment variables to configure in `backend/.env`:

### Required API Keys
- `OPENAI_API_KEY`: For AI letter generation
- `GEOCODIO_API_KEY`: For address geocoding and representative lookup
- `SECRET_KEY`: Application secret key (generate a strong random string)
- `JWT_SECRET_KEY`: JWT signing key (generate a strong random string)

### Optional Service Keys
- `MAILGUN_API_KEY`: For email delivery
- `MAILGUN_DOMAIN`: Your Mailgun domain
- `SIGNALWIRE_PROJECT_ID`: For fax delivery
- `SIGNALWIRE_TOKEN`: SignalWire authentication token
- `SIGNALWIRE_SPACE_URL`: Your SignalWire space URL

## Database Schema

The application uses PostgreSQL with the following main tables:

- **users**: User accounts and authentication
- **user_addresses**: Stored user addresses
- **geocoding_cache**: Cached geocoding results (30-day TTL)
- **representatives**: Cached representative information
- **letters**: Letter drafts and metadata
- **letter_recipients**: Personalized letters for each recipient
- **delivery_logs**: Delivery attempts and status tracking

## API Endpoints

### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/refresh` - Refresh JWT token

### Representatives
- `POST /api/representatives/lookup` - Find representatives by address
- `GET /api/representatives/{id}` - Get representative details

### Letters
- `POST /api/letters/draft` - Generate AI letter
- `GET /api/letters/{id}` - Get letter details
- `PUT /api/letters/{id}` - Update letter content

### Delivery
- `POST /api/delivery/pdf` - Generate PDF
- `POST /api/delivery/fax` - Send via fax
- `POST /api/delivery/email` - Send via email

## Docker Commands

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f [service_name]

# Stop all services
docker-compose down

# Reset database
docker-compose down -v
docker-compose up -d
docker-compose exec backend alembic upgrade head

# Access backend shell
docker-compose exec backend /bin/bash

# Run database migrations
docker-compose exec backend alembic upgrade head

# Create new migration
docker-compose exec backend alembic revision --autogenerate -m "Description"
```

## Development Workflow

1. **Backend Development**
   - Make changes to Python code
   - Server auto-reloads with changes (when using --reload)
   - Test endpoints at http://localhost:8000/api/docs

2. **Frontend Development**
   - Make changes to React code
   - Hot module replacement updates the browser automatically
   - View at http://localhost:3000

3. **Database Changes**
   - Modify models in `backend/app/models/`
   - Generate migration: `alembic revision --autogenerate -m "Description"`
   - Apply migration: `alembic upgrade head`

## Testing

```bash
# Run backend tests
cd backend
pytest

# Run with coverage
pytest --cov=app tests/

# Run frontend tests
cd frontend
npm test
```

## Production Deployment

For production deployment:

1. Update environment variables for production values
2. Set `DEBUG=False` in environment
3. Use production-grade servers (Gunicorn/Uvicorn for backend)
4. Build optimized frontend: `npm run build`
5. Serve static files with Nginx
6. Enable HTTPS with SSL certificates
7. Set up monitoring (Sentry, logging, etc.)

## Security Considerations

- All passwords are hashed using bcrypt
- JWT tokens for stateless authentication
- Rate limiting on authentication endpoints
- CORS properly configured
- Input validation and sanitization
- SQL injection prevention via parameterized queries
- XSS protection headers

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is proprietary software. All rights reserved.

## Support

For issues or questions, please create an issue in the GitHub repository.

## Acknowledgments

- Built with FastAPI, React, PostgreSQL, and Redis
- AI letter generation powered by OpenAI
- Address geocoding by Geocod.io
- Fax delivery via SignalWire
- Email delivery via Mailgun

---

**Note**: This application is currently in active development. Some features may not be fully implemented yet.