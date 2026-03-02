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

## Twilio Webhook Configuration

After starting the containers, you need to configure Twilio to send incoming SMS messages to your ngrok URL.

### 1. Get your ngrok URL

Visit the ngrok dashboard at `http://localhost:4040` or check the container logs:

```bash
docker logs messaging-api-ngrok
```

Look for the forwarding URL (e.g., `https://your-domain.ngrok-free.app` or `https://abc123.ngrok-free.app`).

### 2. Configure Twilio Phone Number

1. Go to [Twilio Console > Phone Numbers](https://console.twilio.com/us1/develop/phone-numbers/manage/incoming/)
2. Click on your phone number
3. Scroll down to **Messaging Configuration**
4. Under **"A MESSAGE COMES IN"**:
   - Select: `Webhook`
   - URL: `https://your-ngrok-url.ngrok-free.app/sms/reply`
   - Method: `HTTP POST`
5. Click **Save**

**Example webhook URL:**
```
https://abc123.ngrok-free.app/sms/reply
```

### 3. Test the Integration

Send an SMS to your Twilio phone number:

```
"Can I get a haircut this week?"
```

You should receive an AI-powered response with available slots!

**Troubleshooting:**
- Check logs: `docker logs messaging-api` for FastAPI logs
- Check ngrok dashboard: `http://localhost:4040` to see incoming requests
- Verify webhook validation is disabled for testing: `TWILIO_WEBHOOKS_VALIDATION_ENABLED=False` in docker-compose

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
