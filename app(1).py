import streamlit as st
import sqlite3
import pandas as pd
import re
import spacy
import pdfplumber
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import matplotlib.pyplot as plt
from collections import Counter

# Load SpaCy model
nlp = spacy.load("en_core_web_sm")

# Email sending function
def send_email(receiver_email, candidate_name):
    sender_email = 'shrutiashinde26@gmail.com'  # Your Gmail
    sender_password = 'uenm qhvh nllw odwj'  # Your 16-digit App password

    subject = "Congratulations on Your Shortlisting!"
    body = f"""
    Dear {candidate_name},

    Congratulations! 🎉

    We are pleased to inform you that your resume has been shortlisted based on your skills and experience.

    Our team will be in touch with you for the next steps.

    Best regards,  
    Recruitment Team
    """

    msg = MIMEMultipart()
    msg['From'] = sender_email
    msg['To'] = receiver_email
    msg['Subject'] = subject

    msg.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP('smtp.gmail.com', 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, receiver_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Error: {e}")
        return False

# Database connection
def connect_db():
    conn = sqlite3.connect('resumes.db')
    return conn

def create_table(conn):
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        data_engineer_score REAL,
        software_developer_score REAL,
        data_scientist_score REAL,
        machine_engineer_score REAL,
        best_role TEXT
    )
    ''')

    c.execute("PRAGMA table_info(resumes);")
    columns = c.fetchall()
    existing_columns = [column[1] for column in columns]

    if 'data_engineer_score' not in existing_columns:
        c.execute('ALTER TABLE resumes ADD COLUMN data_engineer_score REAL;')
    if 'software_developer_score' not in existing_columns:
        c.execute('ALTER TABLE resumes ADD COLUMN software_developer_score REAL;')
    if 'data_scientist_score' not in existing_columns:
        c.execute('ALTER TABLE resumes ADD COLUMN data_scientist_score REAL;')
    if 'machine_engineer_score' not in existing_columns:
        c.execute('ALTER TABLE resumes ADD COLUMN machine_engineer_score REAL;')
    if 'best_role' not in existing_columns:
        c.execute('ALTER TABLE resumes ADD COLUMN best_role TEXT;')

    c.execute('''CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT,
        email TEXT,
        phone TEXT,
        skills TEXT,
        data_engineer_score REAL,
        software_developer_score REAL,
        data_scientist_score REAL,
        machine_engineer_score REAL,
        best_role TEXT
    )''')
    conn.commit()

role_skills = {
    'Data Engineer': ['python', 'sql', 'hadoop', 'spark', 'aws', 'etl', 'big data'],
    'Software Developer': ['java', 'python', 'c++', 'git', 'html', 'css', 'javascript'],
    'Data Scientist': ['python', 'machine learning', 'deep learning', 'statistics', 'pandas', 'numpy', 'matplotlib'],
    'Machine Engineer': ['c++', 'python', 'arduino', 'robotics', 'mechanical engineering']
}

conn = connect_db()
create_table(conn)
c = conn.cursor()

st.sidebar.title("Smart Resume Analyzer")
page = st.sidebar.selectbox("Select Option", ["Upload Resume", "View Database"])

def extract_name(text):
    name_match = re.findall(r'\b[A-Z][a-z]+(?:\s[A-Z][a-z]+)?\b', text)
    if name_match:
        unwanted = ['email', 'phone', 'contact', 'address', 'linkedin', 'github']
        for name in name_match:
            if not any(word in name.lower() for word in unwanted):
                return name
    return "Name not found"

def extract_info(text):
    name = extract_name(text)
    email = ""
    phone = ""
    skills = []

    email_match = re.findall(r'\S+@\S+', text)
    if email_match:
        email = email_match[0]

    phone_match = re.findall(r'\+?\d[\d -]{8,}\d', text)
    if phone_match:
        phone = phone_match[0]

    doc = nlp(text.lower())
    for token in doc:
        if token.is_alpha and not token.is_stop:
            for role in role_skills.values():
                if token.text in role and token.text not in skills:
                    skills.append(token.text)

    return name, email, phone, skills

def calculate_scores(skills):
    scores = {}
    for role, required_skills in role_skills.items():
        match_count = len(set(skills) & set(required_skills))
        total = len(required_skills)
        score = (match_count / total) * 100
        scores[role] = round(score, 2)
    return scores

if page == "Upload Resume":
    st.title("Upload Candidate Resume")
    uploaded_file = st.file_uploader("Upload Resume (PDF/TXT format)", type=["pdf", "txt"])

    if uploaded_file is not None:
        text = ""
        if uploaded_file.type == "application/pdf":
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text()
        else:
            text = str(uploaded_file.read(), 'utf-8')

        name, email, phone, skills = extract_info(text)
        scores = calculate_scores(skills)
        best_role = max(scores, key=scores.get)

        st.subheader("Extracted Information:")
        st.write(f"**Name:** {name}")
        st.write(f"**Email:** {email}")
        st.write(f"**Phone:** {phone}")
        st.write(f"**Skills:** {', '.join(skills)}")

        st.subheader("Role Suitability Scores:")
        for role, score in scores.items():
            st.write(f"**{role}:** {score}%")

        st.success(f"**Best Suited Role: {best_role}**")

        if st.button("Save to Database"):
            c.execute('''INSERT INTO resumes (name, email, phone, skills,
                        data_engineer_score, software_developer_score, data_scientist_score, machine_engineer_score, best_role)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)''',
                        (name, email, phone, ', '.join(skills),
                         scores['Data Engineer'], scores['Software Developer'], scores['Data Scientist'], scores['Machine Engineer'], best_role))
            conn.commit()
            st.success("Resume information saved successfully!")

elif page == "View Database":
    st.title("Database of Resumes")
    c.execute("SELECT * FROM resumes")
    data = c.fetchall()

    if data:
        c.execute("PRAGMA table_info(resumes);")
        columns_info = c.fetchall()
        column_names = [column[1] for column in columns_info]
        df = pd.DataFrame(data, columns=column_names)

        st.dataframe(df)

        st.subheader("Shortlist and Notify Candidates")

        selected_role = st.selectbox("Select Role to View Top 5 Candidates", ['Data Engineer', 'Software Developer', 'Data Scientist', 'Machine Engineer'])
        role_score_column = f"{selected_role.lower().replace(' ', '_')}_score"

        top_5_candidates = df[['name', 'email', role_score_column]].sort_values(by=role_score_column, ascending=False).head(5)
        st.write(f"**Top 5 {selected_role}s:**")
        st.dataframe(top_5_candidates)

        for idx, row in top_5_candidates.iterrows():
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**{row['name']}** - 📧 {row['email']}")
            with col2:
                if st.button(f"Shortlist {row['name']}", key=f"shortlist_{idx}"):
                    if row['email']:
                        success = send_email(row['email'], row['name'])
                        if success:
                            st.success(f"Email sent to {row['name']} at {row['email']}")
                        else:
                            st.error(f"Failed to send email to {row['name']}.")
                    else:
                        st.error(f"No email found for {row['name']}.")

        st.write("---")
        delete_name = st.selectbox("Select Resume to Delete", df["name"].values)
        if st.button(f"Delete {delete_name}"):
            c.execute("DELETE FROM resumes WHERE name=?", (delete_name,))
            conn.commit()
            st.success(f"Deleted resume with name {delete_name} successfully!")
            st.rerun()

        st.write("---")
        st.subheader("Delete Entire Database")
        confirm = st.checkbox("Confirm you want to delete ALL resumes", key="confirm_delete")

        if confirm:
            if st.button("Delete All Resumes (Dangerous)"):
                c.execute("DELETE FROM resumes;")
                conn.commit()
                st.success("All resumes deleted successfully!")
                st.rerun()

        st.write("---")
        if st.button("Download All Resumes as CSV"):
            csv = df.to_csv(index=False)
            st.download_button("Download CSV", csv, "resumes.csv", "text/csv")

        st.subheader("Data Visualizations:")

        fig1, ax1 = plt.subplots(figsize=(8, 6))
        ax1.bar(top_5_candidates['name'], top_5_candidates[role_score_column], color='blue')
        ax1.set_xlabel("Candidates")
        ax1.set_ylabel(f"{selected_role} Score")
        ax1.set_title(f"Top 5 {selected_role}s Based on Score")
        plt.xticks(rotation=45)
        st.pyplot(fig1)

        role_distribution = df['best_role'].value_counts()

        fig2, ax2 = plt.subplots(figsize=(8, 8))
        ax2.pie(role_distribution.values, labels=role_distribution.index, autopct='%1.1f%%', startangle=140, colors=plt.cm.Paired.colors)
        ax2.set_title('Distribution of Candidates by Best Role')
        ax2.axis('equal')
        st.pyplot(fig2)

        all_skills = []
        for skill_list in df['skills']:
            if isinstance(skill_list, str):
                all_skills.extend([s.strip().lower() for s in skill_list.split(',')])

        all_known_skills = [skill for skills in role_skills.values() for skill in skills]
        skill_counter = Counter(all_skills)

        missing_skills = {skill: skill_counter.get(skill, 0) for skill in all_known_skills}
        sorted_missing_skills = dict(sorted(missing_skills.items(), key=lambda item: item[1]))

        fig3, ax3 = plt.subplots(figsize=(10, 8))
        ax3.barh(list(sorted_missing_skills.keys()), list(sorted_missing_skills.values()), color='red')
        ax3.set_xlabel('Number of Candidates with Skill')
        ax3.set_ylabel('Skills')
        ax3.set_title('Skill Gap Analysis (Lower means Missing Skills)')
        st.pyplot(fig3)

    else:
        st.info("No resumes in database yet.")
