import os
import urllib

from google.appengine.ext import ndb
from webapp2_extras import json
from google.appengine.api import mail
from message_generator import randMessage
from sendgrid import SendGridClient
from sendgrid import Mail
from secrets import username, password

import jinja2
import webapp2
import logging

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

class EmailNotification(ndb.Model):
    """A model representing a single email notification."""
    created = ndb.DateTimeProperty(auto_now_add=True)
    recipient_email = ndb.StringProperty(indexed=True)
    sender_name = ndb.StringProperty(indexed=True)

class EmailNotificationHandler(webapp2.RequestHandler):

    def post(self):
        email_notification = EmailNotification()
        logging.debug(self.request.body)
        body = json.decode(self.request.body)
        email_notification.recipient_email = body["recipient_email"]
        logging.debug("recipient_email: %s", email_notification.recipient_email)
        email_notification.sender_name = body["sender_name"]
        logging.debug("sender_name: %s", email_notification.sender_name)
        email_notification.put()
        resp = {
            "recipient_email": email_notification.recipient_email,
            "sender_name": email_notification.sender_name
        }
        if not mail.is_email_valid(email_notification.recipient_email):
            self.response.write('Bad Email')
        else:


            sender = "%s <dontmakemehangrynoreply@gmail.com>" % email_notification.sender_name
            subject, body, html = randMessage(email_notification.sender_name)
            logging.debug('Sending Email')
            sendEmailWithSendGrid(sender, email_notification.recipient_email, subject, body, html)
            # sendEmailWithGAEMailAPI(sender, email_notification.recipient_email, subject, body, html)
            logging.debug('Sending Response')
            self.response.write(json.encode(resp))

def sendEmailWithSendGrid(sender, to, subject, body, html):

    # make a secure connection to SendGrid
    sg = SendGridClient(username, password, secure=True)

    # make a message object
    message = Mail()
    message.set_subject(subject)
    message.set_html(html)
    message.set_text(body)
    message.set_from(sender)

    # add a recipient
    message.add_to(to)

    logging.debug("message %s" % message)

    # use the Web API to send your message
    sg.send(message)

def sendEmailWithGAEMailAPI(sender, to, subject, body, html):
    message = mail.EmailMessage(sender=sender, subject=subject)
    message.to = to
    message.body = body
    message.html = html
    message.send()


application = webapp2.WSGIApplication([
    ('/notifications', EmailNotificationHandler)
], debug=True)
