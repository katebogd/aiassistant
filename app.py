import os
import datetime
import json

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

from helpers import apology, comp, get_system_prompt

# Configure application
app = Flask(__name__)
con = sqlite3.connect("projects.db")
db = con.cursor()


# Input inbox items
@app.route("/", methods=["GET", "POST"])
def index():
    """Request quiz topic and save to file"""
    if request.method == "POST":
        if not request.form.get("todo"):
            return render_template("index.html")

        todo = request.form.get("todo")
        with open("todo.txt", "w") as file:
            file.write(todo)

        prompt = get_system_prompt()
        response = comp(prompt, MaxToken=3000, outputs=3)
        todo = json.loads(response)["todo"]
        unknown = 0
        for item in todo:
            if item["type"].lower() == "unknown":
                unknown += 1
            db.execute(
                "INSERT INTO items (item, type, project) VALUES (?, ?, ?)",
                [item["item"], item["type"].lower(), item["project"].lower()]
            )
        if unknown > 0:
            return redirect("/sort_inbox")
        return redirect("/projects")

    else:
        return render_template("index.html")


# Sort through leftovers
@app.route("/sort_inbox", methods=["GET", "POST"])
def sort_index():
    if request.method == "POST":
        #TODO
        items = db.execute(
            "SELECT * FROM items WHERE type = project"
        )
        return render_template("projects.html", items=items)
    else:
        items = db.execute(
            "SELECT * FROM items WHERE type = unknown"
        )
        return render_template("sort.html", items=items)


# Display all projects with items
@app.route("/projects", methods=["GET"])
def projects():
    items = db.execute(
        "SELECT * FROM items WHERE type = project"
    )
    return render_template("projects.html", items=items)


# Display all later actions
@app.route("/later", methods=["GET"])
def later():
    items = db.execute(
        "SELECT * FROM items WHERE type = later"
    )
    return render_template("later.html", items=items)


# Display all reference items
@app.route("/reference", methods=["GET"])
def reference():
    items = db.execute(
        "SELECT * FROM items WHERE type = reference"
    )
    return render_template("reference.html", items=items)


@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response
