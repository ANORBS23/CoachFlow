import os
import html
import resend


resend.api_key = os.environ["RESEND_API_KEY"]


def send_email(to_email, subject, message):

    safe_message = html.escape(message).replace("\n", "<br>")

    response = resend.Emails.send({
        "from": "CoachFlow <onboarding@resend.dev>",
        "to": [to_email],
        "subject": subject,
        "html": f"<p>{safe_message}</p>"
    })

    return response