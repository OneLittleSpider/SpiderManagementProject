from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from datetime import datetime
import os.path

# Define scopepython test_calendar.py
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']

# Run auth flow
flow = InstalledAppFlow.from_client_secrets_file('client_secret.json', SCOPES)
creds = flow.run_local_server(port=0)

# Build the service
service = build('calendar', 'v3', credentials=creds)

# Call the Calendar API
now = datetime.utcnow().isoformat() + 'Z'  # 'Z' indicates UTC time
print('Getting the upcoming 10 events')
events_result = service.events().list(
    calendarId='primary', timeMin=now,
    maxResults=10, singleEvents=True,
    orderBy='startTime').execute()
events = events_result.get('items', [])

# Print events
if not events:
    print('No upcoming events found.')
for event in events:
    start = event['start'].get('dateTime', event['start'].get('date'))
    print(start, event['summary'])
