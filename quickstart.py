import datetime
import os.path
import pytz
from datetime import time
import random


from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from collections import defaultdict


# If modifying these scopes, delete the file token_*.json and re-authenticate
SCOPES = ['https://www.googleapis.com/auth/calendar']

#   Service is a python object that is like "a replication/interface to my real google calendar" that allows me to edit and make change to it.
# And by editting the service object(functions like list(), insert(), delete(), I can read and write my actual google calendar as well.
#   Calendar ID: my email account that's signed in to ggc
#   Time_min: the starting time for looking up events
#   max_result: events quantity that we're fetching


CALENDAR_IDS = [
    "jianj@jnclighting.com",           # me
    "staytest440@gmail.com",           # test account
    "2330212816@qq.com"             # jally
]

def get_events(service, calendar_id, time_min, time_max):
      # Following code fetches and record the upcoming 10 events
      events_result = (
          service.events()
          .list(
              calendarId=calendar_id,
              timeMin=time_min,
              timeMax=time_max,
              singleEvents=True,
              orderBy="startTime",
          )
          .execute()
      )
      return events_result.get("items", [])


# using the event fetched from get_events
# *function doesn't handle all-day events yet
def get_busy_intervals(events):
    busy = []
    tz = pytz.timezone("America/Los_Angeles")
    # looping through all events
    for event in events:
        start = event["start"].get("dateTime")
        end = event["end"].get("dateTime")
        if start and end:
            start_dt = datetime.datetime.fromisoformat(start).astimezone(tz)
            end_dt = datetime.datetime.fromisoformat(end).astimezone(tz)
            busy.append((start_dt, end_dt))
    return busy


def get_free_intervals(busy, day_start, day_end, min_duration_minutes=60):
    """Subtract busy intervals from the daily range, keeping only ≥ 1-hour free blocks"""
    free = []
    cursor = day_start
    min_duration = datetime.timedelta(minutes=min_duration_minutes)

    for start, end in sorted(busy):
        if end <= cursor:
            continue
        if start > cursor:
            gap = start - cursor
            if gap >= min_duration:
                free.append((cursor, start))
        cursor = max(cursor, end)

    if day_end - cursor >= min_duration:
        free.append((cursor, day_end))

    return free


def get_daily_bounds(day, tz):
    """Return datetime objects for that day's 9am–9pm"""
    start = tz.localize(datetime.datetime.combine(day, datetime.time(9, 0)))
    end = tz.localize(datetime.datetime.combine(day, datetime.time(21, 0)))
    return start, end


def find_mutual_free_blocks(free1, free2, block_minutes=60):
    """Return all 1-hour mutual blocks between two sets of free times"""
    mutual = []
    block = datetime.timedelta(minutes=block_minutes)

    # loops through every free block in both calendar and find mutual free time (1hr)
    for s1, e1 in free1:
        for s2, e2 in free2:
            start = max(s1, s2)
            end = min(e1, e2)
            # Only keep blocks that are >= 1 hour
            while (end - start) >= block:
                mutual.append((start, start + block))
                start += block
    return mutual


def main():
    import sys

    user_id = sys.argv[1] if len(sys.argv) > 1 else 'user1'  # default to user1
    token_path = f'token_{user_id}.json'

    creds = None
    if os.path.exists(token_path):
        creds = Credentials.from_authorized_user_file(token_path, SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file("client_secret.json", SCOPES)
            creds = flow.run_local_server(port=5632, access_type='offline', prompt='consent')
        with open(token_path, 'w') as token:
            token.write(creds.to_json())

    try:
        service = build("calendar", "v3", credentials=creds)

        # 📋 Print all calendars User 1 can access
        calendar_list = service.calendarList().list().execute()
        print("\n🔍 Calendars visible to User 1:")
        for calendar in calendar_list['items']:
            print(f"- {calendar['summary']}: {calendar['id']}")

        tz = pytz.timezone("America/Los_Angeles")
        now = datetime.datetime.now(tz).isoformat()
        then = (datetime.datetime.now(tz) + datetime.timedelta(days=7)).isoformat()

        all_events = {
            cal_id: get_events(service, cal_id, now, then)
            for cal_id in CALENDAR_IDS
        }

        for cal_id, events in all_events.items():
            print(f"\n📅 Events from {cal_id}'s calendar:")
            for event in events:
                start = event["start"].get("dateTime", event["start"].get("date"))
                end = event["end"].get("dateTime", event["end"].get("date"))
                start_dt = datetime.datetime.fromisoformat(start).astimezone(pytz.timezone("America/Los_Angeles"))
                end_dt = datetime.datetime.fromisoformat(end).astimezone(pytz.timezone("America/Los_Angeles"))
                print(
                    f"{start_dt.strftime('%Y-%m-%d %I:%M %p')} – {end_dt.strftime('%I:%M %p')}  {event.get('summary', '[No Title]')}")

        # 🔍 Mutual free time
        print("\n🔍 Finding mutual free 1-hour blocks...")
        today = datetime.datetime.now(tz).date()

        for day_offset in range(7):
            day = today + datetime.timedelta(days=day_offset)
            day_start, day_end = get_daily_bounds(day, tz)

            all_free = []
            for cal_id in CALENDAR_IDS:
                busy = [b for b in get_busy_intervals(all_events[cal_id]) if b[1] > day_start and b[0] < day_end]
                free = get_free_intervals(busy, day_start, day_end)
                all_free.append(free)

            if all_free:
                mutual = all_free[0]
                for other_free in all_free[1:]:
                    mutual = find_mutual_free_blocks(mutual, other_free)

                if mutual:
                    print(f"\n🗖 {day.strftime('%A, %B %d')}")
                    for start, end in mutual:
                        print(f"  ✅ {start.strftime('%I:%M %p')} - {end.strftime('%I:%M %p')}")

    except HttpError as error:
        print(f"An error occurred: {error}")

    get_mutual_blocks()

def get_mutual_blocks(token_file="token_user1.json"):
    tz = pytz.timezone("America/Los_Angeles")
    now = datetime.datetime.now(tz)
    then = now + datetime.timedelta(days=30)
    today = now.date()

    # Authenticate once as user1
    creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list['items']:
        print(f"{cal['summary']} ({cal['id']}): access = {cal['accessRole']}")

    # Step 1: Fetch all events
    all_events = {}
    for cal_id in CALENDAR_IDS:
        all_events[cal_id] = get_events(service, cal_id, now.isoformat(), then.isoformat())

    results = []

    import random
    all_candidates = []

    for i in range(30):
        day = today + datetime.timedelta(days=i)
        day_start, day_end = get_daily_bounds(day, tz)

        all_free = []
        for cal_id in CALENDAR_IDS:
            busy = [b for b in get_busy_intervals(all_events[cal_id]) if b[1] > day_start and b[0] < day_end]
            free = get_free_intervals(busy, day_start, day_end)
            all_free.append(free)

        if all_free:
            mutual = all_free[0]
            for other_free in all_free[1:]:
                mutual = find_mutual_free_blocks(mutual, other_free)

            if mutual:
                start_dt, end_dt = random.choice(mutual)
                all_candidates.append((day, start_dt, end_dt))  # Include day for grouping later

    # Group by ISO week number
    weeks = defaultdict(list)
    for day, start_dt, end_dt in all_candidates:
        week = day.isocalendar()[1]
        weeks[week].append((start_dt, end_dt))

    # Pick up to 2 options per week, up to 8 total
    results = []
    for week in sorted(weeks.keys()):
        random.shuffle(weeks[week])
        results.extend(weeks[week][:2])
        if len(results) >= 8:
            break

    return results


if __name__ == "__main__":
  main()


