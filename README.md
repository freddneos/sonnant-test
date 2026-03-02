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

**All environment variables are centralized in a single `.env` file** used by both Docker and local development.

```bash
cp .env.example .env
# Edit .env with your real credentials
```

The `.env` file contains unified variables (no duplication):

```bash
# Ngrok (optional - only for custom domains)
NGROK_AUTHTOKEN=your_ngrok_token

# Google AI - Gemini API
GOOGLE_API_KEY=AIzaSyBY...

# Twilio
TWILIO_AUTH_TOKEN=your_twilio_token
TWILIO_ACCOUNT_SID=ACxxx
TWILIO_PHONE_NUMBER=+15551234567

# Application
LOG_LEVEL=DEBUG
LOG_FORMATTER=text
```

**No prefixes, no duplication** — one variable, one value, works everywhere.

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
# With Docker (no setup needed, reads from .env)
make compose-test

# Or locally (reads from .env automatically via pydantic-settings)
pytest -vv
```

**Test Coverage:**
- ✅ Happy path booking flow
- ✅ Multilingual natural language requests (English, Portuguese, Spanish)
- ✅ Date context injection (AI understands "today", "tomorrow", "this week")
- ✅ Double booking prevention
- ✅ Invalid date/barber handling
- ✅ Conversation history persistence
- ✅ Customer preference recall

## SMS Flow Examples

### English - Natural Language
```
Customer: "Can I get a haircut this week?"
System:   [AI proactively checks next 7 days]
          "Carlos has openings Thursday at 10:00, 10:30, 14:00..."

Customer: "Book me with Carlos at 10am Thursday"
System:   "You're booked with Carlos on Thursday at 10:00 AM!"
          "What type of cut would you like? (fade, buzz cut, classic...)"

Customer: "I usually get a fade"
System:   "Got it! I'll remember you prefer a fade."
```

### Portuguese - Natural Language
```
Customer: "Quero cortar o cabelo hoje"
System:   [AI recognizes "hoje" = today, checks today's availability]
          "Carlos tem horários às 14:00, 15:30, 16:00..."

Customer: "Marcar com Carlos às 14h"
System:   "Agendado com Carlos para hoje às 14:00!"
```

### Returning Customer
```
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
