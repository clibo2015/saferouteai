# SafeRouteAI - Technical Overview

## Product Description
SafeRouteAI is a mobile navigation app that provides real-time safety intelligence for drivers. The app analyzes crime data, hazard reports, and environmental factors to recommend the safest routes and alert users to potential dangers along their journey.

## Core Features

### Real-Time Safety Navigation
- Live route optimization based on safety scores
- Dynamic rerouting when hazards are detected
- Turn-by-turn navigation with safety alerts
- Visual safety heatmap overlay on maps

### Hazard Detection & Alerts
- Real-time crime hotspot identification
- User-reported hazard crowdsourcing
- Environmental hazard detection
- Proactive alerts before entering high-risk areas

### User Authentication & Personalization
- Secure user accounts with JWT authentication
- Journey history tracking
- Personalized safety preferences
- Saved locations and frequent routes

### Interactive Mapping
- Huawei Map Kit integration for accurate mapping
- Safety zone visualization with color-coded risk levels
- Hazard markers and incident reporting
- Real-time location tracking

## Technology Stack

### Frontend (Mobile App)
- **Framework**: React Native with Capacitor
- **Platform**: Android (with iOS capability)
- **UI Components**: Custom React components
- **State Management**: React hooks
- **Map Integration**: Huawei Map Kit SDK
- **Build Tools**: npm, Android Studio

### Backend (API Server)
- **Framework**: FastAPI (Python)
- **Server**: Uvicorn ASGI server
- **Reverse Proxy**: Nginx
- **Authentication**: JWT tokens with bcrypt password hashing
- **API Architecture**: RESTful endpoints

### Database
- **Primary Database**: Neon PostgreSQL (serverless)
- **ORM**: SQLAlchemy
- **Schema**: Users, Journeys, Hazard Reports
- **Connection**: Pooled connections with SSL

### Cloud Infrastructure (Huawei Cloud)
- **Compute**: ECS (Elastic Cloud Server) - Ubuntu 22.04
- **Region**: ap-southeast-1 (Singapore)
- **Storage**: OBS (Object Storage Service)
- **ML Platform**: ModelArts (for future AI model training)
- **Networking**: VPC with security groups
- **SSL/TLS**: Let's Encrypt certificates
- **Domain**: DuckDNS (saferouteai.duckdns.org)

### Security
- HTTPS encryption (TLS 1.2+)
- JWT-based authentication
- Password hashing with bcrypt
- Security groups restricting inbound traffic
- Environment variable configuration for secrets
- CORS protection

### DevOps & Deployment
- **Process Management**: systemd services
- **Auto-restart**: Configured for both Nginx and backend
- **Monitoring**: Service health checks
- **Logging**: Application and system logs
- **SSL Renewal**: Automated via certbot

## System Architecture

```
Mobile App (Android)
    ↓ HTTPS
Domain (saferouteai.duckdns.org)
    ↓
Nginx (Port 443) → SSL Termination
    ↓
FastAPI Backend (Port 8004)
    ↓
Neon PostgreSQL Database
```

## API Endpoints

### Authentication
- `POST /api/v1/auth/register` - User registration
- `POST /api/v1/auth/login` - User login
- `POST /api/v1/auth/refresh` - Token refresh
- `GET /api/v1/auth/me` - Get current user
- `PUT /api/v1/auth/preferences` - Update user preferences

### Map & Navigation
- `GET /api/v1/map/config` - Map configuration
- `POST /api/v1/map/geocode` - Address to coordinates
- `GET /api/v1/map/markers` - Get hazard markers
- `GET /api/v1/map/hazard-zones` - Get danger zones
- `GET /api/v1/map/safety-heatmap` - Get safety heatmap data
- `POST /api/v1/map/report-hazard` - Report new hazard
- `POST /api/v1/map/analyze-route-safety` - Analyze route safety

### Journey Management
- `POST /api/v1/journeys` - Save completed journey
- `GET /api/v1/journeys` - Get user journey history
- `GET /api/v1/hazards` - Get user hazard reports

### Route Optimization
- `POST /api/v1/optimize-route` - Get safest route between points

## Data Models

### User
- Email (unique identifier)
- Name
- Hashed password
- Preferences (JSON)
- Created timestamp

### Journey
- User ID (foreign key)
- Start/end coordinates
- Route waypoints
- Duration
- Distance
- Safety score
- Timestamp

### Hazard Report
- User ID (foreign key)
- Location (lat/lng)
- Hazard type
- Description
- Severity level
- Timestamp

## Performance & Scalability

### Current Capacity
- Single ECS instance handling all traffic
- Serverless database with automatic scaling
- SSL certificate auto-renewal
- Systemd auto-restart on failures

### Future Scalability Options
- Horizontal scaling with load balancer
- Database read replicas
- CDN for static assets
- Redis caching layer
- ModelArts for ML model deployment

## Development Workflow

### Making Changes
1. Update code locally
2. For frontend: `npm run build` → `npx cap sync android` → rebuild in Android Studio
3. For backend: SSH to ECS → pull changes → `sudo systemctl restart saferouteai`

### Environment Variables
- `.env` - Backend configuration
- `frontend/.env.local` - Frontend API URL
- Secrets stored in environment, not in code

## Production Status
- ✅ Backend deployed and running on Huawei Cloud ECS
- ✅ HTTPS enabled with valid SSL certificate
- ✅ Database connected and operational
- ✅ Android app built and installable
- ✅ Authentication system functional
- ✅ Map integration active
- ✅ Auto-restart configured for reliability
- ✅ Accessible from any network (WiFi/mobile data)

## Technical Differentiators
- Real-time safety data processing
- Serverless database for cost efficiency
- Production-grade security (HTTPS, JWT, password hashing)
- Cross-platform capability (Android now, iOS ready)
- Scalable cloud architecture
- Automated deployment and monitoring
