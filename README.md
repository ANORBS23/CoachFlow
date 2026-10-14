# CoachFlow

AI-powered business management SaaS designed to help small businesses manage clients, leads, appointments and customer follow-ups from one platform.

## Overview

CoachFlow is a full-stack web application developed using Python and Flask.

The application provides a centralised workspace where businesses can manage their customer pipeline, communicate with leads, schedule appointments and automate follow-up processes.

CoachFlow also integrates locally hosted AI to generate personalised customer responses and follow-up messages without relying on a paid AI API.

## Features

### Business Authentication
- Business account registration and login
- Secure password hashing using Argon2
- Session-based authentication
- Business-level data isolation

### Client Management
- Add new clients
- View client profiles
- Edit client information
- Track client goals and notes
- Delete clients

### Lead Management
- Create and manage potential customers
- Track lead status through the customer pipeline
- Search and filter leads
- View individual lead profiles
- Convert leads into clients
- Delete leads

### AI-Powered Responses
- Generate personalised responses to customer enquiries
- Generate follow-up messages using locally hosted AI
- Uses Ollama and Llama 3.2
- Designed to avoid inventing prices, availability or business promises

### Email Communication
- Send customer emails directly from the application
- AI-generated responses can be reviewed and sent
- Communication history is stored for each lead
- Email delivery is handled using Resend

### Automated Follow-Ups
- Schedule automated follow-up sequences
- Configure follow-up intervals
- Automatically generate follow-up messages using AI
- Automatically send follow-up emails
- Track previous follow-ups
- Automatically stop sequences after the configured limit
- Follow-ups are disabled when a lead is converted or marked as lost

### Appointment Management
- Create appointments
- Edit appointments
- Manage appointments associated with clients

### Analytics
- Business performance dashboard
- Lead pipeline analytics
- Conversion statistics
- Revenue statistics
- Client and lead insights
- Visual data presentation

## Technology Stack

### Backend
- Python
- Flask
- SQLite
- Argon2

### AI
- Ollama
- Llama 3.2

### Frontend
- HTML
- CSS
- JavaScript
- Jinja2

### Email
- Resend

### Development Tools
- Visual Studio Code
- Git
- GitHub

## Project Structure

```text
CoachFlow/
│
├── ai/
│   └── ollama_client.py
│
├── analytics/
│   ├── __init__.py
│   └── charts.py
│
├── automation/
│   ├── __init__.py
│   └── follow_up_scheduler.py
│
├── database/
│   ├── database.py
│   └── database.db
│
├── services/
│   ├── __init__.py
│   └── resend_client.py
│
├── static/
│   └── style.css
│
├── templates/
│   ├── login.html
│   ├── register.html
│   ├── dashboard.html
│   ├── clients.html
│   ├── client_profile.html
│   ├── add_client.html
│   ├── edit_client.html
│   ├── leads.html
│   ├── lead_profile.html
│   ├── edit_lead.html
│   ├── appointments.html
│   ├── add_appointment.html
│   ├── edit_appointment.html
│   ├── analytics.html
│   └── follow_ups.html
│
├── app.py
├── charts.py
├── validation.py
└── README.md


### One important thing

I deliberately **didn't put `database.db` in the README as something users should commit**. Your `.gitignore` should keep it out of GitHub.

After you save `README.md`, run:

```powershell
git add README.md
git commit -m "Add professional project README"
git push

###Author
Alex Norbury
Bsc Computer Science
