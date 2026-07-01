# Financial Cockpit

## Overview

Financial Cockpit is a personal finance management web application developed as a final project for practical software engineering studies (Mahat).

The system allows users to manage and analyze their personal finances by tracking income and expenses, viewing financial summaries, filtering transactions, and analyzing financial data through dashboards and charts.

The application supports role-based access control with two types of users:

* USER
* ADMIN

---

## Features

### User Management

* User registration and authentication
* Login and logout functionality
* Role-based access control (USER / ADMIN)

### Financial Management

* Add, edit, and delete income records
* Add, edit, and delete expense records
* Manage financial transactions
* Calculate current balance

### Dashboard & Analysis

* Financial dashboard with summaries
* Income and expense analysis
* Charts and visual reports
* Transaction filtering and search capabilities

### Export

* Export financial data for external usage

### Administration

* Administrative functionality for managing system data

---

## Architecture

The project is built using a layered architecture approach.

### Routes Layer

Responsible for handling HTTP requests, user interactions, and application endpoints.

Examples:

* Authentication routes
* Income routes
* Expense routes
* Dashboard routes

### Services Layer

Contains the business logic of the application.

Responsible for:

* Processing financial operations
* Applying application rules
* Connecting between routes and data access layers

### Repositories Layer

Responsible for communication with the database.

Handles:

* Data retrieval
* Data insertion
* Data updates
* Database queries

### Utilities Layer

Contains reusable helper functions such as:

* Authentication utilities
* Permission handling
* Shared application logic

### Database Layer

The project uses SQLite as the database system.

Database structure is managed through:

```
schema.sql
```

---

## Technologies Used

* Python
* Flask
* SQLite
* Pandas
* NumPy
* Jinja2
* HTML
* CSS

---

## Project Structure

```
Financial-Cockpit/

├── app.py
├── config.py
├── db.py
├── schema.sql
│
├── routes/
├── services/
├── repositories/
├── utils/
│
├── templates/
└── static/
```

---

## Installation & Running

### Clone the repository

```bash
git clone <repository-url>
```

### Create virtual environment

```bash
python -m venv .venv
```

Activate the environment:

Linux:

```bash
source .venv/bin/activate
```

Windows:

```bash
.venv\Scripts\activate
```

### Install dependencies

```bash
pip install -r requirements.txt
```

### Run the application

```bash
python app.py
```

The application will be available at:

```
http://127.0.0.1:5000
```

---

## Project Purpose

This project was developed as a final project for practical software engineering studies.

The goal was to build a complete web application while implementing backend development principles, database management, user authentication, layered architecture, and financial data analysis.

---

## Future Improvements

Possible future enhancements:

* Migration to a production database such as PostgreSQL
* Deployment to a cloud environment
* Additional financial reports
* Improved user interface
* Automated testing

```
```
