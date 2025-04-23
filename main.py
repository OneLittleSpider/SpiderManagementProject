#Below are all the imports for this project
from flask import Flask, redirect, url_for, session, request
from flask import render_template_string
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build
import os
import pathlib


#Create Flask application instance,sets up the whole framework so we can define routes and serve pages
app = Flask(__name__)

# ！！might need to change: use a strong random key in real projects
app.secret_key = "your_secret_key"

# This is the path to my client_secret.json that has password/access to my google data
CLIENT_SECRETS_FILE = "client_secret.json"

#scope that request "read only" access from google calendar
SCOPES = ["https://www.googleapis.com/auth/calendar.readonly"]
REDIRECT_URI = "http://localhost:4999/oauth2callback"


@app.route("/")
def index():
    # 1️⃣ Check if we have OAuth credentials in the session, if not, direct to asking for access
    if "credentials" not in session:
        return '<a href="/authorize">Connect to Google Calendar</a>'

    # 2️⃣ Rebuild a Credentials object from what we stored in session
    creds = Credentials.from_authorized_user_info(session["credentials"])

    # 3️⃣ Create a Google Calendar API client
    service = build("calendar", "v3", credentials=creds)

    # 4️⃣ Fetch the next 10 events from the user's primary calendar
    events_result = service.events().list(calendarId='primary', maxResults=10).execute()
    events = events_result.get("items", [])

    # 5️⃣ Build a tiny HTML page listing those events
    html = "<h1>Your Upcoming Events</h1><ul>"
    for event in events:
        html += f"<li>{event.get('summary')} - {event.get('start', {}).get('dateTime')}</li>"
    html += "</ul><a href='/logout'>Logout</a>"

    # 6️⃣ Return that HTML (Flask will send it to the browser)
    return render_template_string(html)


#this route: set OAuth up for getting permission and send permission request
@app.route("/authorize")
def authorize():
    #flow is a part of the OAuth library that helps me manage OAuth
    flow = Flow.from_client_secrets_file(
        #The following 3 lines gives it my credentials, the scope details, and where to redirect user after getting the permission.
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        redirect_uri=REDIRECT_URI
    )
    auth_url, state = flow.authorization_url(prompt="consent")
    session["state"] = state
    return redirect(auth_url)

#this route: after oauth get permission,
@app.route("/oauth2callback")
def oauth2callback():
    state = session["state"]
    flow = Flow.from_client_secrets_file(
        CLIENT_SECRETS_FILE,
        scopes=SCOPES,
        state=state,
        redirect_uri=REDIRECT_URI
    )

    #send permission proof to google, get new token, and saved the new token
    flow.fetch_token(authorization_response=request.url)

    creds = flow.credentials

    #session is a flask object that acts like a storage space. we store the following info there.
    session["credentials"] = {
        "token": creds.token,
        "refresh_token": creds.refresh_token,
        "token_uri": creds.token_uri,
        "client_id": creds.client_id,
        "client_secret": creds.client_secret,
        "scopes": creds.scopes
    }

    return redirect(url_for("index"))

#remove credential access when user logs out
@app.route("/logout")
def logout():
    #remove line
    session.pop("credentials", None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True, port=4999)

