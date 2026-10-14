import time
import threading
from datetime import date, timedelta, datetime

from ai.ollama_client import generate_follow_up
from services.resend_client import send_email

from database.database import (
    get_due_follow_ups,
    add_communication,
    complete_automated_follow_up
)


MAX_AUTOMATED_FOLLOW_UPS = 3


def process_due_follow_up(lead):

    lead_id = lead["id"]
    business_id = lead["business_id"]

    print(
        f"[CoachFlow] Processing automated follow-up "
        f"for lead {lead_id}..."
    )

    try:

        business_name = "CoachFlow"

        message = generate_follow_up(
            lead["lead_name"],
            lead["notes"],
            lead["status"],
            lead["last_contacted"],
            business_name
        )

        subject = f"Following up with {lead['lead_name']}"

        response = send_email(
            lead["email"],
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
            recipient=lead["email"],
            subject=subject,
            message=message,
            sent_at=datetime.now().isoformat(),
            status="sent",
            ai_generated=True,
            provider_id=provider_id
        )

        current_count = lead["follow_up_count"] or 0
        new_count = current_count + 1

        today = date.today().isoformat()

        # -------------------------------------------------
        # Stop automation after maximum follow-ups
        # -------------------------------------------------

        if new_count >= MAX_AUTOMATED_FOLLOW_UPS:

            complete_automated_follow_up(
                lead_id,
                business_id,
                today,
                None,
                new_count,
                0
            )

            print(
                f"[CoachFlow] Lead {lead_id} completed "
                f"automated follow-up sequence."
            )

            return

        # -------------------------------------------------
        # Schedule next follow-up
        # -------------------------------------------------

        interval = lead["follow_up_interval"] or 3

        next_date = (
            date.today()
            + timedelta(days=interval)
        ).isoformat()

        complete_automated_follow_up(
            lead_id,
            business_id,
            today,
            next_date,
            new_count,
            1
        )

        print(
            f"[CoachFlow] Follow-up sent to "
            f"{lead['email']}. "
            f"Next follow-up: {next_date}"
        )

    except Exception as error:

        print(
            f"[CoachFlow] Automated follow-up failed "
            f"for lead {lead_id}: {error}"
        )


def check_for_due_follow_ups():

    leads = get_due_follow_ups()

    if not leads:
        return

    print(
        f"[CoachFlow] Found {len(leads)} due follow-up(s)."
    )

    for lead in leads:

        process_due_follow_up(lead)


def scheduler_loop():

    print(
        "[CoachFlow] Automated follow-up scheduler started."
    )

    while True:

        try:

            check_for_due_follow_ups()

        except Exception as error:

            print(
                f"[CoachFlow] Scheduler error: {error}"
            )

        # Check once every minute
        time.sleep(60)


def start_scheduler():

    scheduler_thread = threading.Thread(
        target=scheduler_loop,
        daemon=True
    )

    scheduler_thread.start()

    return scheduler_thread