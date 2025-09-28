# Prompt Sanctuary Architecture

This document provides a comprehensive overview of the Prompt Sanctuary system architecture, including components, data flow, and technical implementation details.

## System Overview

Prompt Sanctuary is built as a modern web application using Flask as the backend framework, with a responsive frontend using Tailwind CSS and vanilla JavaScript. The system is designed for scalability, security, and maintainability.

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   External APIs │
│   (Browser)     │    │   (Flask)       │    │   (Gemini AI)   │
├─────────────────┤    ├─────────────────┤    ├─────────────────┤
│ • Tailwind CSS  │◄──►│ • Flask App     │◄──►│ • Gemini API    │
│ • JavaScript    │    │ • Blueprints    │    │ • Key Rotation  │
│ • Responsive UI │    │ • Routes        │    │ • Rate Limiting │
│ • Real-time     │    │ • Models        │    │ • Error Handling│
│   Streaming     │    │ • Security      │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   Database      │
                    │   (SQLite)      │
                    ├─────────────────┤
                    │ • Multi-DB      │
                    │   Architecture  │
                    │ • WAL Mode      │
                    │ • Migrations    │
                    │ • Backup System │
                    └─────────────────┘
```

## Backend Architecture

### Flask Application Structure

```
web/
├── app.py                 # Application entry point and configuration
├── models.py              # Database models and operations
├── routes.py              # Route definitions and handlers
├── response.py            # AI integration (legacy)
├── response2.py           # AI integration (current)
├── api_key_pool.py        # API key management and pooling
├── api_key_validator.py   # API key validation logic
├── utils.py               # Utility functions and helpers
├── safe_migration.py      # Database migration utility
└── static/                # Static assets
    ├── script/            # JavaScript modules
    ├── styles/            # CSS files
    └── icon/              # Icons and images
```

### Core Components

#### 1. Application Entry Point (`app.py`)
- **Flask App Initialization**: Main application setup and configuration
- **CSRF Protection**: Flask-WTF integration for security
- **Internationalization**: Flask-Babel setup for multilingual support
- **Database Configuration**: Multi-database path setup
- **Blueprint Registration**: Modular route organization

#### 2. Database Models (`models.py`)
- **Multi-Database Architecture**: Separate databases for different concerns
- **WAL Mode**: SQLite Write-Ahead Logging for better concurrency
- **Schema Management**: Automatic table creation and migration
- **Transaction Handling**: Robust database operations with retry logic

#### 3. Route Handlers (`routes.py`)
- **Blueprint Architecture**: Modular route organization
- **Authentication**: Session-based user authentication
- **CSRF Protection**: Token validation for all POST requests
- **Error Handling**: Comprehensive error handling and logging

#### 4. AI Integration (`response.py`, `response2.py`)
- **Model Management**: Support for multiple AI models
- **Streaming Support**: Server-Sent Events for real-time responses
- **Key Rotation**: Automatic API key rotation and health monitoring
- **Error Recovery**: Robust retry mechanisms with exponential backoff

### Database Architecture

#### Multi-Database Design

The application uses a distributed database architecture for scalability and data isolation:

```
web/database/
├── user.db                    # User accounts, sessions, profiles
├── prompt_data.db             # Personal prompts, versions, user tables
├── feedback.db                # User feedback storage
└── community/
    ├── query.db              # Built-in system prompts
    └── shared.db             # Community shared prompts
```

#### Database Schema

**User Database (`user.db`)**
```sql
-- User accounts and authentication
CREATE TABLE users (
    username TEXT PRIMARY KEY,
    password TEXT NOT NULL,
    points REAL DEFAULT 80.0,
    gemini_api_key TEXT,
    api_key_validated INTEGER DEFAULT 0
);

-- Session management
CREATE TABLE sessions (
    id TEXT PRIMARY KEY,
    username TEXT NOT NULL,
    user_agent TEXT,
    ip_address TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Achievement system
CREATE TABLE achievements (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    description TEXT NOT NULL,
    icon TEXT NOT NULL,
    points_reward REAL NOT NULL,
    category TEXT NOT NULL,
    condition_type TEXT NOT NULL,
    condition_value INTEGER,
    hidden INTEGER DEFAULT 0
);

-- Point transactions and history
CREATE TABLE point_transactions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    points REAL NOT NULL,
    source TEXT NOT NULL,
    description TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP,
    is_expired INTEGER DEFAULT 0
);
```

**Prompt Database (`prompt_data.db`)**
```sql
-- Version-controlled prompt storage
CREATE TABLE prompt_versions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    prompt_id TEXT NOT NULL,
    version_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(username, prompt_id, version_number)
);

-- User-specific prompt tables (dynamic)
CREATE TABLE "{username}" (
    random_val TEXT PRIMARY KEY,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_shared INTEGER DEFAULT 0
);
```

**Community Database (`community/shared.db`)**
```sql
-- Community-contributed prompts
CREATE TABLE shared (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    title TEXT NOT NULL,
    prompt TEXT NOT NULL,
    tags TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    view_count INTEGER DEFAULT 0,
    copy_count INTEGER DEFAULT 0
);
```

### Security Architecture

#### CSRF Protection
- **Flask-WTF Integration**: Automatic CSRF token generation
- **Token Validation**: Server-side validation for all POST requests
- **Frontend Integration**: Automatic token inclusion in AJAX requests
- **Session Security**: Secure session management with proper expiration

#### Input Sanitization
- **DOMPurify Integration**: Client-side HTML sanitization
- **Server-side Validation**: Input validation and sanitization
- **XSS Prevention**: Multiple layers of XSS protection
- **SQL Injection Prevention**: Parameterized queries and input validation

#### Session Management
- **Secure Cookies**: HttpOnly, Secure, SameSite cookie attributes
- **Session Validation**: Token-based session validation
- **Session Revocation**: Ability to revoke specific sessions
- **Activity Tracking**: Monitor session activity and detect anomalies

## Frontend Architecture

### Technology Stack
- **Tailwind CSS v3**: Utility-first CSS framework
- **Vanilla JavaScript**: No heavy frameworks for better performance
- **Server-Sent Events**: Real-time streaming support
- **Responsive Design**: Mobile-first approach with extensive breakpoints

### Component Structure

#### JavaScript Modules
```
static/script/
├── generator.js           # Prompt generation and streaming
├── prompt_refinement.js   # AI-powered prompt optimization
├── personal.js           # Personal library management
├── community.js          # Community features
├── api_key_manager.js    # API key management
├── point_history.js      # Point tracking and history
├── notifications.js      # Global notification system
├── sidebar.js            # Navigation and sidebar
├── feedback.js           # User feedback system
└── csrf.js               # CSRF token management
```

#### CSS Architecture
```
static/styles/
├── styles.css            # Main stylesheet with custom components
└── loader.css            # Loading animations and states
```

### Real-time Features

#### Streaming Implementation
- **Server-Sent Events**: Real-time content delivery
- **Progressive Rendering**: Content appears as it's generated
- **Error Handling**: Graceful fallback for streaming failures
- **Performance Optimization**: Efficient chunk processing

#### Interactive Components
- **Dynamic UI Updates**: Real-time point balance updates
- **Notification System**: Toast notifications for user feedback
- **Modal System**: Accessible modal dialogs with focus management
- **Form Validation**: Real-time form validation and feedback

## API Architecture

### RESTful Endpoints

#### Authentication & User Management
```
GET  /login              # Login page
POST /login              # User authentication
GET  /signup             # Registration page
POST /signup             # User registration
POST /logout             # User logout
```

#### Prompt Generation
```
GET  /generate           # Basic generator page
POST /generate/tprompt   # Generate text prompt
POST /generate/tprompt/stream  # Streaming text generation
POST /generate/trandom   # Generate random prompt
GET  /advance            # Advanced generator page
POST /advance/generate   # Advanced prompt generation
```

#### Prompt Management
```
GET  /mylib              # Personal library
POST /save_prompt        # Save generated prompt
POST /save_edit          # Save prompt edits
POST /delete_prompt      # Delete saved prompt
GET  /versions/<id>      # Get prompt versions
POST /versions/rollback  # Restore prompt version
```

#### Community Features
```
GET  /library            # Community library
POST /share_prompt       # Share prompt to community
POST /unshare_prompt     # Unshare prompt
GET  /feedback_list      # View feedback
```

#### API Key Management
```
POST /api_key/validate   # Validate API key
POST /api_key/remove     # Remove API key
GET  /api_key/pool_stats # Get pool statistics
```

### API Key Pool System

#### Pool Management
- **Key Rotation**: LRU (Least Recently Used) rotation algorithm
- **Health Monitoring**: Track key performance and reliability
- **Fair Distribution**: Ensure equitable usage across keys
- **Automatic Refresh**: Add new validated keys to the pool

#### Compensation System
- **Usage Tracking**: Monitor how often each key is used
- **Automatic Rewards**: 0.5 points per use compensation
- **Fair Rotation**: Prevent key overuse or underuse
- **Performance Metrics**: Track pool efficiency and health

## Performance Architecture

### Caching Strategy
- **Database Query Optimization**: Efficient queries with proper indexing
- **WAL Mode**: SQLite Write-Ahead Logging for better concurrency
- **Connection Pooling**: Efficient database connection management
- **Static Asset Optimization**: Minification and compression

### Scalability Considerations
- **Horizontal Scaling**: Stateless application design
- **Database Optimization**: Efficient schema and query design
- **API Rate Limiting**: Prevent abuse and ensure fair usage
- **Resource Management**: Efficient memory and CPU usage

### Monitoring & Observability
- **Error Tracking**: Comprehensive error logging and monitoring
- **Performance Metrics**: Response time and throughput monitoring
- **User Analytics**: Usage patterns and feature adoption
- **Health Checks**: System health monitoring and alerting

## Security Architecture

### Multi-Layer Security
1. **Network Security**: HTTPS enforcement and secure headers
2. **Application Security**: CSRF protection and input validation
3. **Data Security**: Encryption at rest and in transit
4. **Session Security**: Secure session management and validation

### Data Protection
- **Input Sanitization**: Multiple layers of input cleaning
- **Output Encoding**: Proper encoding of user-generated content
- **Access Control**: Role-based access control and permissions
- **Audit Logging**: Comprehensive logging of security events

## Deployment Architecture

### Development Environment
- **Local Development**: Flask development server
- **Database Setup**: Automatic database creation and migration
- **Hot Reloading**: Automatic reload on code changes
- **Debug Mode**: Detailed error information and debugging tools

### Production Considerations
- **WSGI Server**: Gunicorn for production deployment
- **Reverse Proxy**: Nginx for static file serving and load balancing
- **Database Backup**: Automated backup and recovery procedures
- **SSL/TLS**: HTTPS enforcement and secure certificate management

### Containerization (Planned)
- **Docker Support**: Containerized deployment
- **Docker Compose**: Multi-service orchestration
- **Health Checks**: Container health monitoring
- **Environment Configuration**: Secure environment variable management

## Future Architecture Considerations

### Planned Improvements
1. **Microservices**: Split into smaller, focused services
2. **Message Queues**: Asynchronous processing for heavy operations
3. **CDN Integration**: Content delivery network for static assets
4. **Advanced Caching**: Redis for session and application caching
5. **Database Scaling**: PostgreSQL for better performance and features

### Scalability Roadmap
1. **Horizontal Scaling**: Load balancing and auto-scaling
2. **Database Sharding**: Distribute data across multiple databases
3. **API Gateway**: Centralized API management and rate limiting
4. **Event-Driven Architecture**: Asynchronous event processing
5. **Cloud-Native**: Kubernetes deployment and management

---

*This architecture documentation reflects the current state of Prompt Sanctuary. For the latest updates and planned changes, refer to the [development roadmap](../development/roadmap.md).*
