# EPOS - Electronic Business Management System

## Overview
EPOS is a microservices-based electronic business management system designed to streamline client management, invoicing, expense tracking, and tenant administration. This project implements a multi-tenant architecture using Python, Flask, SQLite, and RabbitMQ for asynchronous message queuing. The system is tailored for small to medium-sized businesses to manage their operations efficiently, with a focus on scalability and modularity.

## Technologies Used
- **Programming Language**: Python 3.9
- **Framework**: Flask (for RESTful APIs and web interfaces)
- **Database**: SQLite (local database stored in `epos.db`)
- **Message Queue**: RabbitMQ (for inter-service communication)
- **CORS**: Flask-CORS (for cross-origin resource sharing)
- **Containerization**: Docker Compose (for orchestrating multiple services)
- **Libraries**: 
  - `pika` (RabbitMQ client)
  - `redis` (for caching, optional in API Gateway)
  - `requests` (for HTTP requests between services)
  - `uuid` (for generating unique identifiers)
  - `datetime` (for timestamp management)
  - `json` (for data serialization)
  - `dataclasses` (for structured data representation)

## Project Structure
The project is organized into multiple microservices, each running in its own Docker container as defined in `docker-compose.yml`:
- **Tenant Service** (port 5004): Manages tenant registration, validation, and administration (e.g., approving/rejecting requests, suspending tenants).
- **Client Service** (port 5001): Handles client CRUD operations with multi-tenancy support.
- **Invoice Service** (port 5002): Manages invoice creation, updates, retrieval, and automatic expense generation.
- **Expenses Service** (port 5003): Tracks expenses, categorizes them, and provides statistical analysis.
- **API Gateway** (port 8080): Routes requests to appropriate services, handles message queuing, and provides caching (if Redis is available).
- **Web App** (port 5000): Provides a front-end interface for authenticated users to manage clients, invoices, and expenses.
- **Admin Web** (port 5005): Admin dashboard for managing tenants and pending requests.
- **Public Registration** (port 3000): Public-facing form for new tenants to submit activation requests.

## Implementation Details
- **Microservices Architecture**: Each service is a standalone Flask application, communicating via REST APIs and RabbitMQ for asynchronous tasks (e.g., client creation, invoice processing).
- **Multi-Tenancy**: Tenant isolation is achieved using API keys, with tenant-specific data stored in the `tenants` and `klijenti` tables. Validation is performed by the Tenant Service.
- **Database Schema**: SQLite databases include tables for tenants, tenant requests, clients, invoices, expenses, and categories, with foreign key relationships where applicable.
- **Message Queuing**: RabbitMQ facilitates asynchronous communication, with events like `tenant_activated`, `create_client`, and `create_expense` published and processed via callbacks.
- **Front-End**: HTML/CSS/JavaScript interfaces are provided for admin (dynamic tenant/request management), web app (tabbed interface for clients/invoices/expenses), and public registration (form with validation).
- **Authentication**: Basic API key validation is implemented; full user authentication is pending.

## How to Run the Project
1. **Prerequisites**:
   - Install Docker and Docker Compose.
   - Ensure RabbitMQ is installed and running locally (default host: `localhost`).
   - Optional: Install Redis for caching in the API Gateway (default host: `localhost`, port 6379).

2. **Setup**:
   - Clone the repository: `git clone <repository-url>`.
   - Navigate to the project directory: `cd EPOS`.

3. **Configuration**:
   - Update `docker-compose.yml` if needed (e.g., adjust the `device` path under `epos-db` to match your local `db` directory, currently set to `/c/Users/Administrator/PycharmProjects/EPOS/db`).
   - Ensure each service directory (e.g., `tenant_service`, `client-service`) contains a `requirements.txt` file listing dependencies (e.g., `flask`, `pika`, `requests`).

4. **Run the Application**:
   - Start all services with: `docker-compose up --build`.
   - The services will be available on their respective ports (e.g., `http://localhost:5000` for Web App, `http://localhost:3000` for Public Registration).

5. **Access**:
   - Public Registration: `http://localhost:3000`
   - Web App: `http://localhost:5000` (requires API key validation)
   - Admin Dashboard: `http://localhost:5005`
   - API Gateway: `http://localhost:8080`

## Features
- **Client Management**: Create, update, delete, and list clients with tenant isolation.
- **Invoice Management**: Generate invoices with line items, update status, retrieve client-specific invoices, and trigger transport expense creation.
- **Expense Tracking**: Record expenses, categorize them (e.g., material, service, payroll), and view statistics by category and status.
- **Tenant Administration**: Admin panel to view/manage tenant requests, approve/reject requests, suspend tenants, and view active tenants.
- **Public Registration**: Form for new tenants to request activation, with real-time validation and feedback.
- **Statistics**: Web app displays expense statistics (total amount, count, by category, and status).

## Missing Functionalities
- **User Authentication**: Currently relies on API keys; a full user login system with roles (e.g., admin, tenant) is missing.
- **Payment Integration**: No support for processing payments or generating payment links for invoices.
- **Reporting Module**: Detailed financial reports and export functionality (e.g., PDF generation) are not implemented.
- **Real-Time Notifications**: Lack of real-time updates or email notifications for tenant requests, invoice statuses, or expense approvals.
- **Error Handling**: Limited robust error recovery (e.g., RabbitMQ connection retries could be enhanced).
- **Frontend Enhancements**: Basic UI with no advanced interactivity (e.g., charts, drag-and-drop).
