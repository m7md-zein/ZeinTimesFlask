from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from dotenv import load_dotenv
from database import get_connection
import os
from datetime import date

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeintimes_secret")

def get_daily_quote():
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM quotes")
    quotes = cursor.fetchall()
    cursor.close()
    conn.close()
    if not quotes:
        return {"text_ar": "الكلمة سلاح من لا سلاح له.", "author": "مجهول"}
    idx = date.today().toordinal() % len(quotes)
    return quotes[idx]

def get_popular_newspapers(limit=8):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT n.*, COUNT(i.id) as issue_count
        FROM newspapers n
        LEFT JOIN issues i ON i.newspaper_id = n.id AND i.status = 'published'
        GROUP BY n.id
        ORDER BY n.visitor_count DESC, issue_count DESC
        LIMIT %s
    """, (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_issues(sort="latest", limit=9):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    order = "i.created_at DESC" if sort == "latest" else "likes_count DESC"
    cursor.execute(f"""
        SELECT i.*, n.name as newspaper_name, n.username,
               COUNT(l.id) as likes_count
        FROM issues i
        JOIN newspapers n ON n.id = i.newspaper_id
        LEFT JOIN likes l ON l.issue_id = i.id
        WHERE i.status = 'published'
        GROUP BY i.id
        ORDER BY {order}
        LIMIT %s
    """, (limit,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_my_issues(newspaper_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.*, COUNT(l.id) as likes_count
        FROM issues i
        LEFT JOIN likes l ON l.issue_id = i.id
        WHERE i.newspaper_id = %s AND i.status = 'published'
        GROUP BY i.id
        ORDER BY i.created_at DESC
    """, (newspaper_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

@app.route("/")
def landing():
    return render_template("landing.html")

@app.route("/home")
def home():
    quote = get_daily_quote()
    newspapers = get_popular_newspapers()
    issues = get_issues("latest")
    my_issues = []
    if session.get("newspaper_id"):
        my_issues = get_my_issues(session["newspaper_id"])
    return render_template("home.html",
        quote=quote,
        newspapers=newspapers,
        issues=issues,
        my_issues=my_issues
    )

@app.route("/api/issues")
def api_issues():
    sort = request.args.get("sort", "latest")
    issues = get_issues(sort)
    for i in issues:
        if i.get("publish_date"):
            i["publish_date"] = str(i["publish_date"])
        if i.get("created_at"):
            i["created_at"] = str(i["created_at"])
    return jsonify(issues)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        import bcrypt
        conn = get_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM newspapers WHERE username = %s", (username,))
        newspaper = cursor.fetchone()
        cursor.close()
        conn.close()
        if newspaper and bcrypt.checkpw(password.encode(), newspaper["password_hash"].encode()):
            session["newspaper_id"] = newspaper["id"]
            session["newspaper_name"] = newspaper["name"]
            session["username"] = newspaper["username"]
            return redirect(url_for("home"))
        flash("اسم المستخدم أو كلمة المرور غلط.")
    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        import bcrypt
        author_name = request.form.get("author_name")
        name = request.form.get("name")
        username = request.form.get("username", "").lower().strip()
        email = request.form.get("email")
        phone = request.form.get("phone")
        password = request.form.get("password")
        category = request.form.get("category")
        frequency = request.form.get("frequency")
        description = request.form.get("description")
        hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
        conn = get_connection()
        cursor = conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO newspapers (author_name, phone, name, username, email, password_hash, category, frequency, description)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (author_name, phone, name, username, email, hashed, category, frequency, description))
            conn.commit()
            flash("تم إنشاء الجريدة بنجاح! سجل دخولك.")
            return redirect(url_for("login"))
        except Exception as e:
            if "Duplicate entry" in str(e):
                flash("اسم المستخدم أو الإيميل موجود بالفعل.")
            else:
                flash(str(e))
        finally:
            cursor.close()
            conn.close()
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))

@app.route("/check-username")
def check_username():
    username = request.args.get("username", "").lower().strip()
    if not username:
        return jsonify({"available": False})
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM newspapers WHERE username = %s", (username,))
    exists = cursor.fetchone()
    cursor.close()
    conn.close()
    return jsonify({"available": not exists})

@app.route("/newspaper/<username>")
def newspaper_view(username):
    return render_template("newspaper.html")

@app.route("/issue/<int:issue_id>")
def issue_view(issue_id):
    return render_template("issue.html")

@app.route("/dashboard")
def dashboard():
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html")

@app.route("/issue/create")
def issue_create():
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    return render_template("issue_builder.html")

if __name__ == "__main__":
    app.run(debug=True)