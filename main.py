from flask import Flask, render_template
import smtplib
from email.mime.text import MIMEText
from quickstart import get_mutual_blocks
import os
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
import pytz
import datetime

app = Flask(__name__)

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/scheduling")
def scheduling():


    token_path = os.path.join(os.path.dirname(__file__), "token_user1.json")
    blocks = get_mutual_blocks(token_file=token_path)

    available = [
        (start.strftime('%A, %b %d'), f"{start.strftime('%I:%M %p')} to {end.strftime('%I:%M %p')}")
        for start, end in blocks
    ]

    return render_template("scheduling.html", available=available)

@app.route("/confirm", methods=["GET", "POST"])
def confirm():
    import os, json
    from flask import request

    token_path = os.path.join(os.path.dirname(__file__), "token_user1.json")
    names = ["LittleSpider", "JoJo", "Jally"]

    if request.method == "POST":
        day = request.form.get("day")
        time = request.form.get("time")
    else:
        day = request.args.get("day")
        time = request.args.get("time")

    # ✅ Simulate email sending on initial GET if flagged
    send_flag = request.args.get("send_emails") == "yes"
    if send_flag:
        print(f"\n📧 Sending confirmation links for {day} {time}:")
        base_url = "/confirm"
        for name in names:
            link = f"{base_url}?day={day}&time={time}&name={name}"
            print(f"  ✉️  To {name}: http://127.0.0.1:5000{link}")

    if not day or not time:
        return "Missing day or time info.", 400

    slot_key = f"{day} | {time}"
    confirm_file = os.path.join("/tmp", "confirmations.json")


    # If submitting the form
    if request.method == "POST":
        name = request.form.get("name")
        if name not in names:
            return "Unknown name.", 400

        # Load or create confirmation data
        if os.path.exists(confirm_file):
            with open(confirm_file, "r") as f:
                data = json.load(f)
        else:
            data = {}

        # Add this name to confirmations
        if slot_key not in data:
            data[slot_key] = []

        if name not in data[slot_key]:
            data[slot_key].append(name)


        # Save updated data
        with open(confirm_file, "w") as f:
            json.dump(data, f)

        # ✅ If everyone confirmed
        if sorted(data[slot_key]) == sorted(names):
            # 🗓️ Schedule the event for real!
            # Parse exact datetime object from slot_key
            tz = pytz.timezone("America/Los_Angeles")
            day_str = slot_key.split(" | ")[0].strip()
            start_time_str = slot_key.split(" | ")[1].split(" to ")[0].strip()

            dt_str = f"{day_str} {start_time_str}"
            current_year = datetime.datetime.now().year
            dt_str = f"{day} {current_year} {start_time_str}"
            start_dt = datetime.datetime.strptime(dt_str, "%A, %b %d %Y %I:%M %p")

            end_dt = start_dt + datetime.timedelta(hours=1)

            # Now pass actual datetime objects
            create_event_for_slot(start_dt, end_dt)

            return f"✅ All users confirmed! Event for {slot_key} has been scheduled!"

        # 🕒 If still waiting
        missing = [n for n in names if n not in data[slot_key]]
        return f"👍 Thanks {name}, waiting on: {', '.join(missing)}"

    # If GET: show the form
    return render_template("confirm.html", day=day, time=time, names=names)


def send_email(recipient, subject, body):
    sender_email = "jianj@jnclighting.com"
    app_password = "Cheetah1224"  # <- From Gmail App Password
    smtp_server = "smtp.gmail.com"
    smtp_port = 587

    msg = MIMEText(body, "html")  # allows clickable links
    msg["Subject"] = subject
    msg["From"] = sender_email
    msg["To"] = recipient

    with smtplib.SMTP(smtp_server, smtp_port) as server:
        server.starttls()
        server.login(sender_email, app_password)
        server.sendmail(sender_email, recipient, msg.as_string())


def create_event_for_slot(start_dt, end_dt):
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    event = {
        'summary': f'Stay Reunion 🎉',
        'start': {'dateTime': start_dt.isoformat(), 'timeZone': 'America/Los_Angeles'},
        'end': {'dateTime': end_dt.isoformat(), 'timeZone': 'America/Los_Angeles'},
    }

    token_path = os.path.join(os.path.dirname(__file__), "token_user1.json")
    creds = Credentials.from_authorized_user_file(token_path, ['https://www.googleapis.com/auth/calendar'])
    service = build("calendar", "v3", credentials=creds)

    calendar_list = service.calendarList().list().execute()
    for cal in calendar_list['items']:
        if cal['accessRole'] in ['writer', 'owner']:
            cal_id = cal['id']
            created_event = service.events().insert(calendarId=cal_id, body=event).execute()
            print(f"📅 Event added to {cal_id} → {created_event.get('htmlLink')}")



if __name__ == "__main__":
    app.run(debug=True)
