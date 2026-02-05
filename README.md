# Sharinmod - API Token Sharing Platform

A modern web platform for developers to share and consume API tokens through a sharing economy model.

## 🚀 Quick Start

### Prerequisites
- Docker Desktop
- Git

### Setup and Run

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd sharinmod
   ```

2. **Start all services**
   ```bash
   docker-compose up --build
   ```

3. **Access the application**
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs
   - Prometheus: http://localhost:9090
   - Grafana: http://localhost:3001

### Development

1. **Install dependencies** (for local development)
   ```bash
   # Backend
   cd backend
   pip install -r api/requirements.txt

   # Frontend
   cd frontend
   npm install
   ```

2. **Run tests**
   ```bash
   # From project root
   python -m pytest test_*.py -v
   ```

## 🏗️ Architecture

- **Backend**: FastAPI (Python) with PostgreSQL database
- **Frontend**: Next.js (TypeScript) with Tailwind CSS
- **Infrastructure**: Docker Compose with Redis, Prometheus, and Grafana
- **Authentication**: JWT tokens with Auth0 integration

## 📁 Project Structure

```
sharinmod/
├── backend/                 # FastAPI backend
│   ├── api/                # API application
│   ├── .env                # Environment variables
│   └── Dockerfile
├── frontend/               # Next.js frontend
│   ├── src/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml      # Multi-container setup
├── test_*.py              # Integration tests
└── README.md
```

## 🔧 Configuration

### Environment Variables

Copy `backend/.env.example` to `backend/.env` and configure:

- `DATABASE_URI`: PostgreSQL connection string
- `APP_SECRET_KEY`: JWT secret key
- `REDIS_DATABASE`: Redis connection string
- `AUTH0_*`: Auth0 authentication settings

### Database

The application uses PostgreSQL with the following configuration:
- Database: `sharinmod`
- User: `postgres`
- Password: `postgres`
- Port: `5432` (internal), `5454` (external)

## 🧪 Testing

Run the comprehensive test suite:

```bash
python -m pytest test_*.py -v
```

Tests cover:
- Project structure validation
- Docker configuration
- Environment setup
- Service integration

## 📊 Monitoring

- **Prometheus**: Metrics collection at http://localhost:9090
- **Grafana**: Dashboards at http://localhost:3001

## 🔒 Security

- JWT authentication with Auth0
- AES-256 encryption for sensitive data
- CORS configured for frontend-backend communication
- Environment variables for secrets management

## 🤝 Contributing

1. Follow the established coding standards
2. Add tests for new features
3. Update documentation as needed
4. Use conventional commit messages

## 📝 Changelog

### 2026-02-05
- Removed browser dark theme support in frontend CSS to ensure consistent light theme styling regardless of browser settings.

## 📝 License

This project is licensed under the MIT License.