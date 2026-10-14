from flask import Flask, redirect, render_template, request, session
from flask_wtf.csrf import CSRFProtect
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError, VerificationError
from datetime import date, datetime

import calendar
import re
import os
from ai.ollama_client import generate_lead_reply, generate_follow_up
from services.resend_client import send_email
from automation.follow_up_scheduler import start_scheduler

from database.database import (
    create_database,
    get_db_connection,

    # Businesses
    get_business_by_email,
    add_business,

    # Clients
    add_client,
    get_clients,
    get_client,
    update_client,
    delete_client,

    # Appointments
    add_appointment,
    get_appointment,
    get_appointments,
    update_appointment,
    delete_appointment,

    # Leads
    add_lead,
    get_leads,
    get_lead ,
    update_lead,
    delete_lead,
    convert_lead_to_client,
    get_lead_analytics,
    add_follow_up,
    get_follow_up_leads,

    # Analytics
    get_total_revenue,
    get_revenue_statistics,

    # Migrations
    add_follow_up_columns,
    add_revenue_column,
    add_appoitment_status_column,

    # Communications
    create_communications_table,
    add_communication,
    get_lead_communications,
    update_lead_last_contacted,

    #Follow ups
    schedule_follow_up,
    disable_follow_up


)


app = Flask(__name__)

# ---------------------------------------------------------
# SECRET KEY
# ---------------------------------------------------------

# Use an environment variable in production.
# The fallback is only for local development.
app.secret_key = os.environ.get(
    "SECRET_KEY",
    "coachflow-development-secret-key-change-this"
)


password_hasher = PasswordHasher()


# ---------------------------------------------------------
# DATABASE SETUP
# ---------------------------------------------------------

create_database()
add_follow_up_columns()
add_revenue_column()
add_appoitment_status_column()
create_communications_table()


# ---------------------------------------------------------
# VALIDATION HELPERS
# ---------------------------------------------------------

def is_valid_email(email):
    """
    Checks whether an email address has a sensible format.
    """
    pattern = r"^[^@\s]+@[^@\s]+\.[^@\s]+$"
    return re.match(pattern, email) is not None


def validate_password(password):
    """
    Checks whether a password meets CoachFlow's requirements.

    Requirements:
    - At least 8 characters
    - At least one uppercase letter
    - At least one lowercase letter
    - At least one number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long."

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."

    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."

    return True, ""


def validate_required(value, field_name):
    """
    Makes sure a required field is not empty.
    """
    if not value or not value.strip():
        return False, f"{field_name} is required."

    return True, ""


def get_logged_in_business_id():
    """
    Returns the logged-in business ID.

    If the user is not logged in, returns None.
    """
    return session.get("user_id")


# ---------------------------------------------------------
# LOGIN
# ---------------------------------------------------------

@app.route("/", methods=["GET", "POST"])
def login():

    if request.method == "POST":

        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        # Basic validation
        if not email or not password:
            return render_template(
                "login.html",
                error="Please enter your email and password."
            )

        if not is_valid_email(email):
            return render_template(
                "login.html",
                error="Please enter a valid email address."
            )

        business = get_business_by_email(email)

        # Don't reveal whether the account exists.
        if not business:
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        try:
            password_hasher.verify(
                business["password_hash"],
                password
            )

        except (VerifyMismatchError, VerificationError):
            return render_template(
                "login.html",
                error="Invalid email or password."
            )

        # Successful login
        session.clear()

        session["user_id"] = business["id"]
        session["business_name"] = business["business_name"]

        return redirect("/dashboard")

    return render_template("login.html")


# ---------------------------------------------------------
# REGISTER
# ---------------------------------------------------------

@app.route("/register", methods=["GET", "POST"])
def register():

    if request.method == "POST":

        business_name = request.form.get(
            "business_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip().lower()

        password = request.form.get(
            "password",
            ""
        )

        # -------------------------------
        # Business name validation
        # -------------------------------

        valid, message = validate_required(
            business_name,
            "Business name"
        )

        if not valid:
            return render_template(
                "register.html",
                error=message
            )

        if len(business_name) > 100:
            return render_template(
                "register.html",
                error="Business name must be 100 characters or fewer."
            )

        # -------------------------------
        # Email validation
        # -------------------------------

        if not email:
            return render_template(
                "register.html",
                error="Email address is required."
            )

        if not is_valid_email(email):
            return render_template(
                "register.html",
                error="Please enter a valid email address."
            )

        # -------------------------------
        # Check duplicate account
        # -------------------------------

        existing_business = get_business_by_email(email)

        if existing_business:
            return render_template(
                "register.html",
                error="An account with this email already exists."
            )

        # -------------------------------
        # Password validation
        # -------------------------------

        password_valid, password_message = validate_password(password)

        if not password_valid:
            return render_template(
                "register.html",
                error=password_message
            )

        # -------------------------------
        # Hash password
        # -------------------------------

        password_hash = password_hasher.hash(password)

        # -------------------------------
        # Create account
        # -------------------------------

        add_business(
            business_name,
            email,
            password_hash
        )

        return redirect("/")

    return render_template("register.html")


# ---------------------------------------------------------
# DASHBOARD
# ---------------------------------------------------------

@app.route("/dashboard")
def dashboard():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    clients = get_clients(business_id)
    leads = get_leads(business_id)
    appointments = get_appointments(business_id)

    total_revenue = get_total_revenue(business_id)

    return render_template(
        "dashboard.html",
        clients=clients,
        leads=leads,
        appointments=appointments,
        total_revenue=total_revenue
    )


# ---------------------------------------------------------
# ADD CLIENT
# ---------------------------------------------------------

@app.route("/add-client", methods=["GET", "POST"])
def add_client_route():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    if request.method == "POST":

        client_name = request.form.get(
            "client_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        goal = request.form.get(
            "goal",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        revenue = request.form.get(
            "revenue",
            "0"
        ).strip()

        # Name validation
        if not client_name:
            return render_template(
                "add_client.html",
                error="Client name is required."
            )

        # Email validation if supplied
        if email and not is_valid_email(email):
            return render_template(
                "add_client.html",
                error="Please enter a valid email address."
            )

        # Revenue validation
        try:
            revenue_value = float(revenue or 0)

            if revenue_value < 0:
                raise ValueError

        except ValueError:
            return render_template(
                "add_client.html",
                error="Revenue must be a valid positive number."
            )

        add_client(
            business_id,
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue_value
        )

        return redirect("/clients")

    return render_template("add_client.html")


# ---------------------------------------------------------
# CLIENTS
# ---------------------------------------------------------

@app.route("/clients")
def clients():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    search = request.args.get(
        "search",
        ""
    ).strip()

    clients = get_clients(
        business_id,
        search
    )

    return render_template(
        "clients.html",
        clients=clients,
        search=search
    )


# ---------------------------------------------------------
# CLIENT PROFILE
# ---------------------------------------------------------

@app.route("/client/<int:client_id>")
def client_profile(client_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    client = get_client(
        client_id,
        business_id
    )

    if not client:
        return "Client not found", 404

    return render_template(
        "client_profile.html",
        client=client
    )


# ---------------------------------------------------------
# EDIT CLIENT
# ---------------------------------------------------------

@app.route("/edit-client/<int:client_id>", methods=["GET", "POST"])
def edit_client(client_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    client = get_client(
        client_id,
        business_id
    )

    if not client:
        return "Client not found", 404

    if request.method == "POST":

        client_name = request.form.get(
            "client_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        goal = request.form.get(
            "goal",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        revenue = request.form.get(
            "revenue",
            "0"
        ).strip()

        if not client_name:
            return render_template(
                "edit_client.html",
                client=client,
                error="Client name is required."
            )

        if email and not is_valid_email(email):
            return render_template(
                "edit_client.html",
                client=client,
                error="Please enter a valid email address."
            )

        try:
            revenue_value = float(revenue or 0)

            if revenue_value < 0:
                raise ValueError

        except ValueError:
            return render_template(
                "edit_client.html",
                client=client,
                error="Revenue must be a valid positive number."
            )

        update_client(
            client_id,
            business_id,
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue_value
        )

        return redirect(
            f"/client/{client_id}"
        )

    return render_template(
        "edit_client.html",
        client=client
    )


# ---------------------------------------------------------
# DELETE CLIENT
# ---------------------------------------------------------

@app.route("/delete-client/<int:client_id>")
def delete_client_route(client_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    client = get_client(
        client_id,
        business_id
    )

    if not client:
        return "Client not found", 404

    delete_client(
        client_id,
        business_id
    )

    return redirect("/clients")


# ---------------------------------------------------------
# APPOINTMENTS
# ---------------------------------------------------------

@app.route("/appointments")
def appointments():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    today = date.today()

    month_string = request.args.get(
        "month",
        ""
    )

    if month_string:

        try:
            selected_month = datetime.strptime(
                month_string,
                "%Y-%m"
            ).date()

        except ValueError:
            selected_month = today

    else:
        selected_month = today

    year = selected_month.year
    month = selected_month.month

    search = request.args.get(
        "search",
        ""
    ).strip()

    appointments = get_appointments(
        business_id,
        search
    )

    calendar_object = calendar.Calendar(
        firstweekday=0
    )

    month_weeks = calendar_object.monthdatescalendar(
        year,
        month
    )

    calendar_weeks = []

    for week in month_weeks:

        calendar_week = []

        for day in week:

            day_string = day.isoformat()

            day_appointments = [
                appointment
                for appointment in appointments
                if appointment["appointment_date"] == day_string
            ]

            calendar_week.append({
                "date": day,
                "appointments": day_appointments
            })

        calendar_weeks.append(calendar_week)

    if month == 1:
        previous_month = f"{year - 1}-12"
    else:
        previous_month = f"{year}-{month - 1:02d}"

    if month == 12:
        next_month = f"{year + 1}-01"
    else:
        next_month = f"{year}-{month + 1:02d}"

    current_month = f"{year}-{month:02d}"

    return render_template(
        "appointments.html",
        appointments=appointments,
        calendar_weeks=calendar_weeks,
        current_month=current_month,
        previous_month=previous_month,
        next_month=next_month,
        month_name=selected_month.strftime("%B"),
        year=year,
        month=month,
        today=today.isoformat(),
        search=search
    )


# ---------------------------------------------------------
# ADD APPOINTMENT
# ---------------------------------------------------------

@app.route("/add-appointment", methods=["GET", "POST"])
def add_appointment_route():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    selected_date = request.args.get(
        "date",
        ""
    )

    if request.method == "POST":

        client_id = request.form.get(
            "client_id"
        )

        appointment_date = request.form.get(
            "appointment_date"
        )

        appointment_time = request.form.get(
            "appointment_time"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Upcoming"
        )

        if not client_id:
            return render_template(
                "add_appointment.html",
                clients=get_clients(business_id),
                selected_date=appointment_date,
                error="Please select a client."
            )

        if not appointment_date:
            return render_template(
                "add_appointment.html",
                clients=get_clients(business_id),
                selected_date=appointment_date,
                error="Please select an appointment date."
            )

        if not appointment_time:
            return render_template(
                "add_appointment.html",
                clients=get_clients(business_id),
                selected_date=appointment_date,
                error="Please select an appointment time."
            )

        # Make sure the client belongs to this business
        client = get_client(
            int(client_id),
            business_id
        )

        if not client:
            return "Client not found", 404

        add_appointment(
            business_id,
            int(client_id),
            appointment_date,
            appointment_time,
            notes,
            status
        )

        return redirect("/appointments")

    return render_template(
        "add_appointment.html",
        clients=get_clients(business_id),
        selected_date=selected_date
    )


# ---------------------------------------------------------
# EDIT APPOINTMENT
# ---------------------------------------------------------

@app.route(
    "/edit-appointment/<int:appointment_id>",
    methods=["GET", "POST"]
)
def edit_appointment(appointment_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    appointment = get_appointment(
        appointment_id,
        business_id
    )

    if not appointment:
        return "Appointment not found", 404

    if request.method == "POST":

        client_id = request.form.get(
            "client_id"
        )

        appointment_date = request.form.get(
            "appointment_date"
        )

        appointment_time = request.form.get(
            "appointment_time"
        )

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        status = request.form.get(
            "status",
            "Upcoming"
        )

        if not client_id:
            return render_template(
                "edit_appointment.html",
                appointment=appointment,
                clients=get_clients(business_id),
                error="Please select a client."
            )

        client = get_client(
            int(client_id),
            business_id
        )

        if not client:
            return "Client not found", 404

        update_appointment(
            appointment_id,
            business_id,
            int(client_id),
            appointment_date,
            appointment_time,
            notes,
            status
        )

        return redirect("/appointments")

    return render_template(
        "edit_appointment.html",
        appointment=appointment,
        clients=get_clients(business_id)
    )


# ---------------------------------------------------------
# DELETE APPOINTMENT
# ---------------------------------------------------------

@app.route(
    "/delete-appointment/<int:appointment_id>"
)
def delete_appointment_route(appointment_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    appointment = get_appointment(
        appointment_id,
        business_id
    )

    if not appointment:
        return "Appointment not found", 404

    delete_appointment(
        appointment_id,
        business_id
    )

    return redirect("/appointments")


# ---------------------------------------------------------
# LEADS
# ---------------------------------------------------------

@app.route("/leads")
def leads():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    search = request.args.get(
        "search",
        ""
    ).strip()

    leads = get_leads(
        business_id,
        search
    )

    analytics = get_lead_analytics(
        business_id
    )
    today = date.today().isoformat()

    return render_template(
        "leads.html",
        leads=leads,
        analytics=analytics,
        search=search,
        today=today
    )


# ---------------------------------------------------------
# ADD LEAD
# ---------------------------------------------------------

@app.route("/add-lead", methods=["GET", "POST"])
def add_lead_route():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    if request.method == "POST":

        lead_name = request.form.get(
            "lead_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        source = request.form.get(
            "source",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        interest_level = request.form.get(
            "interest_level",
            "Medium"
        )

        status = request.form.get(
            "status",
            "New"
        )

        if not lead_name:
            return render_template(
                "leads.html",
                error="Lead name is required."
            )

        if email and not is_valid_email(email):
            return render_template(
                "leads.html",
                error="Please enter a valid email address."
            )

        add_lead(
            business_id,
            lead_name,
            email,
            phone,
            source,
            notes,
            interest_level,
            status
        )

        return redirect("/leads")

    return render_template("add_lead.html")


# ---------------------------------------------------------
# LEAD PROFILE
# ---------------------------------------------------------
@app.route("/lead/<int:lead_id>")
def lead_profile(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    communications = get_lead_communications(
        lead_id,
        business_id
    )

    return render_template(
        "lead_profile.html",
        lead=lead,
        communications=communications
    )
# ---------------------------------------------------------
# GENERATE AI FOLLOW-UP
# ---------------------------------------------------------

@app.route("/lead/<int:lead_id>/generate-follow-up", methods=["POST"])
def generate_lead_follow_up(lead_id):
    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(lead_id, business_id)

    if not lead:
        return "Lead not found", 404

    business_name = session.get("business_name","the business")

    try:
        ai_follow_up = generate_follow_up(
            lead["lead_name"],
            lead["notes"],
            lead["status"],
            lead["last_contacted"],
            business_name
        )

    except Exception as e:
        communications = get_lead_communications(
            lead_id,
            business_id
        )

        return render_template(
            "lead_profile.html",
            lead=lead,
            communications=communications,
            ai_reply=None,
            ai_follow_up=None,
            error=(
                "Unable to generate an AI follow-up. "
                "Please make sure Ollama is running."
            )
        )

    communications = get_lead_communications(
        lead_id,
        business_id
    )

    return render_template(
        "lead_profile.html",
        lead=lead,
        communications=communications,
        ai_reply=None,
        ai_follow_up=ai_follow_up
    )
# =========================
# GENERATE AI LEAD REPLY
# =========================

@app.route("/lead/<int:lead_id>/generate-reply", methods=["POST"])
def generate_ai_reply(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    lead_name = lead["lead_name"]

    notes = lead["notes"] or (
        "No notes have been provided."
    )

    business_name = session.get(
        "business_name",
        "the business"
    )

    try:

        ai_reply = generate_lead_reply(
            lead_name,
            notes,
            business_name
        )

    except Exception as e:

        print("AI generation error:", e)

        return render_template(
            "lead_profile.html",
            lead=lead,
            ai_reply=None,
            error=(
                "Unable to generate an AI response. "
                "Please make sure Ollama is running."
            )
        )

    return render_template(
        "lead_profile.html",
        lead=lead,
        ai_reply=ai_reply,
        ai_follow_up=None
    )
# --------------------------------------------------------
# SEND EMAIL TO LEAD
# --------------------------------------------------------
@app.route("/lead/<int:lead_id>/send-email", methods=["POST"])
def send_lead_email(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    recipient = (lead["email"] or "").strip()
    message = request.form.get("message", "").strip()

    if not recipient:
        return render_template(
            "lead_profile.html",
            lead=lead,
            ai_reply=message,
            error="This lead does not have an email address."
        )

    if not is_valid_email(recipient):
        return render_template(
            "lead_profile.html",
            lead=lead,
            ai_reply=message,
            error="This lead has an invalid email address."
        )

    if not message:
        return render_template(
            "lead_profile.html",
            lead=lead,
            ai_reply=message,
            error="Please enter a message before sending."
        )

    business_name = session.get(
        "business_name",
        "CoachFlow"
    )

    subject = f"Message from {business_name}"

    try:

        response = send_email(
            recipient,
            subject,
            message
        )

        provider_id = None

        if isinstance(response, dict):
            provider_id = response.get("id")

        add_communication(
            business_id=business_id,
            lead_id=lead_id,
            channel="email",
            recipient=recipient,
            subject=subject,
            message=message,
            sent_at=datetime.now().isoformat(),
            status="sent",
            ai_generated=True,
            provider_id=provider_id
        )
        update_lead_last_contacted(lead_id,
                                   business_id,
                                   date.today().isoformat()
        )

    except Exception as e:

        print("Email sending error:", e)

        return render_template(
            "lead_profile.html",
            lead=lead,
            ai_reply=message,
            error=(
                "Unable to send the email. "
                "Please check your Resend configuration."
            )
        )

    return redirect(f"/lead/{lead_id}")

# ---------------------------------------------------------
# EDIT LEAD
# ---------------------------------------------------------

@app.route(
    "/edit-lead/<int:lead_id>",
    methods=["GET", "POST"]
)
def edit_lead(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    if request.method == "POST":

        lead_name = request.form.get(
            "lead_name",
            ""
        ).strip()

        email = request.form.get(
            "email",
            ""
        ).strip()

        phone = request.form.get(
            "phone",
            ""
        ).strip()

        source = request.form.get(
            "source",
            ""
        ).strip()

        notes = request.form.get(
            "notes",
            ""
        ).strip()

        interest_level = request.form.get(
            "interest_level",
            "Medium"
        )

        status = request.form.get(
            "status",
            "New"
        )

        if not lead_name:
            return render_template(
                "edit_lead.html",
                lead=lead,
                error="Lead name is required."
            )

        if email and not is_valid_email(email):
            return render_template(
                "edit_lead.html",
                lead=lead,
                error="Please enter a valid email address."
            )

        update_lead(
            lead_id,
            business_id,
            lead_name,
            email,
            phone,
            source,
            notes,
            interest_level,
            status
        )

        return redirect(
            f"/lead/{lead_id}"
        )

    return render_template(
        "edit_lead.html",
        lead=lead
    )


# ---------------------------------------------------------
# DELETE LEAD
# ---------------------------------------------------------

@app.route("/delete-lead/<int:lead_id>")
def delete_lead_route(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    delete_lead(
        lead_id,
        business_id
    )

    return redirect("/leads")


# ---------------------------------------------------------
# CONVERT LEAD TO CLIENT
# ---------------------------------------------------------

@app.route("/convert-lead/<int:lead_id>")
def convert_lead(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    convert_lead_to_client(
        lead_id,
        business_id
    )

    return redirect("/clients")


# ---------------------------------------------------------
# LEAD CHART
# ---------------------------------------------------------

@app.route("/lead-chart")
def lead_chart():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    analytics = get_lead_analytics(
        business_id
    )

    return render_template(
        "lead_chart.html",
        analytics=analytics
    )


# ---------------------------------------------------------
# LEAD FOLLOW-UP
# ---------------------------------------------------------

@app.route("/lead/<int:lead_id>/follow-up")
def lead_follow_up(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    add_follow_up(
        lead_id,
        business_id
    )

    return redirect(
        f"/lead/{lead_id}"
    )


# ---------------------------------------------------------
# ANALYTICS
# ---------------------------------------------------------

@app.route("/analytics")
def analytics():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    total_revenue = get_total_revenue(
        business_id
    )

    revenue_statistics = get_revenue_statistics(
        business_id
    )

    lead_analytics = get_lead_analytics(
        business_id
    )

    return render_template(
        "analytics.html",
        total_revenue=total_revenue,
        revenue_stats=revenue_statistics,
        lead_analytics=lead_analytics
    )
# ---------------------------------------------------------
# FOLLOW UPS
# ---------------------------------------------------------
@app.route("/follow-ups")
def follow_ups():

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    follow_ups = get_follow_up_leads(business_id)

    overdue = []
    today = []
    upcoming = []

    current_date = date.today()

    for lead in follow_ups:

        if not lead["next_follow_up"]:
            continue

        follow_up_date = date.fromisoformat(
            lead["next_follow_up"]
        )

        if follow_up_date < current_date:

            overdue.append(lead)

        elif follow_up_date == current_date:

            today.append(lead)

        else:

            upcoming.append(lead)

    return render_template(
        "follow_ups.html",
        overdue=overdue,
        today=today,
        upcoming=upcoming
    )


# ---------------------------------------------------------
# LOGOUT
# ---------------------------------------------------------

@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")


# ---------------------------------------------------------
# ERROR HANDLERS
# ---------------------------------------------------------

@app.errorhandler(404)
def page_not_found(error):

    return """
    <div style="
        font-family: Arial;
        text-align: center;
        padding: 80px;
    ">
        <h1>404</h1>
        <h2>Page not found</h2>
        <p>The page you are looking for does not exist.</p>
        <a href="/">Return to CoachFlow</a>
    </div>
    """, 404


@app.errorhandler(500)
def internal_server_error(error):

    return """
    <div style="
        font-family: Arial;
        text-align: center;
        padding: 80px;
    ">
        <h1>500</h1>
        <h2>Something went wrong</h2>
        <p>Please try again.</p>
        <a href="/">Return to CoachFlow</a>
    </div>
    """, 500
# ---------------------------------------------------------
# AUTOMATED FOLLOW-UP SCHEDULING
# ---------------------------------------------------------

@app.route(
    "/lead/<int:lead_id>/schedule-follow-up",
    methods=["POST"]
)
def schedule_lead_follow_up(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    next_follow_up = request.form.get(
        "next_follow_up",
        ""
    ).strip()

    interval_days = request.form.get(
        "interval_days",
        "3"
    ).strip()

    try:

        interval_days = int(interval_days)

    except ValueError:

        interval_days = 3

    if interval_days < 1:
        interval_days = 1

    if interval_days > 30:
        interval_days = 30

    if not next_follow_up:

        communications = get_lead_communications(
            lead_id,
            business_id
        )

        return render_template(
            "lead_profile.html",
            lead=lead,
            communications=communications,
            error="Please select a follow-up date."
        )

    schedule_follow_up(
        lead_id,
        business_id,
        next_follow_up,
        interval_days
    )

    return redirect(
        f"/lead/{lead_id}"
    )


# ---------------------------------------------------------
# DISABLE AUTOMATED FOLLOW-UP
# ---------------------------------------------------------

@app.route(
    "/lead/<int:lead_id>/disable-follow-up",
    methods=["POST"]
)
def disable_lead_follow_up(lead_id):

    business_id = get_logged_in_business_id()

    if not business_id:
        return redirect("/")

    lead = get_lead(
        lead_id,
        business_id
    )

    if not lead:
        return "Lead not found", 404

    disable_follow_up(
        lead_id,
        business_id
    )

    return redirect(
        f"/lead/{lead_id}"
    )


# ---------------------------------------------------------
# RUN APPLICATION
# ---------------------------------------------------------

if __name__ == "__main__":
    csrf = CSRFProtect(app)
    if(
        not app.debug
        or os.environ.get("WERKZEUG_RUN_MAIN")  == "true"
    ):
        start_scheduler()
    app.run(debug=True)