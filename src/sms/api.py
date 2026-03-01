import logging
from http import HTTPStatus
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from pydantic_ai import Agent, exceptions
from twilio.request_validator import RequestValidator  # type: ignore

from src.core.config import settings
from src.sms.models import SMSRequest, SMSResponse

# Instantiate logger
logger = logging.getLogger("app")

# Create an instance of APIRouter with a prefix for the /sms endpoint and a tag for documentation purposes
router = APIRouter(prefix="/sms", tags=["sms"])


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
        logger.debug(
            f"Received SMS from {sms_request.from_number}: {sms_request.body}",
            extra={"from": sms_request.from_number, "body": sms_request.body},
        )

        # Generate response through an AI model
        try:
            # TODO: this is not ensuring "chat history".
            #       for that we will need to have a stateful model on our side to ensure the following:
            #       User SMS: How is the weather in Portugal today?
            #       AI: I need to know a specific area of Portugal.
            #       User SMS: Porto
            #       AI: It’s a sunny day in Porto.
            #       Otherwise, we are not replicating a real conversation.
            #       For such implementation we will need to deploy a storage solution (e.g. Postgres, Redis)
            #       to store the history of SMSs for each number and pass it to the model.
            agent = Agent(
                model=settings.AI_MODEL,
                system_prompt="You are receiving this request from an API service where the main scope is to "
                "response to customers incoming text messages (SMS) automatically "
                "(like customer support). Be concise, reply with one simple and direct sentence.",
                deps_type=SMSRequest,
            )
            result = await agent.run(user_prompt=sms_request.body, deps=sms_request)
            response_message = result.data
        except (httpx.ConnectTimeout, exceptions.UnexpectedModelBehavior):
            logger.error("Connection error with Gemini", exc_info=True)
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
