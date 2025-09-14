# Invoicely - Invoice Management System

A comprehensive Django-based invoice management system similar to Invoicely.gg for creating, sending, and managing invoices with client management, payment tracking, and a modern dashboard.

## Features

### Core Functionality
- **User Authentication**: Registration, login, logout with role-based access (admin/client)
- **Client Management**: Full CRUD operations for client information
- **Invoice Management**: Create, edit, view, and manage invoices with automatic numbering
- **Payment Tracking**: Record and track payments with multiple payment methods
- **Dashboard**: Statistics and analytics with charts and recent activity

### Advanced Features
- **PDF Generation**: Generate professional PDF invoices using WeasyPrint
- **Email Integration**: Send invoices directly to clients via email
- **Search & Filter**: Advanced search and filtering for invoices, clients, and payments
- **CSV Export**: Export invoice data to CSV format
- **Dark Mode**: Toggle between light and dark themes
- **Responsive Design**: Mobile-friendly UI built with Tailwind CSS

### Technical Features
- **REST API**: Django REST Framework endpoints for all major operations
- **PostgreSQL**: Robust database backend
- **Modern UI**: Tailwind CSS with Alpine.js for interactivity
- **Security**: Best practices for authentication and data protection

## Technology Stack

### Backend
- **Django 4.2+**: Web framework
- **Django REST Framework**: API development
- **PostgreSQL**: Database
- **WeasyPrint**: PDF generation
- **Python Decouple**: Environment configuration

### Frontend
- **Tailwind CSS**: Styling framework
- **Alpine.js**: JavaScript framework for interactivity
- **Chart.js**: Data visualization
- **Font Awesome**: Icons

## Installation & Setup

### Prerequisites
- Python 3.8+
- PostgreSQL 12+
- Node.js (optional, for development)

### 1. Clone the Repository
```bash
git clone <repository-url>
cd invoicely
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

### 4. Database Setup
Create a PostgreSQL database and user:
```sql
CREATE DATABASE invoicely_db;
CREATE USER invoicely_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE invoicely_db TO invoicely_user;
```

### 5. Environment Configuration
Copy `.env.example` to `.env` and update the values:
```bash
cp .env.example .env
```

Edit `.env` with your configuration:
```env
SECRET_KEY=your-secret-key-here
DEBUG=True
DB_NAME=invoicely_db
DB_USER=invoicely_user
DB_PASSWORD=your_password
DB_HOST=localhost
DB_PORT=5432
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
DEFAULT_FROM_EMAIL=noreply@invoicely.com
```

### 6. Run Migrations
```bash
python manage.py makemigrations
python manage.py migrate
```

### 7. Create Superuser
```bash
python manage.py createsuperuser
```

### 8. Collect Static Files
```bash
python manage.py collectstatic
```

### 9. Run Development Server
```bash
python manage.py runserver
```

Visit `http://localhost:8000` to access the application.

## Project Structure

```
invoicely/
├── invoicely/              # Main project directory
│   ├── settings.py         # Django settings
│   ├── urls.py            # Main URL configuration
│   └── wsgi.py            # WSGI configuration
├── users/                 # User management app
│   ├── models.py          # Custom User model
│   ├── views.py           # Authentication views
│   ├── forms.py           # User forms
│   └── urls.py            # User URLs
├── clients/               # Client management app
│   ├── models.py          # Client model
│   ├── views.py           # Client CRUD views
│   ├── forms.py           # Client forms
│   └── urls.py            # Client URLs
├── invoices/              # Invoice management app
│   ├── models.py          # Invoice and InvoiceItem models
│   ├── views.py           # Invoice CRUD views
│   ├── forms.py           # Invoice forms
│   ├── utils.py           # PDF generation utilities
│   └── urls.py            # Invoice URLs
├── payments/              # Payment tracking app
│   ├── models.py          # Payment model
│   ├── views.py           # Payment CRUD views
│   ├── forms.py           # Payment forms
│   └── urls.py            # Payment URLs
├── templates/             # HTML templates
│   ├── base.html          # Base template with navigation
│   ├── users/             # User templates
│   ├── clients/           # Client templates
│   ├── invoices/          # Invoice templates
│   └── payments/          # Payment templates
├── static/                # Static files (CSS, JS, images)
├── media/                 # User uploaded files
├── requirements.txt       # Python dependencies
└── README.md             # This file
```

## Usage

### Getting Started
1. Register a new account or login with existing credentials
2. Add your first client in the Clients section
3. Create an invoice for the client
4. Send the invoice via email or download as PDF
5. Record payments when received
6. Monitor everything from the dashboard

### Demo Credentials
For testing purposes, you can use these demo accounts:
- **Admin**: admin@invoicely.com / admin123
- **Client**: client@invoicely.com / client123

### Key Workflows

#### Creating an Invoice
1. Navigate to Invoices → New Invoice
2. Select a client and set dates
3. Add invoice items with descriptions, quantities, and prices
4. Set tax rate if applicable
5. Add notes and terms
6. Save the invoice

#### Sending an Invoice
1. Open the invoice detail page
2. Click "Actions" → "Email Invoice"
3. Customize the email message
4. Send (PDF will be automatically attached)

#### Recording a Payment
1. Navigate to Payments → Record Payment
2. Select the invoice
3. Enter payment amount and method
4. Add reference number and notes
5. Save the payment

## API Endpoints

The application provides REST API endpoints for integration:

### Authentication
- `POST /api/auth/login/` - User login
- `POST /api/auth/logout/` - User logout
- `POST /api/auth/register/` - User registration

### Clients
- `GET /api/clients/` - List clients
- `POST /api/clients/` - Create client
- `GET /api/clients/{id}/` - Get client details
- `PUT /api/clients/{id}/` - Update client
- `DELETE /api/clients/{id}/` - Delete client

### Invoices
- `GET /api/invoices/` - List invoices
- `POST /api/invoices/` - Create invoice
- `GET /api/invoices/{id}/` - Get invoice details
- `PUT /api/invoices/{id}/` - Update invoice
- `DELETE /api/invoices/{id}/` - Delete invoice
- `GET /api/invoices/{id}/pdf/` - Download PDF
- `POST /api/invoices/{id}/email/` - Email invoice

### Payments
- `GET /api/payments/` - List payments
- `POST /api/payments/` - Create payment
- `GET /api/payments/{id}/` - Get payment details
- `PUT /api/payments/{id}/` - Update payment
- `DELETE /api/payments/{id}/` - Delete payment

## Configuration

### Email Settings
Configure SMTP settings in your `.env` file for email functionality:
```env
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

For Gmail, you'll need to:
1. Enable 2-factor authentication
2. Generate an app-specific password
3. Use the app password in EMAIL_HOST_PASSWORD

### PDF Generation
PDF generation uses WeasyPrint which requires some system dependencies:

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-dev python3-pip python3-cffi python3-brotli libpango-1.0-0 libharfbuzz0b libpangoft2-1.0-0
```

**macOS:**
```bash
brew install pango
```

**Windows:**
WeasyPrint should work out of the box with the pip installation.

## Development

### Running Tests
```bash
python manage.py test
```

### Code Style
The project follows PEP 8 guidelines. Use tools like `black` and `flake8` for formatting:
```bash
pip install black flake8
black .
flake8 .
```

### Database Migrations
When making model changes:
```bash
python manage.py makemigrations
python manage.py migrate
```

## Deployment

### Production Settings
1. Set `DEBUG=False` in production
2. Configure proper `ALLOWED_HOSTS`
3. Use environment variables for sensitive data
4. Set up proper static file serving
5. Configure database connection pooling
6. Set up SSL/HTTPS

### Docker Deployment
A `Dockerfile` and `docker-compose.yml` can be added for containerized deployment.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Support

For support and questions:
- Create an issue on GitHub
- Check the documentation
- Review the code comments

## Roadmap

Future enhancements may include:
- Stripe/PayPal payment integration
- Multi-currency support
- Invoice templates
- Recurring invoices
- Time tracking integration
- Mobile app
- Advanced reporting
- Multi-language support
