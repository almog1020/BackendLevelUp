# LevelUp - Game Price Comparison Platform (Backend API)

RESTful API backend for the LevelUp game price comparison platform. This service aggregates game prices from multiple PC stores, manages user data, handles authentication, and provides real-time price updates.

## Project Overview

This is the backend service for a university project that solves the problem of scattered game pricing across multiple digital stores. The API handles data aggregation through ETL pipelines, user authentication, game catalog management, and real-time price comparisons.

## Problem Statement

### Technical Challenges Solved:
- **Data Aggregation**: Scraping and normalizing game data from multiple sources
- **Price Tracking**: Real-time monitoring and historical price data storage
- **User Management**: Secure authentication and authorization
- **Real-time Updates**: WebSocket support for live price notifications
- **Scalability**: Efficient database design for handling large datasets
- **Security**: JWT-based authentication with OAuth2 integration

### API Capabilities:
- Aggregate game prices from multiple stores
- Provide RESTful endpoints for frontend consumption
- Handle user authentication and authorization
- Manage game catalog, reviews, and purchases
- Execute ETL pipelines for data collection
- Deliver real-time updates via WebSockets

## Features

### Core API Features

1. **Authentication & Authorization**
   - JWT token-based authentication
   - Google OAuth2 integration
   - Role-based access control (User/Admin)
   - Secure password hashing (Argon2)
   - Session management

2. **User Management**
   - User registration and profile management
   - Password reset functionality
   - User activity tracking
   - Admin user management endpoints

3. **Game Catalog API**
   - Browse games with pagination
   - Search by title, genre, platform
   - Filter by multiple criteria
   - Get detailed game information
   - Price history tracking

4. **Price Comparison**
   - Multi-store price aggregation
   - Historical price data
   - Deal detection and highlighting
   - Real-time price updates

5. **Review System**
   - User reviews and ratings
   - Review CRUD operations
   - Review moderation endpoints
   - Rating aggregation

6. **Purchase & Wishlist**
   - User game library management
   - Wishlist functionality
   - Purchase history tracking

7. **Admin Panel APIs**
   - Game management (CRUD)
   - Genre management
   - Top deals management
   - User management
   - Review moderation

8. **ETL Pipeline**
   - Automated data collection from multiple sources
   - Data transformation and normalization
   - Price update scheduling
   - Error handling and logging

9. **Real-time Features**
   - WebSocket support for live updates
   - Price change notifications
   - Deal alerts

## Tech Stack

### Core Framework
- **FastAPI** - Modern, high-performance web framework
- **Python 3.14** - Programming language
- **Uvicorn** - ASGI server with hot reload

### Database & ORM
- **PostgreSQL** - Primary database (hosted on Aiven)
- **SQLModel** - SQL databases using Python objects
- **SQLAlchemy** - Database toolkit and ORM
- **Psycopg2** - PostgreSQL adapter

### Authentication & Security
- **Python-JOSE** - JWT implementation
- **PyJWT** - JSON Web Token handling
- **PWDLib (Argon2)** - Password hashing
- **Google-Auth** - Google OAuth integration

### Data Validation
- **Pydantic** - Data validation using Python type hints
- **Pydantic-Settings** - Settings management

### HTTP & WebSockets
- **HTTPX** - Async HTTP client for ETL
- **Requests** - HTTP library for web scraping
- **WebSockets** - Real-time communication

### Development & Deployment
- **Docker** - Containerization
- **Docker Compose** - Multi-container orchestration
- **Python-Dotenv** - Environment variable management
- **Python-Multipart** - File upload support

## Prerequisites

Before you begin, ensure you have the following installed:
- **Python 3.11+** (3.14 recommended)
- **PostgreSQL** (or access to PostgreSQL database)
- **Docker & Docker Compose** (optional, for containerized deployment)
- **Git** for version control

## Installation & Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd backendlevelup
```

### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Environment Variables
Create a `.env` file in the root directory:
```env
# Database
DATABASE_URL=postgresql://user:password@host:port/database?sslmode=require

# JWT Secret
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Google OAuth
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret

# CORS Origins
CORS_ORIGINS=http://localhost:5173,https://your-frontend-url.com

# API Settings
API_VERSION=v1
DEBUG=True
```

### 5. Run Database Migrations
The application automatically creates database tables on startup using SQLModel.

### 6. Start Development Server
```bash
python -m app.main
```

The API will be available at `http://localhost:8000`

API Documentation (Swagger UI): `http://localhost:8000/docs`
Alternative Documentation (ReDoc): `http://localhost:8000/redoc`

## Docker Deployment

### Build and Run with Docker Compose
```bash
docker-compose up --build
```

### Run in Detached Mode
```bash
docker-compose up -d
```

### Stop Services
```bash
docker-compose down
```

## Project Structure

```
backendlevelup/
├── app/
│   ├── routers/              # API route handlers
│   │   ├── auth/             # Authentication endpoints
│   │   ├── users/            # User management endpoints
│   │   ├── games/            # Game catalog endpoints
│   │   ├── reviews/          # Review endpoints
│   │   ├── purchases/        # Purchase/wishlist endpoints
│   │   └── admin/            # Admin panel endpoints
│   │       ├── games.py      # Admin game management
│   │       ├── genres.py     # Genre management
│   │       └── topdeals.py   # Deal management
│   ├── models/               # SQLModel database models
│   │   ├── users.py          # User model
│   │   ├── games.py          # Game model
│   │   ├── reviews.py        # Review model
│   │   ├── purchases.py      # Purchase model
│   │   └── token.py          # Token model
│   ├── logic/                # Business logic
│   │   ├── auth.py           # Authentication logic
│   │   ├── users.py          # User management logic
│   │   ├── games.py          # Game logic
│   │   ├── reviews.py        # Review logic
│   │   ├── purchases.py      # Purchase logic
│   │   ├── stores.py         # Store integration
│   │   └── etl.py            # ETL pipeline (27KB - data extraction)
│   ├── services/             # External services
│   ├── utilities/            # Helper utilities
│   ├── core/                 # Core configuration
│   ├── db.py                 # Database connection
│   ├── dependencies.py       # FastAPI dependencies
│   ├── schemas.py            # Pydantic schemas
│   ├── server.py             # FastAPI app instance
│   └── main.py               # Application entry point
├── requirements.txt          # Python dependencies
├── Dockerfile               # Docker configuration
├── docker-compose.yml       # Docker Compose setup
├── .env                     # Environment variables (not in git)
├── .gitignore              # Git ignore rules
└── README.md               # This file
```

## API Endpoints

### Authentication
- `POST /auth/register` - Register new user
- `POST /auth/login` - Login user (returns JWT token)
- `POST /auth/google` - Google OAuth login
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout user

### Users
- `GET /users/me` - Get current user profile
- `PUT /users/me` - Update user profile
- `DELETE /users/me` - Delete user account
- `GET /users/{user_id}` - Get user by ID (Admin)

### Games
- `GET /games` - Get all games (with pagination & filters)
- `GET /games/{game_id}` - Get game details
- `GET /games/search` - Search games
- `GET /games/genre/{genre}` - Filter by genre
- `GET /games/{game_id}/prices` - Get price history

### Reviews
- `GET /games/{game_id}/reviews` - Get game reviews
- `POST /games/{game_id}/reviews` - Create review
- `PUT /reviews/{review_id}` - Update review
- `DELETE /reviews/{review_id}` - Delete review

### Purchases/Wishlist
- `GET /purchases/library` - Get user's game library
- `POST /purchases/library` - Add game to library
- `GET /purchases/wishlist` - Get user's wishlist
- `POST /purchases/wishlist` - Add game to wishlist
- `DELETE /purchases/wishlist/{game_id}` - Remove from wishlist

### Admin Endpoints
- `POST /admin/games` - Create new game
- `PUT /admin/games/{game_id}` - Update game
- `DELETE /admin/games/{game_id}` - Delete game
- `GET /admin/users` - Get all users
- `PUT /admin/users/{user_id}` - Update user (ban/unban)
- `POST /admin/genres` - Create genre
- `POST /admin/topdeals` - Set top deal
- `GET /admin/reviews` - Get all reviews (moderation)
- `DELETE /admin/reviews/{review_id}` - Delete review (moderation)

### ETL & Data Sync
- `POST /admin/etl/trigger` - Trigger ETL pipeline
- `GET /admin/etl/status` - Check ETL status

## Database Schema

### Core Tables
- **users** - User accounts and profiles
- **games** - Game catalog
- **genres** - Game genres
- **stores** - Game store information
- **prices** - Price history tracking
- **reviews** - User reviews and ratings
- **purchases** - User game library
- **wishlist** - User wishlist
- **deals** - Top deals and promotions
- **tokens** - JWT token management

## Authentication Flow

1. User registers via `/auth/register` or Google OAuth
2. Credentials validated and hashed (Argon2)
3. User logs in via `/auth/login`
4. Server generates JWT access token
5. Client includes token in Authorization header: `Bearer <token>`
6. Protected endpoints validate token via dependency injection
7. Role-based access control applied for admin routes

## ETL Pipeline

The ETL (Extract, Transform, Load) pipeline handles data aggregation:

1. **Extract**: Scrape game data from multiple sources
   - Steam, Epic Games, GOG, etc.
   - Product information, prices, screenshots
   - Deal and discount data

2. **Transform**: Normalize and clean data
   - Standardize game titles
   - Convert prices to common currency
   - Validate and sanitize inputs

3. **Load**: Store in PostgreSQL database
   - Insert new games
   - Update existing prices
   - Track price history
   - Update deal status

## Real-time Features

WebSocket endpoints for real-time updates:
- Price change notifications
- New deal alerts
- Review updates

## Security Best Practices

- **Password Hashing**: Argon2 algorithm
- **JWT Tokens**: Secure token generation and validation
- **CORS**: Configured for specific origins
- **SQL Injection**: Protected via SQLModel/SQLAlchemy ORM
- **Input Validation**: Pydantic models validate all inputs
- **Rate Limiting**: (To be implemented)
- **HTTPS**: Required in production

## Development Guidelines

### Code Style
- Follow PEP 8 style guide
- Use type hints for all functions
- Document complex logic with docstrings
- Keep functions small and focused

### API Design
- RESTful endpoint naming
- Proper HTTP status codes
- Consistent error responses
- Versioned API routes

### Database
- Use SQLModel for type-safe queries
- Implement proper indexes for performance
- Use migrations for schema changes
- Handle transactions appropriately

### Testing
- Unit tests for business logic
- Integration tests for endpoints
- Test authentication flows
- Mock external services

## Running Tests

```bash
pytest
```

## API Documentation

FastAPI automatically generates interactive API documentation:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Performance Optimization

- Database connection pooling
- Query optimization with indexes
- Async operations for I/O-bound tasks
- Response caching (Redis - to be implemented)
- Pagination for large datasets

## Monitoring & Logging

- Uvicorn access logs
- Application error logging
- Database query logging (SQLAlchemy echo)
- ETL pipeline logs

## Known Issues & Future Improvements

- [ ] Implement Redis caching for frequently accessed data
- [ ] Add rate limiting middleware
- [ ] Implement comprehensive test coverage
- [ ] Add API versioning
- [ ] Set up CI/CD pipeline
- [ ] Implement email notifications
- [ ] Add more game stores to ETL pipeline
- [ ] Implement GraphQL endpoint
- [ ] Add API analytics

## Environment Setup

### Local Development
```bash
python -m app.main
```

### Production
```bash
uvicorn app.server:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker Production
```bash
docker-compose -f docker-compose.prod.yml up -d
```

## Troubleshooting

### Database Connection Issues
- Verify DATABASE_URL in .env
- Check PostgreSQL is running
- Verify network connectivity
- Check SSL mode requirements

### Authentication Errors
- Verify SECRET_KEY is set
- Check token expiration
- Validate Google OAuth credentials

### ETL Pipeline Failures
- Check external API rate limits
- Verify network connectivity
- Review error logs
- Check data validation rules

## Contributing

This is a university project. If you're a team member:
1. Create a feature branch from main
2. Implement your changes
3. Write/update tests
4. Submit a pull request
5. Request code review

## Team

University Project - 2026 CLOUD DEV Workshop

## License

This is a university project created for educational purposes.

---

**Note**: This backend API was developed as part of a university course to demonstrate:
- RESTful API design
- Authentication & authorization
- Database design and ORM usage
- ETL pipeline implementation
- Docker containerization
- FastAPI framework proficiency
- Async Python programming
- Security best practices
