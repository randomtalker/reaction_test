import os

import psycopg
from dotenv import load_dotenv
from flask import Flask, render_template

load_dotenv()
app = Flask(__name__)


@app.route("/")
def index():
    return "ranking_reaction_flaskTEST"


@app.route("/db_check")
def db_check():
    with psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    ) as conn:
        return conn.execute("SELECT version()").fetchone()[0]

@app.route("/signup")
def sign_up():
    return render_template("signup.html")