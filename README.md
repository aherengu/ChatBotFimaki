# ChatBotFimaki

ChatBotFimaki is a small Flask API for running a Fimaki Games assistant with OpenAI Assistants and optional Airtable lead capture.

## Security and Privacy Warning

This project may process user messages. Do not deploy it publicly without authentication, rate limiting, HTTPS, and a privacy policy. Do not log private user messages in production.

By default the server binds to `127.0.0.1` for local development. Public hosting should only be enabled intentionally with `HOST=0.0.0.0` and proper deployment controls.

## Setup

1. Create and activate a Python virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

3. Copy `.env.example` to `.env` and fill in your own values. Do not commit `.env`.
4. Configure your own Airtable base and table if you want CRM lead capture. A public Airtable template is not included.
5. Start the server:

```bash
python main.py
```

The default local URL is `http://127.0.0.1:8080`.

## Environment

Use `.env.example` as the safe template. It contains placeholders only:

```text
OPENAI_API_KEY=
AIRTABLE_API_KEY=
AIRTABLE_BASE_ID=
AIRTABLE_TABLE_NAME=Leads
CHATBOT_API_KEY=
HOST=127.0.0.1
PORT=8080
```

If `CHATBOT_API_KEY` is set, `/start` and `/chat` require either:

```text
Authorization: Bearer <key>
```

or:

```text
X-API-Key: <key>
```

If `CHATBOT_API_KEY` is not set, local development remains usable, but public deployment is unsafe.

## API

Start a thread:

```bash
curl http://127.0.0.1:8080/start
```

Send a message:

```bash
curl -X POST http://127.0.0.1:8080/chat \
  -H "Content-Type: application/json" \
  -d '{"thread_id":"<thread_id>","message":"Hello"}'
```

## License

The source code is licensed under the Apache License 2.0. See `LICENSE`.