# Invoice Management Application

A modern, multi-tenant invoice management system built with FastAPI and React. This application allows businesses to manage clients, create invoices, track payments, and generate professional PDF invoices.

## 🚀 Features

### Core Functionality
- **Multi-tenant Architecture** - Isolated data per tenant/organization
- **Client Management** - Add, edit, and manage customer information
- **Invoice Creation** - Generate professional invoices with automatic numbering
- **Payment Tracking** - Record and track payments against invoices
- **Dashboard Analytics** - Overview of financial metrics and statistics
- **PDF Generation** - Export invoices as professional PDF documents
- **Responsive Design** - Modern UI that works on desktop and mobile

### Authentication & Security
- **User Authentication** - Secure login/signup with JWT tokens
- **Role-based Access** - Admin, user, and viewer roles
- **Google SSO** - Optional Google OAuth integration
- **Tenant Isolation** - Complete data separation between organizations

### Technical Features
- **RESTful API** - Clean, documented API endpoints
- **Real-time Updates** - Instant UI updates with optimistic rendering
- **Search & Filtering** - Advanced filtering and search capabilities
- **Docker Support** - Containerized deployment ready
- **Database Migrations** - Automated schema management

## 🏗️ Architecture

### Backend (FastAPI)
- **Framework**: FastAPI with Python 3.11
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: JWT with fastapi-users
- **Documentation**: Auto-generated OpenAPI/Swagger docs
- **Deployment**: Docker containerized

### Frontend (React)
- **Framework**: React 18 with TypeScript
- **Build Tool**: Vite
- **UI Library**: ShadCN UI components with Tailwind CSS
- **State Management**: TanStack Query for server state
- **Routing**: React Router with protected routes
- **Deployment**: Docker containerized

### Infrastructure
- **Orchestration**: Docker Compose
- **Database**: Persistent SQLite with volume mounting
- **Networking**: Internal Docker network for service communication

## 📋 Prerequisites

- Docker and Docker Compose
- Node.js 18+ (for local development)
- Python 3.11+ (for local development)

## 🚀 Quick Start

### Using Docker (Recommended)

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd invoice-app
   ```

2. **Start the application**
   ```bash
   docker-compose up -d
   ```

3. **Access the application**
   - Frontend: http://localhost:8080
   - Backend API: http://localhost:8000
   - API Documentation: http://localhost:8000/docs

### Local Development Setup

#### Backend Setup
```bash
cd api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
python db_init.py  # Initialize database
uvicorn main:app --reload
```

#### Frontend Setup
```bash
cd ui
npm install
npm run dev
```

## 📚 API Documentation

The API is fully documented and available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### Key Endpoints

#### Authentication
- `POST /api/auth/register` - User registration
- `POST /api/auth/login` - User login
- `POST /api/auth/logout` - User logout

#### Clients
- `GET /api/clients/` - List clients
- `POST /api/clients/` - Create client
- `PUT /api/clients/{id}` - Update client
- `DELETE /api/clients/{id}` - Delete client

#### Invoices
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/` - Create invoice
- `PUT /api/invoices/{id}` - Update invoice
- `DELETE /api/invoices/{id}` - Delete invoice

#### Payments
- `GET /api/payments/` - List payments
- `POST /api/payments/` - Record payment
- `PUT /api/payments/{id}` - Update payment

## 🗃️ Database Schema

### Core Entities

#### Tenants
- Multi-tenant isolation
- Company information (name, address, tax ID)
- Logo and branding settings

#### Users
- Authentication and authorization
- Role-based access control
- Google SSO integration

#### Clients
- Customer information
- Contact details
- Balance tracking

#### Invoices
- Auto-generated invoice numbers
- Due dates and status tracking
- Notes and custom fields

#### Payments
- Payment tracking against invoices
- Multiple payment methods
- Reference numbers

## 🎨 Frontend Structure

```
ui/src/
├── components/          # Reusable UI components
│   ├── ui/             # ShadCN UI components
│   ├── auth/           # Authentication components
│   ├── invoices/       # Invoice-specific components
│   └── layout/         # Layout components
├── pages/              # Route components
├── lib/                # Utilities and API client
├── hooks/              # Custom React hooks
└── routers/            # Route definitions
```

## 🔧 Configuration

### Environment Variables

#### Backend (.env)
```env
DATABASE_URL=sqlite:///./invoice_app.db
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret
GOOGLE_CLIENT_ID=your-google-client-id
GOOGLE_CLIENT_SECRET=your-google-client-secret
```

#### Frontend (.env)
```env
VITE_API_URL=http://localhost:8000/api
```

## 🚀 Deployment

### Production Deployment

1. **Update environment variables** for production
2. **Build and deploy with Docker Compose**:
   ```bash
   docker-compose -f docker-compose.prod.yml up -d
   ```

### Cloud Deployment
- **Backend**: Deploy to any platform supporting Docker (AWS ECS, Google Cloud Run, etc.)
- **Frontend**: Deploy to static hosting (Vercel, Netlify, AWS S3 + CloudFront)
- **Database**: Migrate to PostgreSQL for production use

## 🔒 Security Considerations

- JWT tokens for authentication
- Password hashing with bcrypt
- CORS properly configured
- SQL injection protection via SQLAlchemy ORM
- Input validation with Pydantic schemas
- Tenant isolation at database level

## 🧪 Testing

### Backend Tests
```bash
cd api
pytest
```

### Frontend Tests
```bash
cd ui
npm test
```

## 📈 Performance

- **Database**: Optimized queries with proper indexing
- **Caching**: Query result caching with TanStack Query
- **Lazy Loading**: Component-level code splitting
- **Compression**: Gzip compression for API responses

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/new-feature`
3. Commit changes: `git commit -am 'Add new feature'`
4. Push to branch: `git push origin feature/new-feature`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🔮 Roadmap

- [ ] Email invoice delivery
- [ ] Recurring invoices
- [ ] Multi-currency support
- [ ] Advanced reporting and analytics
- [ ] Mobile app (React Native)
- [ ] Integration with payment gateways
- [ ] Automated backup system
- [ ] Advanced user permissions

## 🆘 Support

For support and questions:
- Create an issue on GitHub
- Check the documentation at `/docs`
- Review API documentation at `/docs` endpoint

## 🏷️ Version History

- **v1.0.0** - Initial release with core functionality
  - Multi-tenant architecture
  - Invoice and client management
  - Payment tracking
  - PDF generation
  - Modern React UI
