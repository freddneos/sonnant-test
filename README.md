# Messaging API

A Python/FastAPI application for receiving SMS messages via Twilio webhooks and generating AI-powered responses using Google Gemini.

## Requirements

- Python 3.11
- Docker & Docker Compose
- [ngrok](https://ngrok.com/) account (for Twilio webhook delivery)
- [Google AI Studio](https://aistudio.google.com/) account (Gemini API key)
- [Twilio](https://www.twilio.com/) account (for SMS)

## Environment Setup

Copy the example env file and fill in your credentials:

```bash
cp .env.example .env
# Edit .env with your values
```

Or export them in your shell:

```bash
export MESSAGING_API_NGROK_AUTHTOKEN=your_token
export MESSAGING_API_NGROK_DOMAIN=your-domain.ngrok-free.app
export GEMINI_API_KEY=your_gemini_key
export MESSAGING_API_TWILIO_AUTH_TOKEN=your_twilio_token
```

**Note:** `GEMINI_API_KEY` is mapped to `GOOGLE_API_KEY` inside the container, which is what pydantic-ai reads.

## Local Development

```bash
make local-bootstrap          # Create Python virtualenv
source venv/bin/activate      # Activate it
make local-init               # Install dependencies + pre-commit hooks
```

## Run with Docker

```bash
make compose-build            # Build container images
make compose-run              # Start API + ngrok containers
```

The API is available at `http://localhost:9000`. ngrok dashboard at `http://localhost:4040`.

## Run Tests

```bash
make compose-test             # Run pytest inside Docker
```

Or locally:

```bash
pytest -vv
```

## Available Commands

Run `make help` to see all available Makefile commands.
