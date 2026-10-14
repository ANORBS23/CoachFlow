import sqlite3
from datetime import date


# =========================================================
# DATABASE CONNECTION
# =========================================================

def get_db_connection():

    conn = sqlite3.connect(
        "database/database.db"
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================================================
# CREATE DATABASE
# =========================================================

def create_database():

    conn = get_db_connection()

    cursor = conn.cursor()

    # -----------------------------------------------------
    # Businesses
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS businesses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_name TEXT NOT NULL,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )

    # -----------------------------------------------------
    # Clients
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            client_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            goal TEXT NOT NULL,
            notes TEXT NOT NULL,
            revenue REAL DEFAULT 0,
            FOREIGN KEY (business_id)
                REFERENCES businesses(id)
        )
        """
    )

    # -----------------------------------------------------
    # Appointments
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            client_id INTEGER NOT NULL,
            appointment_date TEXT NOT NULL,
            appointment_time TEXT NOT NULL,
            notes TEXT,
            status TEXT NOT NULL DEFAULT 'Upcoming',
            FOREIGN KEY (business_id)
                REFERENCES businesses(id),
            FOREIGN KEY (client_id)
                REFERENCES clients(id)
        )
        """
    )

    # -----------------------------------------------------
    # Leads
    # -----------------------------------------------------

    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            lead_name TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            source TEXT,
            notes TEXT,
            interest_level TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            last_contacted TEXT,
            next_follow_up TEXT,
            FOREIGN KEY (business_id)
                REFERENCES businesses(id)
        )
        """
    )

    conn.commit()
    conn.close()


# =========================================================
# APPOINTMENT STATUS MIGRATION
# =========================================================

def add_appointment_status_column():

    connection = get_db_connection()

    columns = connection.execute(
        "PRAGMA table_info(appointments)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if "status" not in column_names:

        connection.execute(
            """
            ALTER TABLE appointments
            ADD COLUMN status TEXT
            NOT NULL DEFAULT 'Upcoming'
            """
        )

    connection.commit()
    connection.close()


def add_appoitment_status_column():

    add_appointment_status_column()


# =========================================================
# REVENUE MIGRATION
# =========================================================

def add_revenue_column():

    connection = get_db_connection()

    columns = connection.execute(
        "PRAGMA table_info(clients)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if "revenue" not in column_names:

        connection.execute(
            """
            ALTER TABLE clients
            ADD COLUMN revenue REAL DEFAULT 0
            """
        )

    connection.commit()
    connection.close()


# =========================================================
# FOLLOW-UP MIGRATION
# =========================================================

def add_follow_up_columns():

    connection = get_db_connection()

    columns = connection.execute(
        "PRAGMA table_info(leads)"
    ).fetchall()

    column_names = [
        column["name"]
        for column in columns
    ]

    if "last_contacted" not in column_names:

        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN last_contacted TEXT
            """
        )

    if "next_follow_up" not in column_names:

        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN next_follow_up TEXT
            """
        )

    if "follow_up_enabled" not in column_names:

        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN follow_up_enabled INTEGER
            NOT NULL DEFAULT 0
            """
        )

    if "follow_up_count" not in column_names:

        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN follow_up_count INTEGER
            NOT NULL DEFAULT 0
            """
        )

    if "follow_up_interval" not in column_names:

        connection.execute(
            """
            ALTER TABLE leads
            ADD COLUMN follow_up_interval INTEGER
            NOT NULL DEFAULT 3
            """
        )

    connection.commit()
    connection.close()


# =========================================================
# BUSINESS METHODS
# =========================================================

def add_business(
    business_name,
    email,
    password_hash
):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO businesses (
            business_name,
            email,
            password_hash
        )
        VALUES (?, ?, ?)
        """,
        (
            business_name,
            email,
            password_hash
        )
    )

    connection.commit()
    connection.close()


def create_business(
    business_name,
    email,
    password_hash
):

    add_business(
        business_name,
        email,
        password_hash
    )


def get_business_by_email(email):

    connection = get_db_connection()

    business = connection.execute(
        """
        SELECT *
        FROM businesses
        WHERE LOWER(email) = LOWER(?)
        """,
        (email,)
    ).fetchone()

    connection.close()

    return business


# =========================================================
# CLIENT METHODS
# =========================================================

def add_client(
    business_id,
    client_name,
    email,
    phone,
    goal,
    notes,
    revenue=0
):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO clients (
            business_id,
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue
        )
    )

    connection.commit()
    connection.close()


def get_clients(
    business_id,
    search=""
):

    connection = get_db_connection()

    query = """
        SELECT *
        FROM clients
        WHERE business_id = ?
    """

    parameters = [business_id]

    if search:

        query += """
            AND (
                client_name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
            )
        """

        search_term = f"%{search}%"

        parameters.extend([
            search_term,
            search_term,
            search_term
        ])

    query += """
        ORDER BY client_name ASC
    """

    clients = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return clients


def get_client(
    client_id,
    business_id
):

    connection = get_db_connection()

    client = connection.execute(
        """
        SELECT *
        FROM clients
        WHERE id = ?
        AND business_id = ?
        """,
        (
            client_id,
            business_id
        )
    ).fetchone()

    connection.close()

    return client


def update_client(
    client_id,
    business_id,
    client_name,
    email,
    phone,
    goal,
    notes,
    revenue
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE clients

        SET
            client_name = ?,
            email = ?,
            phone = ?,
            goal = ?,
            notes = ?,
            revenue = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue,
            client_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def delete_client(
    client_id,
    business_id
):

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM appointments
        WHERE client_id = ?
        AND business_id = ?
        """,
        (
            client_id,
            business_id
        )
    )

    connection.execute(
        """
        DELETE FROM clients
        WHERE id = ?
        AND business_id = ?
        """,
        (
            client_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# APPOINTMENT METHODS
# =========================================================

def add_appointment(
    business_id,
    client_id,
    appointment_date,
    appointment_time,
    notes,
    status="Upcoming"
):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO appointments (
            business_id,
            client_id,
            appointment_date,
            appointment_time,
            notes,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            client_id,
            appointment_date,
            appointment_time,
            notes,
            status
        )
    )

    connection.commit()
    connection.close()


def get_appointment(
    appointment_id,
    business_id
):

    connection = get_db_connection()

    appointment = connection.execute(
        """
        SELECT
            appointments.id,
            appointments.business_id,
            appointments.client_id,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.notes,
            appointments.status,
            clients.client_name

        FROM appointments

        JOIN clients
            ON appointments.client_id = clients.id

        WHERE appointments.id = ?
        AND appointments.business_id = ?
        """,
        (
            appointment_id,
            business_id
        )
    ).fetchone()

    connection.close()

    return appointment


def get_appointments(
    business_id,
    search="",
    date=""
):

    connection = get_db_connection()

    query = """
        SELECT
            appointments.id,
            appointments.business_id,
            appointments.client_id,
            appointments.appointment_date,
            appointments.appointment_time,
            appointments.notes,
            appointments.status,
            clients.client_name

        FROM appointments

        JOIN clients
            ON appointments.client_id = clients.id

        WHERE appointments.business_id = ?
    """

    parameters = [business_id]

    if search:

        query += """
            AND clients.client_name LIKE ?
        """

        parameters.append(
            f"%{search}%"
        )

    if date:

        query += """
            AND appointments.appointment_date = ?
        """

        parameters.append(date)

    query += """
        ORDER BY
            appointments.appointment_date ASC,
            appointments.appointment_time ASC
    """

    appointments = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return appointments


def update_appointment(
    appointment_id,
    business_id,
    client_id,
    appointment_date,
    appointment_time,
    notes,
    status
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE appointments

        SET
            client_id = ?,
            appointment_date = ?,
            appointment_time = ?,
            notes = ?,
            status = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            client_id,
            appointment_date,
            appointment_time,
            notes,
            status,
            appointment_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def delete_appointment(
    appointment_id,
    business_id
):

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM appointments
        WHERE id = ?
        AND business_id = ?
        """,
        (
            appointment_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# LEAD METHODS
# =========================================================

def add_lead(
    business_id,
    lead_name,
    email,
    phone,
    source,
    notes,
    interest_level,
    status
):

    connection = get_db_connection()

    connection.execute(
        """
        INSERT INTO leads (
            business_id,
            lead_name,
            email,
            phone,
            source,
            notes,
            interest_level,
            status,
            follow_up_enabled,
            follow_up_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0, 0)
        """,
        (
            business_id,
            lead_name,
            email,
            phone,
            source,
            notes,
            interest_level,
            status
        )
    )

    connection.commit()
    connection.close()


def get_leads(
    business_id,
    search="",
    status=""
):

    connection = get_db_connection()

    query = """
        SELECT *
        FROM leads
        WHERE business_id = ?
    """

    parameters = [business_id]

    if search:

        query += """
            AND (
                lead_name LIKE ?
                OR email LIKE ?
                OR phone LIKE ?
            )
        """

        search_term = f"%{search}%"

        parameters.extend([
            search_term,
            search_term,
            search_term
        ])

    if status:

        query += """
            AND status = ?
        """

        parameters.append(status)

    query += """
        ORDER BY created_at DESC
    """

    leads = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return leads


def get_lead(
    lead_id,
    business_id
):

    connection = get_db_connection()

    lead = connection.execute(
        """
        SELECT *
        FROM leads
        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    ).fetchone()

    connection.close()

    return lead


def update_lead(
    lead_id,
    business_id,
    lead_name,
    email,
    phone,
    source,
    notes,
    interest_level,
    status
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET
            lead_name = ?,
            email = ?,
            phone = ?,
            source = ?,
            notes = ?,
            interest_level = ?,
            status = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_name,
            email,
            phone,
            source,
            notes,
            interest_level,
            status,
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def delete_lead(
    lead_id,
    business_id
):

    connection = get_db_connection()

    connection.execute(
        """
        DELETE FROM communications
        WHERE lead_id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    )

    connection.execute(
        """
        DELETE FROM leads
        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# LEAD STATISTICS
# =========================================================

def get_lead_statistics(
    business_id
):

    connection = get_db_connection()

    total_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        """,
        (business_id,)
    ).fetchone()[0]

    new_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        AND status = 'New'
        """,
        (business_id,)
    ).fetchone()[0]

    contacted_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        AND status = 'Contacted'
        """,
        (business_id,)
    ).fetchone()[0]

    interested_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        AND status = 'Interested'
        """,
        (business_id,)
    ).fetchone()[0]

    converted_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        AND status = 'Converted'
        """,
        (business_id,)
    ).fetchone()[0]

    lost_leads = connection.execute(
        """
        SELECT COUNT(*)
        FROM leads
        WHERE business_id = ?
        AND status = 'Lost'
        """,
        (business_id,)
    ).fetchone()[0]

    connection.close()

    conversion_rate = (
        converted_leads / total_leads * 100
        if total_leads > 0
        else 0
    )

    return {
        "total": total_leads,
        "new": new_leads,
        "contacted": contacted_leads,
        "interested": interested_leads,
        "converted": converted_leads,
        "lost": lost_leads,
        "conversion_rate": conversion_rate
    }


# =========================================================
# LEAD ANALYTICS
# =========================================================

def get_lead_analytics(
    business_id
):

    connection = get_db_connection()

    total = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM leads
        WHERE business_id = ?
        """,
        (business_id,)
    ).fetchone()

    converted = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM leads
        WHERE business_id = ?
        AND status = 'Converted'
        """,
        (business_id,)
    ).fetchone()

    active = connection.execute(
        """
        SELECT COUNT(*) AS count
        FROM leads
        WHERE business_id = ?
        AND status != 'Converted'
        """,
        (business_id,)
    ).fetchone()

    sources = connection.execute(
        """
        SELECT
            COALESCE(NULLIF(source, ''), 'Unknown') AS source,
            COUNT(*) AS count
        FROM leads
        WHERE business_id = ?
        GROUP BY COALESCE(NULLIF(source, ''), 'Unknown')
        ORDER BY count DESC
        """,
        (business_id,)
    ).fetchall()

    statuses = connection.execute(
        """
        SELECT
            status,
            COUNT(*) AS count
        FROM leads
        WHERE business_id = ?
        GROUP BY status
        ORDER BY count DESC
        """,
        (business_id,)
    ).fetchall()

    connection.close()

    total_count = total["count"]
    converted_count = converted["count"]

    conversion_rate = (
        converted_count / total_count * 100
        if total_count > 0
        else 0
    )

    return {
        "total": total_count,
        "converted": converted_count,
        "active": active["count"],
        "conversion_rate": conversion_rate,
        "sources": sources,
        "statuses": statuses
    }


# =========================================================
# CONVERT LEAD TO CLIENT
# =========================================================

def convert_lead_to_client(
    lead_id,
    business_id
):

    connection = get_db_connection()

    lead = connection.execute(
        """
        SELECT *
        FROM leads
        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    ).fetchone()

    if not lead:
        connection.close()
        return False

    if lead["status"] == "Converted":
        connection.close()
        return False

    connection.execute(
        """
        INSERT INTO clients (
            business_id,
            client_name,
            email,
            phone,
            goal,
            notes,
            revenue
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            lead["lead_name"],
            lead["email"],
            lead["phone"],
            "",
            lead["notes"] or "",
            0
        )
    )

    connection.execute(
        """
        UPDATE leads
        SET
            status = 'Converted',
            follow_up_enabled = 0,
            next_follow_up = NULL

        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()

    return True


# =========================================================
# FOLLOW-UP METHODS
# =========================================================

def update_lead_follow_up(
    lead_id,
    business_id,
    last_contacted,
    next_follow_up
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET
            last_contacted = ?,
            next_follow_up = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            last_contacted,
            next_follow_up,
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def schedule_follow_up(
    lead_id,
    business_id,
    next_follow_up,
    interval_days=3
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET
            next_follow_up = ?,
            follow_up_enabled = 1,
            follow_up_count = 0,
            follow_up_interval = ?

        WHERE id = ?
        AND business_id = ?
        AND status NOT IN ('Converted', 'Lost')
        """,
        (
            next_follow_up,
            interval_days,
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def disable_follow_up(
    lead_id,
    business_id
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET
            follow_up_enabled = 0,
            next_follow_up = NULL

        WHERE id = ?
        AND business_id = ?
        """,
        (
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def add_follow_up(
    lead_id,
    business_id
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET last_contacted = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            date.today().isoformat(),
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


def get_follow_up_leads(
    business_id
):

    connection = get_db_connection()

    leads = connection.execute(
        """
        SELECT *
        FROM leads

        WHERE business_id = ?

        AND status IN (
            'New',
            'Contacted',
            'Interested'
        )

        ORDER BY
            CASE
                WHEN next_follow_up IS NOT NULL THEN 1
                ELSE 2
            END,
            next_follow_up ASC,
            created_at ASC
        """,
        (business_id,)
    ).fetchall()

    connection.close()

    return leads


def get_due_follow_ups(
    business_id=None
):

    connection = get_db_connection()

    query = """
        SELECT *
        FROM leads

        WHERE follow_up_enabled = 1

        AND next_follow_up IS NOT NULL

        AND next_follow_up <= date('now')

        AND status NOT IN (
            'Converted',
            'Lost'
        )

        AND email IS NOT NULL
        AND email != ''
    """

    parameters = []

    if business_id is not None:

        query += """
            AND business_id = ?
        """

        parameters.append(business_id)

    query += """
        ORDER BY next_follow_up ASC
    """

    leads = connection.execute(
        query,
        parameters
    ).fetchall()

    connection.close()

    return leads


def complete_automated_follow_up(
    lead_id,
    business_id,
    last_contacted,
    next_follow_up,
    follow_up_count,
    enabled
):

    connection = get_db_connection()

    connection.execute(
        """
        UPDATE leads

        SET
            last_contacted = ?,
            next_follow_up = ?,
            follow_up_count = ?,
            follow_up_enabled = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            last_contacted,
            next_follow_up,
            follow_up_count,
            enabled,
            lead_id,
            business_id
        )
    )

    connection.commit()
    connection.close()


# =========================================================
# REVENUE
# =========================================================

def get_total_revenue(
    business_id
):

    connection = get_db_connection()

    result = connection.execute(
        """
        SELECT
            COALESCE(SUM(revenue), 0) AS total_revenue
        FROM clients
        WHERE business_id = ?
        """,
        (business_id,)
    ).fetchone()

    connection.close()

    return result["total_revenue"]


def get_revenue_statistics(
    business_id
):

    connection = get_db_connection()

    total = connection.execute(
        """
        SELECT
            COALESCE(SUM(revenue), 0) AS total_revenue
        FROM clients
        WHERE business_id = ?
        """,
        (business_id,)
    ).fetchone()

    average = connection.execute(
        """
        SELECT
            COALESCE(AVG(revenue), 0) AS average_revenue
        FROM clients
        WHERE business_id = ?
        AND revenue > 0
        """,
        (business_id,)
    ).fetchone()

    highest = connection.execute(
        """
        SELECT
            client_name,
            revenue
        FROM clients
        WHERE business_id = ?
        ORDER BY revenue DESC
        LIMIT 5
        """,
        (business_id,)
    ).fetchall()

    connection.close()

    return {
        "total": total["total_revenue"],
        "average": average["average_revenue"],
        "highest": highest
    }


# =========================================================
# COMMUNICATIONS
# =========================================================

def create_communications_table():

    conn = get_db_connection()

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS communications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            business_id INTEGER NOT NULL,
            lead_id INTEGER NOT NULL,
            channel TEXT NOT NULL,
            recipient TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            sent_at TEXT NOT NULL,
            status TEXT NOT NULL,
            ai_generated INTEGER NOT NULL DEFAULT 0,
            provider_id TEXT,
            FOREIGN KEY (business_id)
                REFERENCES businesses(id),
            FOREIGN KEY (lead_id)
                REFERENCES leads(id)
        )
        """
    )

    conn.commit()
    conn.close()


def add_communication(
    business_id,
    lead_id,
    channel,
    recipient,
    subject,
    message,
    sent_at,
    status,
    ai_generated,
    provider_id=None
):

    conn = get_db_connection()

    conn.execute(
        """
        INSERT INTO communications (
            business_id,
            lead_id,
            channel,
            recipient,
            subject,
            message,
            sent_at,
            status,
            ai_generated,
            provider_id
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            business_id,
            lead_id,
            channel,
            recipient,
            subject,
            message,
            sent_at,
            status,
            ai_generated,
            provider_id
        )
    )

    conn.commit()
    conn.close()


def get_lead_communications(
    lead_id,
    business_id
):

    conn = get_db_connection()

    communications = conn.execute(
        """
        SELECT *
        FROM communications
        WHERE lead_id = ?
        AND business_id = ?
        ORDER BY sent_at DESC
        """,
        (
            lead_id,
            business_id
        )
    ).fetchall()

    conn.close()

    return communications


def update_lead_last_contacted(
    lead_id,
    business_id,
    contacted_date
):

    conn = get_db_connection()

    conn.execute(
        """
        UPDATE leads

        SET last_contacted = ?

        WHERE id = ?
        AND business_id = ?
        """,
        (
            contacted_date,
            lead_id,
            business_id
        )
    )

    conn.commit()
    conn.close()