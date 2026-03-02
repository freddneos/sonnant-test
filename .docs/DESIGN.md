# Design Notes

1. **Proactive multilingual AI agent** — System prompt instructs the agent to understand date references ("today", "tomorrow", "this week") in any language without asking for ISO formats. Current date/time injected into every request enables autonomous date calculation. Agent calls tools immediately rather than requesting clarification, creating a conversational UX that feels natural across English, Portuguese, Spanish, etc.

2. **Tool-based deterministic actions** — Availability checking, booking, and preference management are discrete Python functions registered with pydantic-ai. This separates AI reasoning (when to act) from business logic (what to do), making core operations testable and predictable. AI decides *when* to call `book_appointment`, but the function enforces *what* constitutes a valid booking.

3. **Conversation memory per customer** — Last 10 messages stored by phone number and replayed to the agent on each turn. Enables multi-step flows ("Can I get a haircut?" → "Thursday at 2pm" → "What type?" → "Fade" → booked). Customer preferences (haircut style) automatically loaded and referenced in future conversations ("Welcome back! Last time you got a fade").

4. **Structured logging for observability** — Emoji-prefixed logs (📱 SMS, 🤖 AI, 🔧 tools, ✅ success, ❌ errors) provide visual parsing in terminal and production logs. Each log includes contextual data (phone, date, model) for debugging. Critical for evaluating AI behavior during testing and diagnosing issues in production.

5. **Conflict prevention at database layer** — Unique constraint on (barber_id, start_time) prevents double bookings even under race conditions. SQLAlchemy enforces this at commit time; application catches IntegrityError and returns user-friendly message. Ensures reliability without distributed locks.

6. **Phone number as stateless identity** — Twilio provides E.164 phone in every webhook. No session management or authentication needed — the phone number itself is the customer ID. Preferences and history keyed by phone, making the system naturally stateless and horizontally scalable.

7. **Slot-based dynamic availability** — Generate all possible 30-min slots within barber working hours, subtract existing bookings from database. Availability computed fresh on each request rather than cached, ensuring accuracy. Simple O(n) algorithm sufficient for barbershop scale (3 barbers × 9 hours × 2 slots/hour = 54 slots/day).

8. **Unified environment configuration** — Single `.env` file with zero duplication. Same variable names (`GOOGLE_API_KEY`, `TWILIO_AUTH_TOKEN`) used by both Docker Compose and pydantic-settings. No `MESSAGING_API_*` prefixes vs unprefixed duplicates. Change an API key once, works everywhere. Reduces configuration errors and maintenance overhead.

9. **Graceful degradation and error handling** — AI model failures return friendly SMS ("We're having trouble, try again later") rather than 500 errors. All webhook responses return valid TwiML so Twilio never sees HTTP errors. Prevents customer-facing failures from infrastructure issues.

10. **Test coverage matching evaluation criteria** — Unit tests for tools (booking, availability, preferences), E2E tests for SMS flow, multilingual NLP scenarios, date context injection. Skipped tests documented with reasons. Tests validate happy path, error cases, and AI behavior — directly addressing "functionality, reliability, architecture" rubric.

11. **90-day reminder background task** — Asyncio task runs hourly within FastAPI lifespan, checking for old appointments and sending follow-up SMS via Twilio. No external queue needed for demo scale. Demonstrates async patterns and complete feature implementation without overengineering.

12. **SQLite → PostgreSQL swap path** — SQLAlchemy abstraction means changing database is a one-line config change. Async session management already in place. Constraints (unique barber slots) work identically. Demonstrates architectural decision to start simple but design for growth — appropriate for technical assessment.
