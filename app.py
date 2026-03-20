from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
from dotenv import load_dotenv
from database import get_connection
import os
from datetime import date
from werkzeug.utils import secure_filename

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "zeintimes_secret")
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

from database import init_db
with app.app_context():
    init_db()


STYLES = {
    "كلاسيكي": {"bg":"#f5f0e8","header_bg":"#2c1810","header_color":"#f5f0e8","text_color":"#2c1810","section_bg":"#fff8f0","border":"#8b6914","section_title_color":"#8b6914"},
    "علمي":    {"bg":"#f0f4f8","header_bg":"#1a3a5c","header_color":"#ffffff","text_color":"#1a2a3a","section_bg":"#ffffff","border":"#2980b9","section_title_color":"#1a3a5c"},
    "عصور وسطى":{"bg":"#f4e8c1","header_bg":"#3d1f00","header_color":"#f4e8c1","text_color":"#3d1f00","section_bg":"#fdf3d0","border":"#8b4513","section_title_color":"#8b4513"},
    "نمط الحياة":{"bg":"#fff0f5","header_bg":"#e91e8c","header_color":"#ffffff","text_color":"#333333","section_bg":"#ffffff","border":"#e91e8c","section_title_color":"#e91e8c"},
    "رياضي":   {"bg":"#f0f0f0","header_bg":"#1a1a1a","header_color":"#f5c518","text_color":"#1a1a1a","section_bg":"#ffffff","border":"#f5c518","section_title_color":"#f5c518"},
}

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
        WHERE i.newspaper_id = %s
        GROUP BY i.id
        ORDER BY i.created_at DESC
    """, (newspaper_id,))
    result = cursor.fetchall()
    cursor.close()
    conn.close()
    return result

def get_newspaper_by_id(newspaper_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM newspapers WHERE id = %s", (newspaper_id,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_newspaper_by_username(username):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM newspapers WHERE username = %s", (username,))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result

def get_followers_count(newspaper_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM follows WHERE following_id = %s", (newspaper_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def get_following_count(newspaper_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM follows WHERE follower_id = %s", (newspaper_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count

def is_following(follower_id, following_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM follows WHERE follower_id = %s AND following_id = %s",
                   (follower_id, following_id))
    result = cursor.fetchone()
    cursor.close()
    conn.close()
    return result is not None

def get_newspaper_issues(newspaper_id):
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

def get_issue_data(issue_id):
    conn = get_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("""
        SELECT i.*, n.name as newspaper_name, n.username, n.id as newspaper_id,
               COUNT(l.id) as likes_count
        FROM issues i
        JOIN newspapers n ON n.id = i.newspaper_id
        LEFT JOIN likes l ON l.issue_id = i.id
        WHERE i.id = %s
        GROUP BY i.id
    """, (issue_id,))
    issue = cursor.fetchone()
    cursor.execute("SELECT * FROM sections WHERE issue_id = %s ORDER BY section_order", (issue_id,))
    sections = cursor.fetchall()
    cursor.close()
    conn.close()
    return issue, sections

def get_next_issue_number(newspaper_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM issues WHERE newspaper_id = %s", (newspaper_id,))
    count = cursor.fetchone()[0]
    cursor.close()
    conn.close()
    return count + 1

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
    return render_template("home.html", quote=quote, newspapers=newspapers, issues=issues, my_issues=my_issues)

@app.route("/api/issues")
def api_issues():
    sort = request.args.get("sort", "latest")
    issues = get_issues(sort)
    for i in issues:
        if i.get("publish_date"): i["publish_date"] = str(i["publish_date"])
        if i.get("created_at"): i["created_at"] = str(i["created_at"])
    return jsonify(issues)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        import bcrypt
        username = request.form.get("username")
        password = request.form.get("password")
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
            flash("اسم المستخدم أو الإيميل موجود بالفعل." if "Duplicate entry" in str(e) else str(e))
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

@app.route("/dashboard")
def dashboard():
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    newspaper_id = session["newspaper_id"]
    return render_template("dashboard.html",
        newspaper=get_newspaper_by_id(newspaper_id),
        issues=get_my_issues(newspaper_id),
        followers_count=get_followers_count(newspaper_id),
        following_count=get_following_count(newspaper_id)
    )

@app.route("/dashboard/update", methods=["POST"])
def dashboard_update():
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE newspapers SET description=%s, category=%s, frequency=%s WHERE id=%s",
        (request.form.get("description"), request.form.get("category"),
         request.form.get("frequency"), session["newspaper_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    flash("تم حفظ التغييرات!")
    return redirect(url_for("dashboard"))

@app.route("/issue/create", methods=["GET", "POST"])
def issue_create():
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    if request.method == "POST":
        title = request.form.get("title")
        issue_number = request.form.get("issue_number")
        publish_date = request.form.get("publish_date")
        style = request.form.get("style", "كلاسيكي")
        sections_count = int(request.form.get("sections_count", 3))
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO issues (newspaper_id, title, issue_number, publish_date, style, status)
            VALUES (%s, %s, %s, %s, %s, 'draft')
        """, (session["newspaper_id"], title, issue_number, publish_date, style))
        issue_id = cursor.lastrowid
        for i in range(sections_count):
            sec_title = request.form.get(f"section_title_{i}", f"فقرة {i+1}")
            sec_text = request.form.get(f"section_text_{i}", "")
            image_path = None
            img_file = request.files.get(f"section_image_{i}")
            if img_file and img_file.filename:
                filename = secure_filename(f"{issue_id}_{i}_{img_file.filename}")
                img_file.save(os.path.join(UPLOAD_FOLDER, filename))
                image_path = os.path.join(UPLOAD_FOLDER, filename)
            cursor.execute("""
                INSERT INTO sections (issue_id, title, body_text, image_path, section_order)
                VALUES (%s, %s, %s, %s, %s)
            """, (issue_id, sec_title, sec_text, image_path, i+1))
        conn.commit()
        cursor.close()
        conn.close()
        return redirect(url_for("issue_view", issue_id=issue_id))
    next_num = get_next_issue_number(session["newspaper_id"])
    return render_template("issue_builder.html", next_issue_number=next_num)

@app.route("/issue/<int:issue_id>")
def issue_view(issue_id):
    issue, sections = get_issue_data(issue_id)
    if not issue:
        flash("العدد غير موجود.")
        return redirect(url_for("home"))
    style = STYLES.get(issue["style"], STYLES["كلاسيكي"])
    is_liked = False
    if session.get("newspaper_id"):
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM likes WHERE issue_id=%s AND newspaper_id=%s",
                       (issue_id, session["newspaper_id"]))
        is_liked = cursor.fetchone() is not None
        cursor.close()
        conn.close()
    return render_template("issue.html", issue=issue, sections=sections, style=style, is_liked=is_liked)

@app.route("/issue/<int:issue_id>/publish", methods=["POST"])
def issue_publish(issue_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE issues SET status='published' WHERE id=%s AND newspaper_id=%s",
                   (issue_id, session["newspaper_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    flash("تم النشر بنجاح!")
    return redirect(url_for("issue_view", issue_id=issue_id))

@app.route("/issue/<int:issue_id>/like", methods=["POST"])
def like_issue(issue_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM likes WHERE issue_id=%s AND newspaper_id=%s",
                   (issue_id, session["newspaper_id"]))
    if cursor.fetchone():
        cursor.execute("DELETE FROM likes WHERE issue_id=%s AND newspaper_id=%s",
                       (issue_id, session["newspaper_id"]))
    else:
        cursor.execute("INSERT INTO likes (issue_id, newspaper_id) VALUES (%s, %s)",
                       (issue_id, session["newspaper_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(request.referrer or url_for("issue_view", issue_id=issue_id))

@app.route("/issue/<int:issue_id>/edit", methods=["GET", "POST"])
def issue_edit(issue_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    next_num = get_next_issue_number(session["newspaper_id"])
    return render_template("issue_builder.html", next_issue_number=next_num)

@app.route("/issue/<int:issue_id>/delete", methods=["POST"])
def issue_delete(issue_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM sections WHERE issue_id=%s", (issue_id,))
    cursor.execute("DELETE FROM likes WHERE issue_id=%s", (issue_id,))
    cursor.execute("DELETE FROM issues WHERE id=%s AND newspaper_id=%s",
                   (issue_id, session["newspaper_id"]))
    conn.commit()
    cursor.close()
    conn.close()
    flash("تم حذف العدد.")
    return redirect(url_for("dashboard"))

@app.route("/issue/<int:issue_id>/download/<fmt>")
def issue_download(issue_id, fmt):
    from export import export_word, export_pdf
    issue, sections = get_issue_data(issue_id)
    if not issue:
        flash("العدد غير موجود.")
        return redirect(url_for("home"))
    if fmt == "word":
        path = export_word(issue, sections)
        return send_file(path, as_attachment=True,
                         download_name=f"{issue['title']}.docx",
                         mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")
    elif fmt == "pdf":
        path = export_pdf(issue, sections)
        return send_file(path, as_attachment=True,
                         download_name=f"{issue['title']}.pdf",
                         mimetype="application/pdf")
    return "صيغة غير مدعومة", 400

@app.route("/uploads/<filename>")
def uploaded_file(filename):
    return send_file(os.path.join(UPLOAD_FOLDER, filename))

@app.route("/newspaper/<username>")
def newspaper_view(username):
    newspaper = get_newspaper_by_username(username)
    if not newspaper:
        flash("الجريدة غير موجودة.")
        return redirect(url_for("home"))
    issues = get_newspaper_issues(newspaper["id"])
    followers_count = get_followers_count(newspaper["id"])
    following = False
    if session.get("newspaper_id"):
        following = is_following(session["newspaper_id"], newspaper["id"])
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE newspapers SET visitor_count=visitor_count+1 WHERE id=%s", (newspaper["id"],))
        conn.commit()
        cursor.close()
        conn.close()
    return render_template("newspaper.html", newspaper=newspaper, issues=issues,
                           followers_count=followers_count, is_following=following)

@app.route("/newspaper/<int:newspaper_id>/follow", methods=["POST"])
def follow(newspaper_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT IGNORE INTO follows (follower_id, following_id) VALUES (%s, %s)",
                       (session["newspaper_id"], newspaper_id))
        conn.commit()
    except: pass
    finally:
        cursor.close()
        conn.close()
    return redirect(request.referrer or url_for("home"))

@app.route("/newspaper/<int:newspaper_id>/unfollow", methods=["POST"])
def unfollow(newspaper_id):
    if "newspaper_id" not in session:
        return redirect(url_for("login"))
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM follows WHERE follower_id=%s AND following_id=%s",
                   (session["newspaper_id"], newspaper_id))
    conn.commit()
    cursor.close()
    conn.close()
    return redirect(request.referrer or url_for("home"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)