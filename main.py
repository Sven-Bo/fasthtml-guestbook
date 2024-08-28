import json
import os
from datetime import datetime

import gspread
import pandas as pd
import pytz
from fasthtml.common import *

# Constants for input character limits and timestamp format
MAX_NAME_CHAR = 15
MAX_MESSAGE_CHAR = 50
TIMESTAMP_FMT = "%Y-%m-%d %I:%M:%S %p CET"


# Load credentials (local or from environment)
def load_credentials():
    google_credentials = os.getenv("GOOGLE_CREDENTIALS")
    if google_credentials:
        credentials = json.loads(google_credentials)
    else:
        credentials = json.load(open("credentials.json"))
    return gspread.service_account_from_dict(credentials)


# Authenticate and connect to Google Sheets
gc = load_credentials()
sheet = gc.open("Guestbook").sheet1  # Open the sheet by name


def get_cet_time():
    cet_tz = pytz.timezone("CET")
    return datetime.now(cet_tz)


def add_message(name, message):
    timestamp = get_cet_time().strftime(TIMESTAMP_FMT)
    sheet.append_row([name, message, timestamp])


def get_messages():
    records = sheet.get_all_records()
    df = pd.DataFrame.from_records(records)
    df["Timestamp"] = pd.to_datetime(df["Timestamp"], format=TIMESTAMP_FMT)
    return df


def render_message(entry):
    return Article(
        Header(f"Name: {entry['Name']}"),
        P(entry["Message"]),
        Footer(f"Posted at {entry['Timestamp']}"),
    )


app, rt = fast_app(
    hdrs=(Link(rel="icon", type="assets/x-icon", href="/assets/favicon.png"),),
)


def render_message_list():
    messages_df = get_messages()
    messages_df = messages_df.sort_values(by="Timestamp", ascending=False)

    return Div(
        *[render_message(entry) for _, entry in messages_df.iterrows()],
        id="message-list",  # ID for the message list
    )


def render_content():
    form = Form(
        Fieldset(
            Input(
                type="text",
                name="name",
                placeholder="Name",
                required=True,
                maxlength=MAX_NAME_CHAR,
            ),
            Input(
                type="text",
                name="message",
                placeholder="Message",
                required=True,
                maxlength=MAX_MESSAGE_CHAR,
            ),
            Button("Submit", type="submit"),
            role="group",
        ),
        method="post",
        hx_post="/submit-message",  # Send a POST request to the /submit-message endpoint
        hx_target="#message-list",  # Only swap the message list
        hx_swap="outerHTML",  # Replace the entire content of the target element with the response
        hx_on__after_request="this.reset()",  # Reset the form after submission
    )

    return Div(
        P(Em("Write something nice!")),
        form,
        Div(
            "Made with ❤️ by ",
            A("Sven", href="https://youtube.com/@codingisfun", target="_blank"),
        ),
        Hr(),
        render_message_list(),
    )


@rt("/", methods=["GET"])
def get():
    return Titled("Sven's Guestbook 📖", render_content())


@rt("/submit-message", methods=["POST"])
def post(name: str, message: str):
    add_message(name, message)
    return render_message_list()


serve()
