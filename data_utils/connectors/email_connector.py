import base64
import logging
import os
import time
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import (
    Attachment,
    Content,
    Email,
    Header,
    Mail,
    Personalization,
)
from typing import List

from data_utils.data_utils.settings import Settings

logger = logging.getLogger(__name__)


class EmailConnector:
    def __init__(self, settings: Settings, sender_name: str = "Python ETL Job") -> None:
        self.settings = settings
        api_key = self.settings.get("sendgrid", "api_key")
        self.sendgrid_client = SendGridAPIClient(apikey=api_key).client
        self.from_email = Email(self.settings.get("sendgrid", "from_email"), sender_name)
        self.to_email = Email(self.settings.get("sendgrid", "to_email"))

    def _prepare_personalization(self, recipients: List[str]) -> Personalization:
        personalization = Personalization()

        if recipients and isinstance(recipients, list):
            for recipient in recipients:
                personalization.add_to(Email(recipient))
        elif self.to_email:
            personalization.add_to(self.to_email)
        else:
            raise ValueError("No recipients have been defined for this email.")

        return personalization

    @staticmethod
    def _add_attachments(email: Mail, attachments: List[str]) -> None:
        if attachments and isinstance(attachments, list):
            for file_path in attachments:
                with open(file_path, "rb") as f:
                    data = f.read()

                encoded = base64.b64encode(data).decode()
                attachment = Attachment()
                attachment.content = encoded
                attachment.filename = os.path.basename(file_path)
                attachment.disposition = "attachment"
                email.add_attachment(attachment)
            else:
                raise ValueError(
                    "Incorrect type for argument attachments. Expecting "
                    "attachments(list[str])."
                )

    @staticmethod
    def _set_importance(mail: Mail, subject: str, importance: str) -> None:
        if not importance and "FAILURE" in subject:
            header = Header("Important", "High")
            mail.add_header(header)
        elif importance:
            header = Header("Important", importance)
            mail.add_header(header)

    def _attempt_to_send_email(self, mail: Mail, max_retry: int):
        retries = 0
        while True:
            response = self.sendgrid_client.mail.send.post(request_body=mail.get())
            if response.status_code == 202:
                break
            else:
                logger.error(
                    f"Received a non-202 response while sending email. Status "
                    f"Code: {response.status_code}. Body: {response.body}"
                )

                if retries < max_retry:
                    logger.info("Sleeping for 10 seconds before retrying...")
                    time.sleep(10)
                    retries += 1
                else:
                    logger.error(
                        f"Unable to send email through SendGrid "
                        f"after {max_retry} retries."
                    )
                    raise Exception(
                        f"Unable to send email. Last response status code: "
                        f"{response.status_code}. Body: {response.body}."
                    )

    def send_email(
        self,
        subject: str,
        body: str,
        recipients: List[str] = None,
        attachments: List[str] = None,
        importance: str = None,
        max_retry: int = 3,
    ) -> None:
        """Modified from integration-utilities library"""

        logger.debug("Configuring email message to send.")

        if self.settings.get("DEFAULT", "environment").upper() != "PROD":
            subject = self.settings.get("DEFAULT", "environment").upper() + " - " + subject

        content = Content("text/html", body)
        mail = Mail(from_email=self.from_email, subject=subject, content=content)
        mail.reply_to = self.from_email

        personalization = self._prepare_personalization(recipients)
        mail.add_personalization(personalization)

        self._add_attachments(mail, attachments)
        self._set_importance(mail, subject, importance)

        self._attempt_to_send_email(mail, max_retry)

        logger.debug(f"Email successfully sent to {recipients or self.to_email}.")
