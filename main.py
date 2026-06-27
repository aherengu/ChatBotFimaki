import hmac
import json
import os
import time

from dotenv import load_dotenv
from flask import Flask, jsonify, request
from openai import OpenAI
from waitress import serve

import custom_functions

load_dotenv()

app = Flask(__name__)
client = OpenAI()
assistant_id = custom_functions.create_assistant(client)

CHATBOT_API_KEY = os.getenv("CHATBOT_API_KEY", "").strip()
HOST = os.getenv("HOST", "127.0.0.1").strip() or "127.0.0.1"
PORT = int(os.getenv("PORT", "8080"))

if not CHATBOT_API_KEY:
    print("WARNING: CHATBOT_API_KEY is not set. Local development is allowed, but public deployment is unsafe.")

if HOST in {"0.0.0.0", "::"}:
    print("WARNING: Server is configured for external binding. Use HTTPS, authentication, rate limiting, and a privacy policy.")


def is_authorized_request():
    if not CHATBOT_API_KEY:
        return True

    auth_header = request.headers.get("Authorization", "")
    bearer_prefix = "Bearer "
    if auth_header.startswith(bearer_prefix):
        candidate = auth_header[len(bearer_prefix):].strip()
    else:
        candidate = request.headers.get("X-API-Key", "").strip()

    return hmac.compare_digest(candidate, CHATBOT_API_KEY)


def require_api_key():
    if is_authorized_request():
        return None
    return jsonify({"error": "Unauthorized"}), 401


@app.route('/start', methods=['GET'])
def start_conversation():
    auth_error = require_api_key()
    if auth_error:
        return auth_error

    print("Starting a new conversation.")
    thread = client.beta.threads.create()
    print("Conversation thread created.")
    return jsonify({"thread_id": thread.id})


@app.route('/chat', methods=['POST'])
def chat():
    auth_error = require_api_key()
    if auth_error:
        return auth_error

    data = request.get_json(silent=True) or {}
    thread_id = data.get('thread_id')
    user_input = data.get('message', '')

    if not thread_id:
        print("Rejected chat request: missing thread_id.")
        return jsonify({"error": "Missing thread_id"}), 400

    print("Received chat request.")

    client.beta.threads.messages.create(
        thread_id=thread_id,
        role="user",
        content=user_input
    )

    run = client.beta.threads.runs.create(
        thread_id=thread_id,
        assistant_id=assistant_id
    )

    while True:
        run_status = client.beta.threads.runs.retrieve(
            thread_id=thread_id,
            run_id=run.id
        )

        if run_status.status == 'completed':
            break

        if run_status.status == 'requires_action':
            for tool_call in run_status.required_action.submit_tool_outputs.tool_calls:
                if tool_call.function.name == "create_lead":
                    arguments = json.loads(tool_call.function.arguments)
                    name = arguments.get('name', '')
                    company_name = arguments.get('company_name', '')
                    phone = arguments.get('phone', '')
                    email = arguments.get('email', '')

                    output = custom_functions.create_lead(name, company_name, phone, email)
                    client.beta.threads.runs.submit_tool_outputs(
                        thread_id=thread_id,
                        run_id=run.id,
                        tool_outputs=[{
                            "tool_call_id": tool_call.id,
                            "output": json.dumps(output)
                        }]
                    )

        time.sleep(1)

    messages = client.beta.threads.messages.list(thread_id=thread_id)
    response = messages.data[0].content[0].text.value

    print("Assistant response generated.")
    return jsonify({"response": response})


if __name__ == '__main__':
    print(f"Starting server on {HOST}:{PORT}.")
    serve(app, host=HOST, port=PORT)