import logging
from datetime import datetime
from http import HTTPStatus
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic_ai import Agent, RunContext, exceptions
from twilio.request_validator import RequestValidator  # type: ignore

from src.core.config import settings
from src.scheduling.tools import (
    book_appointment,
    check_availability,
    get_barbers,
    get_conversation_history,
    get_customer_preference,
    save_customer_preference,
    save_message,
)
from src.sms.models import SMSRequest, SMSResponse

# Instantiate logger
logger = logging.getLogger("app")

# Create an instance of APIRouter with a prefix for the /sms endpoint and a tag for documentation purposes
router = APIRouter(prefix="/sms", tags=["sms"])

BARBERSHOP_SYSTEM_PROMPT = """You are the SMS assistant for Fresh Cuts Barbershop.

You help customers check barber availability, book appointments, and manage their preferences.

CRITICAL: You MUST be proactive and conversational. Do NOT ask customers for exact dates/times unless absolutely necessary.

Available tools:
- check_availability: Check which barbers have open slots on a given date (format: YYYY-MM-DD)
- get_barbers: List all barbers and their specialties
- book_appointment: Book an appointment with a specific barber
- save_customer_preference: Save a customer's preferred haircut style
- get_customer_preference: Look up a customer's preferred haircut style

Date handling (CRITICAL):
- Today's date is always available in your context
- When customer says "today", "hoje", "hoy" → use TODAY's date
- When customer says "tomorrow", "amanhã", "mañana" → use TOMORROW's date
- When customer says "this week", "esta semana", "cette semaine" → check next 7 days starting from today
- When customer says "next week", "próxima semana", "la semana que viene" → check dates 7-14 days from today
- ALWAYS calculate the actual date and call check_availability with YYYY-MM-DD format
- Support multilingual requests (English, Portuguese, Spanish, French, etc.)

Proactive behavior:
- When customer asks about availability for "this week", AUTOMATICALLY check today + next 6 days and show available slots
- When customer asks for "today", IMMEDIATELY check today's availability without asking for confirmation
- DO NOT ask "what date would you like?" - figure it out from context and check availability immediately
- Be conversational: "Let me check what's available this week..." then call the tool

Guidelines:
- Be friendly, conversational, and concise (SMS messages should be short)
- PROACTIVELY use tools to help the customer - don't make them specify exact dates
- When booking, confirm the barber, date, time, and cut type before finalizing
- After a successful booking, ask about their preferred cut if we don't have one on file
- If a returning customer has a preference on file, mention it proactively
- Working hours are generally 9 AM to 6 PM, slots are 30 minutes
- If something goes wrong, apologize and suggest they try again
- Support customers in any language they speak to you
"""

# AI Agent
agent = Agent(
    model=settings.AI_MODEL,
    system_prompt=BARBERSHOP_SYSTEM_PROMPT,
    deps_type=SMSRequest,
)


@agent.tool
async def tool_check_availability(ctx: RunContext[SMSRequest], date: str) -> str:
    return await check_availability(date)


@agent.tool
async def tool_get_barbers(ctx: RunContext[SMSRequest]) -> str:
    return await get_barbers()


@agent.tool
async def tool_book_appointment(
    ctx: RunContext[SMSRequest], barber_name: str, date: str, time: str, cut_type: str = None
) -> str:
    customer_phone = ctx.deps.from_number
    return await book_appointment(barber_name, date, time, customer_phone, cut_type)


@agent.tool
async def tool_save_preference(ctx: RunContext[SMSRequest], preferred_cut: str) -> str:
    customer_phone = ctx.deps.from_number
    return await save_customer_preference(customer_phone, preferred_cut)


@router.post(
    "/reply",
    response_class=Response,
    responses={200: {"content": {"text/xml": {}}}},
)
async def reply(request: Request, sms_request: SMSRequest = Depends(SMSRequest.from_form)) -> Any:
    """
    Endpoint to receive an incoming SMS and reply with a message.

    This endpoint processes incoming SMS requests, extracts the necessary data,
    logs the information for debugging purposes, creates a response message,
    and returns a valid TwiML (Twilio Markup Language) response.
    """

    #
    # Webhook validation
    #
    if settings.TWILIO_WEBHOOKS_VALIDATION_ENABLED:
        # Validate webhook using Twilio signature.
        try:
            validator = RequestValidator(token=settings.TWILIO_AUTH_TOKEN)
            raw_url = str(request.url)
            form_data = await request.form()
            signature = request.headers.get("X-Twilio-Signature", "")
            if not validator.validate(uri=raw_url, params=dict(form_data), signature=signature):
                logger.warning("The webhook received did not belong to Twilio")
                raise HTTPException(status_code=HTTPStatus.FORBIDDEN)
        except AttributeError:
            logger.error("Twilio token not defined, can't validate webhook")
            raise HTTPException(status_code=HTTPStatus.FORBIDDEN)

    #
    # Generate a reply message based on the received content
    #
    if not sms_request:
        # We received an invalid SMS (e.g. wrong body)
        response_message = "Ups! I'm sorry, I can't process your request because your message looks bad! :("
    else:
        # Valid SMS request, build response
        logger.info(
            f"📱 INCOMING SMS | From: {sms_request.from_number} | Message: '{sms_request.body}'",
            extra={"event": "sms_received", "from": sms_request.from_number, "body": sms_request.body},
        )

        # Generate response through an AI model
        try:
            logger.info(f"🔍 Loading conversation history for {sms_request.from_number}")
            history = await get_conversation_history(sms_request.from_number)
            logger.info(f"📝 Found {len(history)} previous messages in history")

            preference_result = await get_customer_preference(sms_request.from_number)
            logger.info(f"💇 Customer preference: {preference_result}")

            # Add current date context for the AI to understand "today", "tomorrow", etc.
            today = datetime.now()
            date_context = f"\n\nCURRENT DATE/TIME CONTEXT (use this to calculate dates):\n- Today is: {today.strftime('%Y-%m-%d')} ({today.strftime('%A, %B %d, %Y')})\n- Current time: {today.strftime('%H:%M')}"

            system_context = BARBERSHOP_SYSTEM_PROMPT + date_context
            if "No preference" not in preference_result:
                system_context += f"\n\nCustomer info: {preference_result}"

            logger.info(f"🤖 Calling AI agent with model: {settings.AI_MODEL}")
            result = await agent.run(
                user_prompt=sms_request.body, deps=sms_request, message_history=history, system_prompt=system_context
            )
            response_message = result.output
            logger.info(f"✅ AI Response: '{response_message}'")

            logger.info("💾 Saving conversation to database")
            await save_message(sms_request.from_number, "user", sms_request.body)
            await save_message(sms_request.from_number, "assistant", response_message)
            logger.info("✅ Conversation saved successfully")
        except (httpx.ConnectTimeout, exceptions.UnexpectedModelBehavior) as e:
            logger.error(f"❌ AI MODEL ERROR: {type(e).__name__} - {str(e)}", exc_info=True)
            response_message = "Ups! We were unable to respond to your request, please try again later :("

    #
    # Build response
    #
    # TODO: improve exception handling
    sms_response = SMSResponse(message=response_message)

    #
    # Return a TwiML response (XML) to be sent by Twilio
    #
    return Response(content=sms_response.to_twiml(), media_type="text/xml")
