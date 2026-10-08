import os
import re

import bcrypt
import psycopg
from dotenv import load_dotenv
from flask import Flask, render_template, request

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

@app.route("/signup",methods=["GET","POST"])
def sign_up():
    if request.method == "POST":
        nickname = request.form["nickname"]
        password = request.form["password"]
        
        if not re.fullmatch(r"[a-z][a-z0-9]{3,15}" , nickname):
            return "id doesnt follow the rule"
        if not re.fullmatch(r"[!-~]{8,64}", password):
            return "pw doesnt follow the rule"
        if not re.search(r"[a-z]",password):
            return "pw doesnt follow the rule(lowercase)"
        if not re.search(r"[A-Z]",password):            
            return "pw doesnt follow the rule(uppercase)"
        if not re.search(r"[0-9]",password):
            return "pw doesnt follow the rule(numcase)"
        if not re.search(r"[^A-Za-z0-9]",password):
            return "pw doesnt follow the rule(symbolcase)"

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        return hashed.decode()

        
    return render_template("signup.html")