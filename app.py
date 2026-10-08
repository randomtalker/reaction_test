import time
import os
import re

import bcrypt
import psycopg
from dotenv import load_dotenv
from flask import Flask, redirect, render_template, request, session, url_for

load_dotenv()
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY")

def get_conn():
    return psycopg.connect(
        host=os.getenv("DB_HOST"),
        port=os.getenv("DB_PORT"),
        dbname=os.getenv("DB_NAME"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
    )


@app.route("/")
def index():
    return "ranking_reaction_flaskTEST"


@app.route("/db_check")
def db_check():
    with get_conn() as conn:
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
        with get_conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO account (id, password) VALUES (%s, %s)",
                    (nickname, hashed.decode()),
                )
            except psycopg.errors.UniqueViolation:
                return "Already used nickname"
        return "Enroll COMPLETE"

        
    return render_template("signup.html")


@app.route("/login",methods=["GET","POST"])
def log_in():
    if request.method == "GET":
        return render_template("login.html")

    if request.method == "POST":
        nickname = request.form["nickname"]
        password = request.form["password"]
        with get_conn() as gcon:
            
            hashed_pw = gcon.execute(
                "SELECT password FROM account WHERE id = %s ", (nickname, )
            ).fetchone()
            if not hashed_pw : #없는아이디일 경우
                return "check your nickname and password OR join us first"

            if not bcrypt.checkpw(password.encode(), hashed_pw[0].encode()): #비번 안맞을 경우
                return "check your nickname and password OR join us first"
            
        session["login_id"] = nickname
        return redirect(url_for("game"))
    
@app.route("/me")
def cookie_test():
    login_TF = session.get("login_id")
    if not login_TF:
        return "not logged in"

    return login_TF

@app.route("/logout")
def log_out():
    session.clear()

    return redirect(url_for("log_in"))

@app.route("/game")
def game():
    login_id = session.get("login_id")
    if not login_id :
        return redirect(url_for("log_in"))
    return render_template("game.html")


@app.route("/game/start", methods=["POST"])
def game_start():
    login_id = session.get("login_id")
    if not login_id :
        return {"error": "not logged in"}, 401
    
    session["start_time"] = time.time()

    return {"ok":True}


@app.route("/game/submit", methods=["POST"])
def g_submit():
    login_id = session.get("login_id")
    if not login_id :
            return {"error": "not logged in"}, 401
    start_time = session.pop("start_time",None)
    if not start_time : 
        return {"error": "time_error" }, 400
    
    cur_time = time.time()
    if cur_time < start_time or cur_time-start_time <= 3.3:
        return {"error": "invalid time"}, 400
    

    data = request.get_json()
    records = data.get("records")
    if not isinstance(records,list):
        return {"error": "invalid records" }, 400

    
    if len(records) != 3 or (not all(isinstance(x, int) for x in records)):
        return {"error": "invalid records"}, 400

    if not all( 100 <= y <= 10000 for y in records) :
        return {"error": "invalid records"}, 400

    avg = round(sum(records)/len(records))    
    

    return {"avg":avg}



