import csv
import datetime
import pytz
import requests
import subprocess
import urllib
import uuid
import random
import json
import sqlite3


from flask import redirect, render_template, session
from functools import wraps

import openai

with open("key.txt", "r") as file:
    openai.api_key = file.readline()

con = sqlite3.connect("projects.db")
db = con.cursor()


def get_system_prompt() -> str:
    with open("topic.txt", "r") as f:
        todo = f.readline()

    with open('todo.json') as f:
        json_schema = json.loads(f.read())
    json_schema_str = ', '.join([f"'{key}': {value}" for key, value in json_schema.items()])

    prompt = "Create a quiz with 10 questions and 4 possible answers for each question. Separately remember the correct answer for each question. Use the following topic for the quiz: {todo}.Please respond with your analysis directly in JSON format (without using Markdown code blocks or any other formatting). The JSON schema should include: {json_schema}.".format(
        todo=todo, json_schema=json_schema_str)

    return prompt


# function that takes in string argument as parameter
def comp(prompt, MaxToken=50, outputs=3):
    with open('todo.json') as f:
        json_schema = json.loads(f.read())
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[
            {
                "role": "user",
                "content": prompt,
            }
        ],
        response_format={"type": "json_object"}
    )
    output = response["choices"][0]["message"]["content"]
    return output


def apology(message, code=400):
    """Render message as an apology to user."""

    def escape(s):
        """
        Escape special characters.

        https://github.com/jacebrowning/memegen#special-characters
        """
        for old, new in [("-", "--"), (" ", "-"), ("_", "__"), ("?", "~q"),
                         ("%", "~p"), ("#", "~h"), ("/", "~s"), ("\"", "''")]:
            s = s.replace(old, new)
        return s

    return render_template("apology.html", top=code, bottom=escape(message)), code


def lookup(symbol):
    """Look up quote for symbol."""

    # Prepare API request
    symbol = symbol.upper()
    end = datetime.datetime.now(pytz.timezone("US/Eastern"))
    start = end - datetime.timedelta(days=7)

    # Yahoo Finance API
    url = (
        f"https://query1.finance.yahoo.com/v7/finance/download/{urllib.parse.quote_plus(symbol)}"
        f"?period1={int(start.timestamp())}"
        f"&period2={int(end.timestamp())}"
        f"&interval=1d&events=history&includeAdjustedClose=true"
    )

    # Query API
    try:
        response = requests.get(url, cookies={"session": str(uuid.uuid4())},
                                headers={"User-Agent": "python-requests", "Accept": "*/*"})
        response.raise_for_status()

        # CSV header: Date,Open,High,Low,Close,Adj Close,Volume
        quotes = list(csv.DictReader(response.content.decode("utf-8").splitlines()))
        quotes.reverse()
        price = round(float(quotes[0]["Adj Close"]), 2)
        return {
            "name": symbol,
            "price": price,
            "symbol": symbol
        }
    except (requests.RequestException, ValueError, KeyError, IndexError):
        return None
