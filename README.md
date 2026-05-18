# 🎓 PlacePro v3 — Campus Placement Portal

A full-featured campus placement portal with **4 user roles**:
- 👩‍💼 **Super Admin** — Full control over everything
- 🎓 **Placement Coordinator** — Notifications, company registration, student eligibility
- 🏢 **Company Recruiter** — Accept / Reject / Shortlist their company's applicants
- 👨‍🎓 **Student** — Browse and apply to companies

---

## 🚀 How to Run (Step by Step)

### Prerequisites
- Python 3.8+ installed (`python --version` to check)
- pip installed

---

### Step 1 — Extract the ZIP

Unzip `campus-placement-v3.zip` to any folder.

```
cd campus-placement-v3
```

---

### Step 2 — Create a Virtual Environment (Recommended)

**Windows:**
```
python -m venv venv
venv\Scripts\activate
```

**Mac / Linux:**
```
python3 -m venv venv
source venv/bin/activate
```

---

### Step 3 — Install Dependencies

```
pip install -r requirements.txt
```

---

### Step 4 — Initialize the Database

Run this **once** to create the database with all tables and seed data:

```
python database.py
```

You should see:
```
✅ Database initialized successfully!
─────────────────────────────────
Admin Login:        admin / admin123
Coordinator Login:  coordinator@college.edu / coord123
─────────────────────────────────
```

---

### Step 5 — Run the App

```
python app.py
```

Then open your browser and go to:
```
http://127.0.0.1:5000
```

---

## 🔐 Login Credentials

| Role | Login URL | Email / Username | Password |
|------|-----------|-----------------|----------|
| Super Admin | `/admin_login` | `admin` | `admin123` |
| Coordinator | `/coordinator_login` | `coordinator@college.edu` | `coord123` |
| Recruiter | `/recruiter_login` | Created by Admin | Set by Admin |
| Student | `/login` | Register first | Your password |

---

## 📋 Feature Summary

### 👩‍💼 Super Admin (`/admin_login`)
- View dashboard with stats (total students, companies, applications, placed count)
- **Add / Edit / Delete companies**
- **Accept, Reject, Shortlist** student applications (dropdown + quick buttons)
- Verify students and set eligibility
- Add Placement Coordinators (set email + password)
- Add Company Recruiters and assign them to companies
- Export students & applications as CSV

### 🎓 Placement Coordinator (`/coordinator_login`)
- Overview of all placements
- **Verify student eligibility** (mark verified / ineligible)
- **Register new companies** to the portal
- View all applications
- **Send notifications** to:
  - All students
  - Specific branch (e.g., "CS", "ECE")
  - Specific student (by email)

### 🏢 Company Recruiter (`/recruiter_login`)
- Dashboard shows only their company's applicants
- Full applicant table with CGPA bar, resume link, branch, phone
- **Shortlist / Accept / Reject** applicants with instant status update
- Separate tabs for Shortlisted and Selected candidates

### 👨‍🎓 Student (`/register` → `/login`)
- View all available companies
- Apply to companies with one click
- View application statuses with color-coded badges
- Receive **notifications** from the placement coordinator on their dashboard

---

## 🏢 Companies Included (20 total)

| Company | Role | Package | Domain |
|---------|------|---------|--------|
| Google | Software Engineer | 45 LPA | Technology |
| Microsoft | Product Engineer | 38 LPA | Technology |
| Amazon | SDE-1 | 42 LPA | Technology |
| Meta | Software Engineer | 50 LPA | Technology |
| Netflix | Backend Engineer | 55 LPA | Technology |
| Apple | iOS Developer | 48 LPA | Technology |
| Nvidia | AI Engineer | 52 LPA | Technology |
| Uber | Software Engineer | 40 LPA | Technology |
| Adobe | UX Engineer | 35 LPA | Technology |
| Swiggy | Backend Engineer | 22 LPA | Startup |
| Goldman Sachs | Technology Analyst | 32 LPA | Finance |
| JP Morgan | Software Engineer | 30 LPA | Finance |
| Morgan Stanley | Analyst | 28 LPA | Finance |
| McKinsey | Business Analyst | 18 LPA | Consulting |
| Deloitte | Tech Consultant | 9.5 LPA | Consulting |
| KPMG | Data Analyst | 12 LPA | Consulting |
| TCS | Systems Engineer | 7 LPA | IT Services |
| Infosys | Systems Engineer | 6.5 LPA | IT Services |
| Qualcomm | VLSI Engineer | 28 LPA | Semiconductor |
| Intel | Hardware Engineer | 26 LPA | Semiconductor |

---

## 🗂 Project Structure

```
campus-placement-v3/
├── app.py              ← Main Flask application
├── database.py         ← Database setup & seed data
├── requirements.txt    ← Python dependencies
├── placement.db        ← SQLite database (auto-created)
├── static/
│   └── uploads/        ← Student resume uploads
└── templates/
    ├── base.html
    ├── index.html
    ├── jobs.html
    ├── job_detail.html
    ├── register.html
    ├── login.html
    ├── stats.html
    ├── student_dashboard.html
    ├── admin_login.html
    ├── admin_dashboard.html
    ├── edit_company.html
    ├── coordinator_login.html
    ├── coordinator_dashboard.html
    ├── recruiter_login.html
    └── recruiter_dashboard.html
```
