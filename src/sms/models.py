import logging
from typing import Optional

import pydantic
from fastapi import Form
from pydantic import BaseModel, Field
from twilio.twiml.messaging_response import MessagingResponse  # type: ignore

# Instantiate logger
logger = logging.getLogger("app")


class SMSRequest(BaseModel):
    """
    Represents an incoming SMS message.

    Attributes:
        from_number (str): The phone number that sent the SMS.
        body (str): The content of the SMS message.
    """

    from_number: str
    body: str = Field(min_length=1)

    @classmethod
    def from_form(cls, from_number: str = Form(alias="From"), body: str = Form(alias="Body")) -> Optional["SMSRequest"]:
        """
        Create an instance of `SMSRequest` from incoming form data.

        Args:
            from_number (str): The phone number that sent the SMS.
            body (str): The content of the SMS message.

        Returns:
            SMSRequest: An instance of `SMSRequest` initialized with the provided data.
            None: When a validation error happens.
        """

        try:
            return cls(from_number=from_number, body=body)
        except pydantic.ValidationError:
            logger.info("Received an invalid SMS message", exc_info=True)
            return None


class SMSResponse(BaseModel):
    """
    Represents an SMS response to be sent.

    Attributes:
        message (str): The content of the SMS message to be sent in the reply.
    """

    message: str

    def to_twiml(self) -> str:
        """
        Generate TwiML response for the SMS.

        TwiML (Twilio Markup Language) is used by Twilio to determine the response to
        incoming SMS messages. This method generates a valid TwiML response with a
        message that will be sent back to the user.

        Returns:
            str: A string representing the generated TwiML response containing the message.

        Ref: https://www.twilio.com/docs/messaging/tutorials/how-to-receive-and-reply/python#what-is-twiml
        """

        response = MessagingResponse()
        response.message(self.message)  # Append the <Message> to the <Response>
        return str(response)  # Convert the complete <Response> to a string
