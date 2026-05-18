from flask import Flask, render_template, request, redirect, session, jsonify, flash
import sqlite3
import os
import csv
import io
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import make_response

app = Flask(__name__)
app.secret_key = "placepro_secret_2025_v3"

UPLOAD_FOLDER = "static/uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER


def get_db():
    conn = sqlite3.connect("placement.db")
    conn.row_factory = sqlite3.Row
    return conn


def now():
    return datetime.now().strftime("%d %b %Y, %I:%M %p")


# ─────────────────────────────────────────────
#  HOME & PUBLIC ROUTES
# ─────────────────────────────────────────────

@app.route("/")
def home():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_applications = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    featured = conn.execute("SELECT * FROM companies ORDER BY package DESC LIMIT 3").fetchall()
    conn.close()
    return render_template("index.html",
        total_students=total_students,
        total_companies=total_companies,
        total_applications=total_applications,
        featured=featured)


@app.route("/jobs")
def jobs():
    domain = request.args.get("domain", "All")
    conn = get_db()
    if domain == "All":
        companies = conn.execute("SELECT * FROM companies WHERE verified=1 ORDER BY id DESC").fetchall()
    else:
        companies = conn.execute("SELECT * FROM companies WHERE domain=? AND verified=1 ORDER BY id DESC", (domain,)).fetchall()
    domains = conn.execute("SELECT DISTINCT domain FROM companies").fetchall()
    conn.close()
    return render_template("jobs.html", companies=companies, domains=domains, active_domain=domain)


@app.route("/job/<int:id>")
def job_detail(id):
    conn = get_db()
    company = conn.execute("SELECT * FROM companies WHERE id=?", (id,)).fetchone()
    applied = False
    if "student" in session:
        app_check = conn.execute(
            "SELECT * FROM applications WHERE student_email=? AND company_id=?",
            (session["student"], id)
        ).fetchone()
        applied = app_check is not None
    conn.close()
    if not company:
        return redirect("/jobs")
    return render_template("job_detail.html", company=company, applied=applied)


@app.route("/stats")
def stats():
    conn = get_db()
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_applications = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    domain_stats = conn.execute("SELECT domain, COUNT(*) as cnt FROM companies GROUP BY domain").fetchall()
    conn.close()
    return render_template("stats.html",
        students=total_students,
        companies=total_companies,
        applications=total_applications,
        domain_stats=domain_stats)


# ─────────────────────────────────────────────
#  STUDENT AUTH & DASHBOARD
# ─────────────────────────────────────────────

@app.route("/register", methods=["GET", "POST"])
def register():
    error = None
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        branch = request.form.get("branch", "")
        cgpa = request.form.get("cgpa", 0)
        phone = request.form.get("phone", "")
        resume = request.files.get("resume")
        filename = ""
        if resume and resume.filename:
            filename = secure_filename(resume.filename)
            resume.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))
        conn = get_db()
        existing = conn.execute("SELECT * FROM students WHERE email=?", (email,)).fetchone()
        if existing:
            error = "Email already registered. Please login."
        else:
            conn.execute(
                "INSERT INTO students(name,email,password,resume,branch,cgpa,phone) VALUES(?,?,?,?,?,?,?)",
                (name, email, password, filename, branch, cgpa, phone)
            )
            conn.commit()
            conn.close()
            return redirect("/login")
        conn.close()
    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        user = conn.execute(
            "SELECT * FROM students WHERE email=? AND password=?", (email, password)
        ).fetchone()
        conn.close()
        if user:
            session["student"] = user["email"]
            session["student_name"] = user["name"]
            return redirect("/student_dashboard")
        else:
            error = "Invalid credentials. Please try again."
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/")


@app.route("/student_dashboard")
def student_dashboard():
    if "student" not in session:
        return redirect("/login")
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE email=?", (session["student"],)).fetchone()
    companies = conn.execute("SELECT * FROM companies WHERE verified=1 ORDER BY id DESC").fetchall()
    applied_ids = [
        row["company_id"] for row in conn.execute(
            "SELECT company_id FROM applications WHERE student_email=?", (session["student"],)
        ).fetchall()
    ]
    my_applications = conn.execute("""
        SELECT c.name, c.role, c.package, c.domain, a.applied_on, a.status, a.id as app_id
        FROM applications a
        JOIN companies c ON a.company_id = c.id
        WHERE a.student_email=?
        ORDER BY a.applied_on DESC
    """, (session["student"],)).fetchall()
    # Notifications for student
    notifications = conn.execute("""
        SELECT * FROM notifications
        WHERE target='all'
           OR (target='branch' AND target_value=?)
           OR (target='student' AND target_value=?)
        ORDER BY sent_on DESC LIMIT 10
    """, (student["branch"], student["email"])).fetchall()
    conn.close()
    return render_template("student_dashboard.html",
        student=student,
        companies=companies,
        applied_ids=applied_ids,
        my_applications=my_applications,
        notifications=notifications)


@app.route("/apply/<int:id>")
def apply(id):
    if "student" not in session:
        return redirect("/login")
    conn = get_db()
    student = conn.execute("SELECT * FROM students WHERE email=?", (session["student"],)).fetchone()
    company = conn.execute("SELECT * FROM companies WHERE id=?", (id,)).fetchone()
    already = conn.execute(
        "SELECT * FROM applications WHERE student_email=? AND company_id=?",
        (session["student"], id)
    ).fetchone()
    if not already and company:
        conn.execute(
            "INSERT INTO applications(student_email,company_id) VALUES(?,?)",
            (session["student"], id)
        )
        conn.commit()
    conn.close()
    return redirect("/student_dashboard")


# ─────────────────────────────────────────────
#  ADMIN ROUTES  (Super Admin)
# ─────────────────────────────────────────────

@app.route("/admin_login", methods=["GET", "POST"])
def admin_login():
    error = None
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        conn = get_db()
        admin = conn.execute(
            "SELECT * FROM admin WHERE username=? AND password=?", (username, password)
        ).fetchone()
        conn.close()
        if admin:
            session["admin"] = username
            session["admin_role"] = admin["role"]
            return redirect("/admin_dashboard")
        else:
            error = "Invalid admin credentials."
    return render_template("admin_login.html", error=error)


@app.route("/admin_dashboard", methods=["GET", "POST"])
def admin_dashboard():
    if "admin" not in session:
        return redirect("/admin_login")

    if request.method == "POST":
        action = request.form.get("action", "add_company")
        if action == "add_company":
            name = request.form["name"]
            role = request.form["role"]
            package = request.form["package"]
            location = request.form.get("location", "")
            description = request.form.get("description", "")
            requirements = request.form.get("requirements", "")
            deadline = request.form.get("deadline", "")
            domain = request.form.get("domain", "Technology")
            job_type = request.form.get("type", "Full-Time")
            min_cgpa = request.form.get("min_cgpa", 6.0)
            branches = request.form.get("branches", "All")
            logo = name[:2].upper()
            conn = get_db()
            conn.execute(
                "INSERT INTO companies(name,role,package,logo,location,description,requirements,deadline,domain,type,min_cgpa,branches,added_by,verified) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
                (name, role, package, logo, location, description, requirements, deadline, domain, job_type, min_cgpa, branches, session["admin"])
            )
            conn.commit()
            conn.close()
            return redirect("/admin_dashboard?tab=companies&msg=Company+added+successfully")

    tab = request.args.get("tab", "overview")
    search_student = request.args.get("sq", "")
    search_company = request.args.get("cq", "")
    status_filter = request.args.get("status", "All")

    conn = get_db()
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    placed_count = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Selected'").fetchone()[0]
    pending_count = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Applied'").fetchone()[0]
    rejected_count = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Rejected'").fetchone()[0]
    shortlisted_count = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Shortlisted'").fetchone()[0]

    cq = f"%{search_company}%" if search_company else "%"
    companies = conn.execute("""
        SELECT c.*, COUNT(a.id) as app_count
        FROM companies c
        LEFT JOIN applications a ON a.company_id = c.id
        WHERE c.name LIKE ? OR c.role LIKE ? OR c.domain LIKE ?
        GROUP BY c.id ORDER BY c.id DESC
    """, (cq, cq, cq)).fetchall()

    sq = f"%{search_student}%" if search_student else "%"
    students = conn.execute("""
        SELECT s.*, COUNT(a.id) as app_count,
               SUM(CASE WHEN a.status='Selected' THEN 1 ELSE 0 END) as selected_count
        FROM students s
        LEFT JOIN applications a ON a.student_email = s.email
        WHERE s.name LIKE ? OR s.email LIKE ? OR s.branch LIKE ?
        GROUP BY s.id ORDER BY s.cgpa DESC
    """, (sq, sq, sq)).fetchall()

    app_query = """
        SELECT a.id as app_id, s.name, s.email, s.branch, s.cgpa,
               c.name as company, c.role, c.package, a.applied_on, a.status, c.id as company_id
        FROM applications a
        JOIN students s ON a.student_email = s.email
        JOIN companies c ON a.company_id = c.id
    """
    if status_filter != "All":
        apps = conn.execute(app_query + " WHERE a.status=? ORDER BY a.applied_on DESC", (status_filter,)).fetchall()
    else:
        apps = conn.execute(app_query + " ORDER BY a.applied_on DESC").fetchall()

    domain_stats = conn.execute("SELECT domain, COUNT(*) as cnt FROM companies GROUP BY domain ORDER BY cnt DESC").fetchall()
    recent_apps = conn.execute("""
        SELECT s.name, c.name as company, c.role, a.applied_on, a.status
        FROM applications a
        JOIN students s ON a.student_email = s.email
        JOIN companies c ON a.company_id = c.id
        ORDER BY a.applied_on DESC LIMIT 5
    """).fetchall()
    branch_stats = conn.execute("SELECT branch, COUNT(*) as cnt FROM students WHERE branch != '' GROUP BY branch ORDER BY cnt DESC").fetchall()
    top_companies = conn.execute("""
        SELECT c.name, COUNT(a.id) as app_count
        FROM companies c LEFT JOIN applications a ON a.company_id=c.id
        GROUP BY c.id ORDER BY app_count DESC LIMIT 5
    """).fetchall()
    coordinators = conn.execute("SELECT * FROM coordinators").fetchall()
    recruiters = conn.execute("SELECT r.*, c.name as cname FROM recruiters r LEFT JOIN companies c ON r.company_id=c.id").fetchall()
    conn.close()
    msg = request.args.get("msg", "")

    return render_template("admin_dashboard.html",
        tab=tab, companies=companies, students=students, apps=apps,
        total_companies=total_companies, total_students=total_students,
        total_apps=total_apps, placed_count=placed_count, pending_count=pending_count,
        rejected_count=rejected_count, shortlisted_count=shortlisted_count,
        recent_apps=recent_apps, domain_stats=domain_stats, branch_stats=branch_stats,
        top_companies=top_companies, status_filter=status_filter,
        search_student=search_student, search_company=search_company,
        coordinators=coordinators, recruiters=recruiters, msg=msg)


@app.route("/admin/update_status/<int:app_id>", methods=["POST"])
def update_status(app_id):
    if "admin" not in session:
        return jsonify({"error": "unauthorized"}), 401
    new_status = request.form.get("status")
    allowed = ["Applied", "Shortlisted", "Selected", "Rejected"]
    if new_status not in allowed:
        return jsonify({"error": "invalid status"}), 400
    conn = get_db()
    conn.execute("UPDATE applications SET status=?, updated_by=?, updated_on=? WHERE id=?",
                 (new_status, f"Admin:{session['admin']}", now(), app_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status})


@app.route("/admin/delete_company/<int:id>")
def delete_company(id):
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    conn.execute("DELETE FROM applications WHERE company_id=?", (id,))
    conn.execute("DELETE FROM companies WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=companies&msg=Company+deleted")


@app.route("/admin/edit_company/<int:id>", methods=["GET", "POST"])
def edit_company(id):
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    if request.method == "POST":
        conn.execute("""
            UPDATE companies SET name=?, role=?, package=?, location=?,
            description=?, requirements=?, deadline=?, domain=?, type=?, min_cgpa=?, branches=?
            WHERE id=?
        """, (
            request.form["name"], request.form["role"], request.form["package"],
            request.form.get("location", ""), request.form.get("description", ""),
            request.form.get("requirements", ""), request.form.get("deadline", ""),
            request.form.get("domain", "Technology"), request.form.get("type", "Full-Time"),
            request.form.get("min_cgpa", 6.0), request.form.get("branches", "All"),
            id
        ))
        conn.commit()
        conn.close()
        return redirect("/admin_dashboard?tab=companies&msg=Company+updated+successfully")
    company = conn.execute("SELECT * FROM companies WHERE id=?", (id,)).fetchone()
    conn.close()
    if not company:
        return redirect("/admin_dashboard")
    return render_template("edit_company.html", company=company)


@app.route("/admin/delete_student/<int:id>")
def delete_student(id):
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    email = conn.execute("SELECT email FROM students WHERE id=?", (id,)).fetchone()
    if email:
        conn.execute("DELETE FROM applications WHERE student_email=?", (email["email"],))
        conn.execute("DELETE FROM students WHERE id=?", (id,))
        conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=students&msg=Student+removed")


@app.route("/admin/verify_student/<int:id>")
def admin_verify_student(id):
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    conn.execute("UPDATE students SET verified=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=students&msg=Student+verified")


@app.route("/admin/toggle_eligible/<int:id>")
def admin_toggle_eligible(id):
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    student = conn.execute("SELECT eligible FROM students WHERE id=?", (id,)).fetchone()
    new_val = 0 if student["eligible"] else 1
    conn.execute("UPDATE students SET eligible=? WHERE id=?", (new_val, id))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=students")


@app.route("/admin/add_coordinator", methods=["POST"])
def add_coordinator():
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    conn.execute("INSERT OR IGNORE INTO coordinators(name,email,password,department) VALUES(?,?,?,?)",
                 (request.form["name"], request.form["email"], request.form["password"], request.form.get("department", "Placement Cell")))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=team&msg=Coordinator+added")


@app.route("/admin/add_recruiter", methods=["POST"])
def add_recruiter():
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    company_id = request.form.get("company_id")
    company = conn.execute("SELECT name FROM companies WHERE id=?", (company_id,)).fetchone()
    cname = company["name"] if company else ""
    conn.execute("INSERT OR IGNORE INTO recruiters(name,email,password,company_id,company_name) VALUES(?,?,?,?,?)",
                 (request.form["name"], request.form["email"], request.form["password"], company_id, cname))
    if company_id:
        conn.execute("UPDATE companies SET recruiter_email=? WHERE id=?", (request.form["email"], company_id))
    conn.commit()
    conn.close()
    return redirect("/admin_dashboard?tab=team&msg=Recruiter+added")


@app.route("/admin/export/students")
def export_students():
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    students = conn.execute("""
        SELECT s.name, s.email, s.branch, s.cgpa,
               COUNT(a.id) as applications,
               SUM(CASE WHEN a.status='Selected' THEN 1 ELSE 0 END) as selected
        FROM students s
        LEFT JOIN applications a ON a.student_email = s.email
        GROUP BY s.id ORDER BY s.cgpa DESC
    """).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Name", "Email", "Branch", "CGPA", "Applications", "Selected"])
    for s in students:
        writer.writerow([s["name"], s["email"], s["branch"], s["cgpa"], s["applications"], s["selected"]])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=students.csv"
    response.headers["Content-type"] = "text/csv"
    return response


@app.route("/admin/export/applications")
def export_applications():
    if "admin" not in session:
        return redirect("/admin_login")
    conn = get_db()
    apps = conn.execute("""
        SELECT s.name, s.email, s.branch, s.cgpa, c.name as company, c.role, c.package, a.applied_on, a.status
        FROM applications a
        JOIN students s ON a.student_email = s.email
        JOIN companies c ON a.company_id = c.id
        ORDER BY a.applied_on DESC
    """).fetchall()
    conn.close()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Student", "Email", "Branch", "CGPA", "Company", "Role", "Package", "Applied On", "Status"])
    for a in apps:
        writer.writerow([a["name"], a["email"], a["branch"], a["cgpa"],
                         a["company"], a["role"], a["package"], a["applied_on"], a["status"]])
    response = make_response(output.getvalue())
    response.headers["Content-Disposition"] = "attachment; filename=applications.csv"
    response.headers["Content-type"] = "text/csv"
    return response


# ─────────────────────────────────────────────
#  COORDINATOR ROUTES
# ─────────────────────────────────────────────

@app.route("/coordinator_login", methods=["GET", "POST"])
def coordinator_login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        coord = conn.execute(
            "SELECT * FROM coordinators WHERE email=? AND password=?", (email, password)
        ).fetchone()
        conn.close()
        if coord:
            session["coordinator"] = coord["email"]
            session["coordinator_name"] = coord["name"]
            return redirect("/coordinator_dashboard")
        else:
            error = "Invalid coordinator credentials."
    return render_template("coordinator_login.html", error=error)


@app.route("/coordinator_dashboard", methods=["GET", "POST"])
def coordinator_dashboard():
    if "coordinator" not in session:
        return redirect("/coordinator_login")

    tab = request.args.get("tab", "overview")
    conn = get_db()

    total_students = conn.execute("SELECT COUNT(*) FROM students").fetchone()[0]
    total_companies = conn.execute("SELECT COUNT(*) FROM companies").fetchone()[0]
    total_apps = conn.execute("SELECT COUNT(*) FROM applications").fetchone()[0]
    placed_count = conn.execute("SELECT COUNT(*) FROM applications WHERE status='Selected'").fetchone()[0]

    students = conn.execute("""
        SELECT s.*, COUNT(a.id) as app_count,
               SUM(CASE WHEN a.status='Selected' THEN 1 ELSE 0 END) as selected_count
        FROM students s
        LEFT JOIN applications a ON a.student_email = s.email
        GROUP BY s.id ORDER BY s.cgpa DESC
    """).fetchall()

    companies = conn.execute("SELECT * FROM companies ORDER BY id DESC").fetchall()
    all_companies = conn.execute("SELECT id, name FROM companies ORDER BY name").fetchall()

    notifications = conn.execute("SELECT * FROM notifications ORDER BY sent_on DESC LIMIT 20").fetchall()

    apps = conn.execute("""
        SELECT a.id as app_id, s.name, s.email, s.branch, s.cgpa, s.phone,
               c.name as company, c.role, c.package, a.applied_on, a.status
        FROM applications a
        JOIN students s ON a.student_email = s.email
        JOIN companies c ON a.company_id = c.id
        ORDER BY a.applied_on DESC
    """).fetchall()

    conn.close()
    msg = request.args.get("msg", "")

    return render_template("coordinator_dashboard.html",
        tab=tab, students=students, companies=companies,
        all_companies=all_companies, notifications=notifications, apps=apps,
        total_students=total_students, total_companies=total_companies,
        total_apps=total_apps, placed_count=placed_count, msg=msg)


@app.route("/coordinator/send_notification", methods=["POST"])
def send_notification():
    if "coordinator" not in session:
        return redirect("/coordinator_login")
    title = request.form["title"]
    message = request.form["message"]
    target = request.form.get("target", "all")
    target_value = request.form.get("target_value", "")
    notif_type = request.form.get("type", "info")
    conn = get_db()
    conn.execute(
        "INSERT INTO notifications(title,message,target,target_value,sent_by,type) VALUES(?,?,?,?,?,?)",
        (title, message, target, target_value, session["coordinator_name"], notif_type)
    )
    conn.commit()
    conn.close()
    return redirect("/coordinator_dashboard?tab=notifications&msg=Notification+sent")


@app.route("/coordinator/add_company", methods=["POST"])
def coordinator_add_company():
    if "coordinator" not in session:
        return redirect("/coordinator_login")
    name = request.form["name"]
    role = request.form["role"]
    package = request.form["package"]
    location = request.form.get("location", "")
    description = request.form.get("description", "")
    requirements = request.form.get("requirements", "")
    deadline = request.form.get("deadline", "")
    domain = request.form.get("domain", "Technology")
    job_type = request.form.get("type", "Full-Time")
    min_cgpa = request.form.get("min_cgpa", 6.0)
    branches = request.form.get("branches", "All")
    logo = name[:2].upper()
    conn = get_db()
    conn.execute(
        "INSERT INTO companies(name,role,package,logo,location,description,requirements,deadline,domain,type,min_cgpa,branches,added_by,verified) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,1)",
        (name, role, package, logo, location, description, requirements, deadline, domain, job_type, min_cgpa, branches, session["coordinator"])
    )
    conn.commit()
    conn.close()
    return redirect("/coordinator_dashboard?tab=companies&msg=Company+registered+successfully")


@app.route("/coordinator/verify_student/<int:id>")
def coordinator_verify_student(id):
    if "coordinator" not in session:
        return redirect("/coordinator_login")
    conn = get_db()
    conn.execute("UPDATE students SET verified=1 WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect("/coordinator_dashboard?tab=students&msg=Student+eligibility+verified")


@app.route("/coordinator/set_eligible/<int:id>/<int:val>")
def coordinator_set_eligible(id, val):
    if "coordinator" not in session:
        return redirect("/coordinator_login")
    conn = get_db()
    conn.execute("UPDATE students SET eligible=? WHERE id=?", (val, id))
    conn.commit()
    conn.close()
    return redirect("/coordinator_dashboard?tab=students")


@app.route("/coordinator_logout")
def coordinator_logout():
    session.pop("coordinator", None)
    session.pop("coordinator_name", None)
    return redirect("/")


# ─────────────────────────────────────────────
#  RECRUITER ROUTES
# ─────────────────────────────────────────────

@app.route("/recruiter_login", methods=["GET", "POST"])
def recruiter_login():
    error = None
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = get_db()
        recruiter = conn.execute(
            "SELECT * FROM recruiters WHERE email=? AND password=?", (email, password)
        ).fetchone()
        conn.close()
        if recruiter:
            session["recruiter"] = recruiter["email"]
            session["recruiter_name"] = recruiter["name"]
            session["recruiter_company_id"] = recruiter["company_id"]
            session["recruiter_company_name"] = recruiter["company_name"]
            return redirect("/recruiter_dashboard")
        else:
            error = "Invalid recruiter credentials."
    return render_template("recruiter_login.html", error=error)


@app.route("/recruiter_dashboard")
def recruiter_dashboard():
    if "recruiter" not in session:
        return redirect("/recruiter_login")

    company_id = session["recruiter_company_id"]
    tab = request.args.get("tab", "overview")
    status_filter = request.args.get("status", "All")
    conn = get_db()

    company = conn.execute("SELECT * FROM companies WHERE id=?", (company_id,)).fetchone()

    app_query = """
        SELECT a.id as app_id, s.name, s.email, s.branch, s.cgpa, s.phone, s.resume,
               s.verified, s.eligible,
               a.applied_on, a.status
        FROM applications a
        JOIN students s ON a.student_email = s.email
        WHERE a.company_id=?
    """
    if status_filter != "All":
        apps = conn.execute(app_query + " AND a.status=? ORDER BY s.cgpa DESC", (company_id, status_filter)).fetchall()
    else:
        apps = conn.execute(app_query + " ORDER BY s.cgpa DESC", (company_id,)).fetchall()

    total = conn.execute("SELECT COUNT(*) FROM applications WHERE company_id=?", (company_id,)).fetchone()[0]
    shortlisted = conn.execute("SELECT COUNT(*) FROM applications WHERE company_id=? AND status='Shortlisted'", (company_id,)).fetchone()[0]
    selected = conn.execute("SELECT COUNT(*) FROM applications WHERE company_id=? AND status='Selected'", (company_id,)).fetchone()[0]
    rejected = conn.execute("SELECT COUNT(*) FROM applications WHERE company_id=? AND status='Rejected'", (company_id,)).fetchone()[0]

    conn.close()
    msg = request.args.get("msg", "")

    return render_template("recruiter_dashboard.html",
        company=company, apps=apps, tab=tab,
        total=total, shortlisted=shortlisted, selected=selected, rejected=rejected,
        status_filter=status_filter, msg=msg)


@app.route("/recruiter/update_status/<int:app_id>", methods=["POST"])
def recruiter_update_status(app_id):
    if "recruiter" not in session:
        return jsonify({"error": "unauthorized"}), 401
    new_status = request.form.get("status")
    allowed = ["Applied", "Shortlisted", "Selected", "Rejected"]
    if new_status not in allowed:
        return jsonify({"error": "invalid status"}), 400
    conn = get_db()
    # Ensure recruiter can only update apps for their company
    company_id = session["recruiter_company_id"]
    app_row = conn.execute("SELECT * FROM applications WHERE id=? AND company_id=?", (app_id, company_id)).fetchone()
    if not app_row:
        conn.close()
        return jsonify({"error": "not found"}), 404
    conn.execute("UPDATE applications SET status=?, updated_by=?, updated_on=? WHERE id=?",
                 (new_status, f"Recruiter:{session['recruiter']}", now(), app_id))
    conn.commit()
    conn.close()
    return jsonify({"success": True, "status": new_status})


@app.route("/recruiter_logout")
def recruiter_logout():
    for key in ["recruiter", "recruiter_name", "recruiter_company_id", "recruiter_company_name"]:
        session.pop(key, None)
    return redirect("/")


if __name__ == "__main__":
    app.run(debug=True)
