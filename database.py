import sqlite3

conn = sqlite3.connect("placement.db")

# ── Students ─────────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS students(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  email TEXT UNIQUE,
  password TEXT,
  resume TEXT,
  cgpa REAL DEFAULT 0,
  branch TEXT DEFAULT '',
  year INTEGER DEFAULT 4,
  phone TEXT DEFAULT '',
  verified INTEGER DEFAULT 0,
  eligible INTEGER DEFAULT 1
)
""")

# ── Companies ─────────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS companies(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  role TEXT,
  package TEXT,
  logo TEXT,
  location TEXT,
  description TEXT,
  requirements TEXT,
  deadline TEXT,
  type TEXT DEFAULT 'Full-Time',
  domain TEXT DEFAULT 'Technology',
  min_cgpa REAL DEFAULT 6.0,
  branches TEXT DEFAULT 'All',
  verified INTEGER DEFAULT 1,
  added_by TEXT DEFAULT 'admin',
  recruiter_email TEXT DEFAULT ''
)
""")

# ── Applications ──────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS applications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  student_email TEXT,
  company_id INTEGER,
  applied_on TEXT DEFAULT CURRENT_TIMESTAMP,
  status TEXT DEFAULT 'Applied',
  updated_by TEXT DEFAULT '',
  updated_on TEXT DEFAULT ''
)
""")

# ── Admin ─────────────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS admin(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  username TEXT UNIQUE,
  password TEXT,
  role TEXT DEFAULT 'admin'
)
""")

# ── Coordinators (College Placement Office) ────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS coordinators(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  email TEXT UNIQUE,
  password TEXT,
  department TEXT DEFAULT 'Placement Cell'
)
""")

# ── Recruiters (Company HR) ───────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS recruiters(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  name TEXT,
  email TEXT UNIQUE,
  password TEXT,
  company_id INTEGER,
  company_name TEXT
)
""")

# ── Notifications ─────────────────────────────────────────────
conn.execute("""
CREATE TABLE IF NOT EXISTS notifications(
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  title TEXT,
  message TEXT,
  target TEXT DEFAULT 'all',
  target_value TEXT DEFAULT '',
  sent_by TEXT,
  sent_on TEXT DEFAULT CURRENT_TIMESTAMP,
  type TEXT DEFAULT 'info'
)
""")

# ── Seed Data ─────────────────────────────────────────────────
conn.execute("DELETE FROM admin")
conn.execute("INSERT INTO admin(username,password,role) VALUES('admin','admin123','super_admin')")

conn.execute("DELETE FROM coordinators")
conn.execute("""
  INSERT INTO coordinators(name,email,password,department)
  VALUES('Dr. Priya Sharma','coordinator@college.edu','coord123','Placement Cell')
""")

# Seed companies (20 companies across domains)
companies = [
    # Technology
    ("Google", "Software Engineer", "45 LPA", "G", "Bangalore / Hyderabad",
     "Join Google's world-class engineering team and work on products used by billions. Collaborate on Search, Maps, YouTube, Cloud, and more.",
     "B.Tech CS/IT/ECE | CGPA 7.5+ | Strong DSA | System Design", "15 Jun 2025", "Full-Time", "Technology", 7.5, "CS,IT,ECE", ""),
    ("Microsoft", "Product Engineer", "38 LPA", "M", "Hyderabad / Noida",
     "Microsoft leads in cloud, AI, and productivity software. Work on Azure, Office 365, Teams, and next-gen developer tools.",
     "B.Tech CS/IT | CGPA 7.0+ | C#/Java/Python | Cloud Basics", "20 Jun 2025", "Full-Time", "Technology", 7.0, "CS,IT", ""),
    ("Amazon", "SDE-1", "42 LPA", "A", "Bangalore / Chennai",
     "Amazon engineers solve problems at massive scale. Work on AWS, e-commerce, logistics, and Alexa.",
     "B.Tech CS/IT | CGPA 7.0+ | OOP & System Design | AWS Knowledge", "1 Jul 2025", "Full-Time", "Technology", 7.0, "CS,IT", ""),
    ("Adobe", "UX Engineer", "35 LPA", "Ad", "Noida / Bangalore",
     "Adobe leads in creative software and digital experiences. Build next-gen design tools and creative cloud products.",
     "CS/IT/Design | CGPA 7.5+ | Frontend Skills | UX Sensibility | Portfolio preferred", "18 Jul 2025", "Full-Time", "Technology", 7.5, "CS,IT,Design", ""),
    ("Meta", "Software Engineer", "50 LPA", "Fb", "Bangalore",
     "Meta builds technologies that help people connect. Work on Facebook, Instagram, WhatsApp, and the Metaverse at hyper-scale.",
     "B.Tech CS/IT | CGPA 8.0+ | Distributed Systems | Strong Algorithms", "10 Jul 2025", "Full-Time", "Technology", 8.0, "CS,IT", ""),
    ("Apple", "iOS Developer", "48 LPA", "Ap", "Hyderabad",
     "Apple creates products that change the world. Build features used by 1B+ iPhone users in Swift and Objective-C.",
     "CS/IT | CGPA 8.0+ | Swift/Objective-C | Mobile Development experience", "25 Jul 2025", "Full-Time", "Technology", 8.0, "CS,IT", ""),
    ("Netflix", "Backend Engineer", "55 LPA", "Nf", "Bangalore",
     "Netflix entertains the world. Build the streaming platform that powers 200M+ subscribers across 190 countries.",
     "B.Tech CS/IT | CGPA 8.0+ | Java/Python | Microservices | Distributed Systems", "20 Jul 2025", "Full-Time", "Technology", 8.0, "CS,IT", ""),
    ("Uber", "Software Engineer", "40 LPA", "Ub", "Hyderabad",
     "Uber re-imagines how cities work through technology. Build mobility and delivery platforms serving millions daily.",
     "CS/IT | CGPA 7.5+ | Backend/Mobile Dev | Real-time systems", "15 Jul 2025", "Full-Time", "Technology", 7.5, "CS,IT", ""),
    ("Swiggy", "Backend Engineer", "22 LPA", "Sw", "Bangalore",
     "India's #1 food delivery platform. Work on real-time logistics, ML-powered recommendations, and high-throughput APIs.",
     "B.Tech CS/IT | CGPA 6.5+ | Backend Frameworks | Database Knowledge", "15 Jun 2025", "Full-Time", "Startup", 6.5, "CS,IT", ""),
    # Finance
    ("Goldman Sachs", "Technology Analyst", "32 LPA", "GS", "Bangalore",
     "Goldman Sachs engineering powers global financial markets. Build high-performance trading systems and financial platforms.",
     "Any Branch | CGPA 8.0+ | Strong Programming | Quantitative Aptitude", "25 Jun 2025", "Full-Time", "Finance", 8.0, "All", ""),
    ("JP Morgan", "Software Engineer", "30 LPA", "JP", "Mumbai / Bangalore",
     "J.P. Morgan is a global leader in financial services. Build fintech solutions powering trillions in daily transactions.",
     "CS/IT/Math | CGPA 7.5+ | Java/Python | Financial systems knowledge", "30 Jun 2025", "Full-Time", "Finance", 7.5, "CS,IT,Maths", ""),
    ("Morgan Stanley", "Analyst", "28 LPA", "MS", "Mumbai",
     "Morgan Stanley leads global investment banking. Drive digital transformation of equity trading and wealth management platforms.",
     "Any Branch | CGPA 7.5+ | Problem Solving | Communication Skills", "5 Jul 2025", "Full-Time", "Finance", 7.5, "All", ""),
    # Consulting
    ("Deloitte", "Tech Consultant", "9.5 LPA", "D", "Pan India",
     "Deloitte bridges business and technology. Lead digital transformation across banking, retail, healthcare, and government.",
     "Any Branch | CGPA 6.5+ | Strong Communication | Analytical Thinking", "5 Jul 2025", "Full-Time", "Consulting", 6.5, "All", ""),
    ("KPMG", "Data Analyst", "12 LPA", "K", "Mumbai / Delhi",
     "KPMG's analytics practice helps Fortune 500 companies make smarter decisions using Python, Power BI and SQL.",
     "B.Tech/Stats/MBA | CGPA 6.5+ | SQL & Python | Data Visualization", "20 Jun 2025", "Full-Time", "Consulting", 6.5, "All", ""),
    ("McKinsey", "Business Analyst", "18 LPA", "Mc", "Delhi / Mumbai",
     "McKinsey & Company is the world's foremost management consulting firm. Solve complex strategic problems for global leaders.",
     "Any Branch | CGPA 8.0+ | Case Solving | Leadership Experience", "1 Jun 2025", "Full-Time", "Consulting", 8.0, "All", ""),
    # IT Services
    ("Infosys", "Systems Engineer", "6.5 LPA", "In", "Pan India",
     "Start your career at one of India's largest IT companies. Get global exposure through enterprise technology projects.",
     "B.Tech/MCA Any Branch | CGPA 6.0+ | No Active Backlogs", "10 Jun 2025", "Full-Time", "IT Services", 6.0, "All", ""),
    ("TCS", "Systems Engineer", "7 LPA", "TC", "Pan India",
     "TCS is a global leader in IT services. Work on cutting-edge projects for Fortune 500 clients worldwide.",
     "Any Branch | CGPA 6.0+ | No Backlogs | Aptitude Test", "12 Jun 2025", "Full-Time", "IT Services", 6.0, "All", ""),
    # Semiconductor / Core
    ("Qualcomm", "VLSI Engineer", "28 LPA", "Q", "Hyderabad / Bangalore",
     "Qualcomm leads the world in wireless technology. Design 5G processors, AI accelerators, and embedded systems.",
     "B.Tech ECE/EEE | CGPA 7.5+ | VHDL/Verilog | Digital Design", "12 Jun 2025", "Full-Time", "Semiconductor", 7.5, "ECE,EEE", ""),
    ("Intel", "Hardware Engineer", "26 LPA", "Int", "Hyderabad / Bangalore",
     "Intel drives innovation in silicon. Work on next-gen processors, memory systems, and AI accelerators.",
     "ECE/EEE | CGPA 7.5+ | Computer Architecture | VLSI Design", "8 Jul 2025", "Full-Time", "Semiconductor", 7.5, "ECE,EEE", ""),
    # Data / AI
    ("Nvidia", "AI Engineer", "52 LPA", "Nv", "Bangalore / Hyderabad",
     "NVIDIA accelerates AI. Work on GPU computing, deep learning frameworks, and autonomous driving systems.",
     "CS/IT/ECE | CGPA 8.0+ | Deep Learning | CUDA/PyTorch | Research Papers a plus", "30 Jun 2025", "Full-Time", "Technology", 8.0, "CS,IT,ECE", ""),
]

conn.execute("DELETE FROM companies")
conn.executemany("""
  INSERT INTO companies(name,role,package,logo,location,description,requirements,deadline,type,domain,min_cgpa,branches,recruiter_email)
  VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)
""", companies)

conn.commit()
conn.close()
print("✅ Database initialized successfully!")
print("─────────────────────────────────")
print("Admin Login:        admin / admin123")
print("Coordinator Login:  coordinator@college.edu / coord123")
print("─────────────────────────────────")
