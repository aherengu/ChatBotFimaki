import json
import os
from urllib.parse import quote

import requests
from openai import OpenAI
from assistant_instructions import assistant_instructions
from dotenv import load_dotenv

load_dotenv()

# Init OpenAI Client
client = OpenAI()


def create_lead(name="", company_name="", phone="", email=""):
    airtable_api_key = os.getenv("AIRTABLE_API_KEY", "").strip()
    airtable_base_id = os.getenv("AIRTABLE_BASE_ID", "").strip()
    airtable_table_name = os.getenv("AIRTABLE_TABLE_NAME", "Leads").strip()

    if not airtable_api_key or not airtable_base_id or not airtable_table_name:
        print("Lead capture skipped: Airtable configuration is incomplete.")
        return {"status": "error", "message": "CRM is not configured."}

    url = f"https://api.airtable.com/v0/{airtable_base_id}/{quote(airtable_table_name, safe='')}"
    headers = {
        "Authorization": f"Bearer {airtable_api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "records": [{
            "fields": {
                "Name": name,
                "Phone": phone,
                "Email": email,
                "CompanyName": company_name,
            }
        }]
    }

    response = requests.post(url, headers=headers, json=data, timeout=20)
    if response.status_code in (200, 201):
        print("Lead created successfully.")
        return {"status": "created"}

    print(f"Lead creation failed with status {response.status_code}.")
    return {"status": "error", "message": "Could not create lead."}


def create_assistant(client):
    assistant_file_path = 'assistant.json'

    # If there is an assistant.json file already, then load that assistant
    if os.path.exists(assistant_file_path):
        with open(assistant_file_path, 'r', encoding='utf-8') as file:
            assistant_data = json.load(file)
            assistant_id = assistant_data['assistant_id']
            print("Loaded existing assistant configuration.")
    else:
        # If no assistant.json is present, create a new assistant using the below specifications
        file = client.files.create(file=open("knowledge.docx", "rb"), purpose='assistants')

        assistant = client.beta.assistants.create(
            name="FimakAI",
            instructions=assistant_instructions,
            model="gpt-4o-mini",
            tools=[
                {
                    "type": "file_search"
                },
                {
                    "type": "function",
                    "function": {
                        "name": "create_lead",
                        "description": "Save consent-based follow-up contact details to Airtable.",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "description": "Name of the lead."
                                },
                                "phone": {
                                    "type": "string",
                                    "description": "Optional phone number of the lead."
                                },
                                "email": {
                                    "type": "string",
                                    "description": "Email address of the lead."
                                },
                                "company_name": {
                                    "type": "string",
                                    "description": "Company name of the lead."
                                }
                            },
                            "required": ["name", "email", "company_name"]
                        }
                    }
                }
            ],
            tool_resources={
                "file_search": {
                    "vector_stores": [{"file_ids": [file.id]}]
                }
            }
        )

        # Save assistant details to a json file
        with open(assistant_file_path, 'w', encoding='utf-8') as file:
            json.dump({'assistant_id': assistant.id}, file)
            print("Created a new assistant configuration.")

        assistant_id = assistant.id

    return assistant_id