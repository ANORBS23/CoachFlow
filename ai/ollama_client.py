from ollama import chat


def generate_lead_reply(lead_name, notes, business_name):

    prompt = f"""
You are an AI assistant for a professional business called {business_name}.

Your job is to write a natural, professional reply to a potential customer.

Customer name:
{lead_name}

Information and notes about the customer's enquiry:
{notes if notes else "No notes have been provided."}

Use the information in the notes to understand what the customer is asking about
and write an appropriate response.

Requirements:
- Address the customer's enquiry directly.
- Use relevant information from the notes.
- Sound natural, friendly and professional.
- Keep the response concise.
- If the notes contain a question, answer it where possible.
- If the notes do not provide enough information to answer something, ask the customer for the missing information.
- Do not invent prices, availability, services, discounts or promises.
- Do not mention that you are an AI.
- End the response in a professional manner thanking them and that you hope to hear back from the future

Write ONLY the message that should be sent to the customer.

Do not include:
- An explanation of the response
- Commentary about the response
- Notes for the business owner
- A heading such as "Proposed response"
- Quotation marks around the response
- Any text before or after the customer message

Your entire output must be the exact customer message that can be copied and sent directly.
"""

    response = chat(
        model="llama3.2:3b",
        messages=[
            {
                "role": "user",
                "content": prompt
            }
        ]
    )

    return response["message"]["content"]

def generate_follow_up(lead_name, notes, status, last_contacted, business_name):
    prompt = f"""
You are an AI assistant for a professional business called {business_name}.

Write a short, natural follow-up message to a potential customer who has previously
shown interest in the business.

Customer name:
{lead_name}

Customer enquiry/notes:
{notes if notes else "No notes have been provided."}

Current lead status:
{status}

Last contacted:
{last_contacted if last_contacted else "The customer has not previously been contacted."}

Requirements:
- Address the customer by name.
- Follow up naturally on their previous enquiry.
- Sound friendly, professional and helpful.
- Keep the message concise.
- Encourage the customer to respond.
- Do not be pushy.
- Do not invent prices, availability, discounts, services or promises.
- Do not mention that you are an AI.
- Do not mention information that is not provided above.

Write ONLY the message that should be sent to the customer.

Do not include:
- An explanation
- A heading
- Quotation marks
- Commentary
- Anything before or after the customer message
"""

    response = chat(
        model="llama3.2:3b",
        messages=[
            {"role": "user", "content": prompt}
        ]
    )

    return response["message"]["content"]