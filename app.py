signup_log = {}

import os
import re
import time

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
            return render_template("signup.html", error="닉네임 규칙을 확인해주세요", nickname=nickname), 400
        if not re.fullmatch(r"[!-~]{8,64}", password):
            return render_template("signup.html", error="패스워드 길이는 최소 8자 이상입니다", nickname=nickname), 400
        if not re.search(r"[a-z]",password):
            return render_template("signup.html", error="패스워드에는 최소 1개의 소문자가 필요합니다", nickname=nickname), 400
        if not re.search(r"[A-Z]",password):            
            return render_template("signup.html", error="패스워드에는 최소 1개의 대문자가 필요합니다", nickname=nickname), 400
        if not re.search(r"[0-9]",password):
            return render_template("signup.html", error="패스워드에는 최소 1개의 숫자가 필요합니다", nickname=nickname), 400
        if not re.search(r"[^A-Za-z0-9]",password):
            return render_template("signup.html", error="패스워드에는 최소 1개의 특수문자가 필요합니다", nickname=nickname), 400

        # 다중 가입차단
        ip = request.remote_addr
        cur_time = time.time()
        if not signup_log.get(ip): signup_log[ip] = [cur_time]
        else : signup_log[ip].append(cur_time)
        signup_log[ip] = [t for t in signup_log[ip] if cur_time - t < 60]
        if len(signup_log[ip]) >= 10 :
            return render_template("signup.html",error="지나치게 많은 시도" , nickname=nickname) , 429



        

        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
        with get_conn() as conn:
            try:
                conn.execute(
                    "INSERT INTO account (id, password) VALUES (%s, %s)",
                    (nickname, hashed.decode()),
                )
            except psycopg.errors.UniqueViolation:
                return render_template("signup.html",error="이미 사용중인 아이디입니다." , nickname=nickname) , 409

        session["login_id"] = nickname
        return redirect(url_for("game"))

        
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

            if not hashed_pw or not bcrypt.checkpw(password.encode(), hashed_pw[0].encode()): #없는아이디일 경우
                return render_template("login.html",error="아이디와 비밀번호를 확인해주세요" , nickname=nickname) , 401
            
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
            app.logger.warning("submit rejected: reason=%s user=%s ip=%s",
                                "not_logged_in", session.get("login_id"), request.remote_addr)
            return {"error": "not logged in"}, 401
    start_time = session.pop("start_time",None)
    if not start_time : 
        app.logger.warning("submit rejected: reason=%s user=%s ip=%s",
                            "no_time", session.get("login_id"), request.remote_addr)
        return {"error": "time_error" }, 400
    
    cur_time = time.time()
    elapsed = cur_time - start_time

    if cur_time < start_time or elapsed <= 3.3 or elapsed >= 300 :
        app.logger.warning("submit rejected: reason=%s user=%s ip=%s start_time=%r submit_time=%r",
                            "bad_elapsed", session.get("login_id"), request.remote_addr, start_time,cur_time)
        return {"error": "invalid time"}, 400
    

    data = request.get_json()
    records = data.get("records")
    if not isinstance(records,list):
        return {"error": "invalid records" }, 400

    
    if len(records) != 3 or (not all(isinstance(x, int) for x in records)):
        app.logger.warning("submit rejected: reason=%s user=%s ip=%s records=%r",
                            "lack_count", session.get("login_id"), request.remote_addr, records)
        return {"error": "invalid records"}, 400

    if not all( 100 <= y < 10000 for y in records) :
        app.logger.warning("submit rejected: reason=%s user=%s ip=%s records=%r",
                            "range", session.get("login_id"), request.remote_addr, records)
        return {"error": "invalid records"}, 400

    avg = round(sum(records)/len(records))    

    with get_conn() as conn:
        conn.execute( #record_his에 입력
            """
            INSERT INTO record_his (account_id, r1,r2,r3,elapsed,ip)
            VALUES (%s, %s,%s,%s, %s, %s)
            """,
            (login_id, *records, elapsed, request.remote_addr ),
        )


        row = conn.execute( #record에 입력
            """
            INSERT INTO record (account_id, best_record)
            VALUES (%s, %s)
            ON CONFLICT (account_id) DO UPDATE
            SET best_record = EXCLUDED.best_record,
                best_at = now()
            WHERE EXCLUDED.best_record <= record.best_record
            RETURNING old.best_record

            """,
            (login_id, avg),
        ).fetchone()

        best = conn.execute(            
            "SELECT best_record FROM record WHERE account_id = %s",
            (login_id,),            
        ).fetchone()[0]
        updated = True

        if not row: # 느려
            updated = False

        elif not row[0]: # 신규기록
            best = avg
            
        elif avg < row[0] : # 기록갱신
            pass

        else: # 동점

            updated = False

    return {"avg":avg, "best" : best, "updated": updated }

@app.route("/ranking")
def ranking():
    with get_conn() as conn:
        rows = conn.execute(
            """
            SELECT account_id, best_record
            FROM record
            ORDER BY best_record ASC, best_at DESC, record_id DESC
            LIMIT 10

            """
        ).fetchall()
    
    return render_template("ranking.html", rows=rows)