# Barbershop SMS Scheduler

An SMS-based agentic scheduling system for a barbershop, built with FastAPI, pydantic-ai, and Twilio.

Customers can text the barbershop to check barber availability, book appointments, and save their preferred haircut style. The system remembers preferences and conversation context across messages.

## Architecture

```
Customer SMS → Twilio → ngrok → FastAPI /sms/reply
  → Load conversation history (SQLite)
  → Load customer preferences
  → pydantic-ai Agent (Gemini) with scheduling tools
  → Agent calls tools: check_availability / book_appointment / save_preference
  → Response → TwiML XML → Twilio → SMS back to customer
```

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

## SMS Flow Example

```
Customer: "Can I get a haircut this week?"
System:   Checks availability → "Carlos has openings Thursday at 10:00, 10:30, 14:00..."

Customer: "Book me with Carlos at 10am Thursday"
System:   Books appointment → "You're booked with Carlos on Thursday at 10:00 AM!"

System:   "What type of cut would you like? (fade, buzz cut, classic...)"
Customer: "I usually get a fade"
System:   Saves preference → "Got it! I'll remember you prefer a fade."

--- Next time ---
Customer: "I need a haircut"
System:   "Welcome back! Last time you got a fade. Want the same?"
```

## Design Decisions

See [DESIGN.md](DESIGN.md) for architectural decisions and tradeoffs.

## Project Structure

```
src/
├── main.py              # FastAPI app, lifespan, routers
├── core/
│   └── config.py        # Settings (pydantic-settings)
├── sms/
│   ├── api.py           # POST /sms/reply webhook handler
│   └── models.py        # SMSRequest/SMSResponse
├── db/
│   ├── database.py      # SQLAlchemy engine, session, init
│   ├── models.py        # Barber, Appointment, Preference, Message
│   └── seed.py          # Initial barber data
├── scheduling/
│   ├── tools.py         # Agent tools: availability, booking, preferences
│   ├── reminders.py     # 90-day reminder background task
│   └── api.py           # /reminders/check endpoint
└── tests/
    └── test_e2e_scheduling.py
```

## Available Commands

Run `make help` to see all available Makefile commands.
