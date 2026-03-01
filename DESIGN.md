# Design Notes

1. **pydantic-ai for agent orchestration** — Provides type-safe tool calling and structured model interactions. Tools are plain Python functions registered with the agent, keeping AI logic separate from business logic.

2. **SQLite for persistence** — Zero-dependency, file-based storage ideal for a demo. SQLAlchemy ORM provides a clean abstraction layer, making it straightforward to swap to PostgreSQL for production.

3. **Tool-based architecture** — Availability checking, booking, and preference management are implemented as discrete agent tools rather than prompt-engineered behaviors. This makes actions deterministic and testable.

4. **Phone number as customer identity** — Twilio provides the sender's phone in E.164 format. No authentication needed — the phone number serves as a natural, stable identifier for preferences and history.

5. **Conversation history per phone number** — Last 10 messages stored and replayed to the agent on each turn, enabling multi-step scheduling flows ("Can I get a haircut?" → "When?" → "Thursday 2pm" → booked).

6. **Slot-based availability** — 30-minute slots within configurable working hours per barber. Availability is computed dynamically: all possible slots minus existing bookings, checked at the database level.

7. **Conflict prevention at DB level** — Unique constraint on (barber_id, start_time) prevents double bookings even under concurrent requests. Application-level validation provides user-friendly error messages.

8. **Graceful degradation** — If the AI model is unreachable, the system returns a friendly error message rather than crashing. All webhook responses are valid TwiML so Twilio never receives an error.

9. **90-day reminder system** — Lightweight asyncio background task checks hourly for appointments due for a follow-up. No external job queue needed for the demo; production would use Celery or similar.

10. **Production readiness path** — Key changes for production: PostgreSQL for concurrent access, Redis/Celery for reliable reminders, rate limiting on the webhook endpoint, proper secret management (Vault/KMS), and horizontal scaling behind a load balancer.
