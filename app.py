import base64
import os
import pymysql
import pandas as pd
import streamlit as st
from dotenv import load_dotenv
from PIL import Image
import PyPDF2 as pdf
import google.generativeai as genai
from datetime import datetime
import time
import re
import random 
# import pafy

# def fetch_yt_video(link):
#     video = pafy.new(link)
#     return video.title
# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

# Connect to MySQL
connection = pymysql.connect(
    host='localhost',
    user='root',
    password='',
    database='sra',  # Ensure this database exists in MySQL
    port=3307,
    cursorclass=pymysql.cursors.DictCursor
)
cursor = connection.cursor()

# Create database and table
cursor.execute("CREATE DATABASE IF NOT EXISTS sra")
cursor.execute("USE sra")

DB_table_name = "user_data"
table_sql = f"""
    CREATE TABLE IF NOT EXISTS {DB_table_name} (
        ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
        Name VARCHAR(100) NOT NULL,
        Email_ID VARCHAR(50) NOT NULL,
        Resume_Score VARCHAR(8) NOT NULL,
        Timestamp VARCHAR(50) NOT NULL,
        Page_No VARCHAR(5) NOT NULL,
        Predicted_Field VARCHAR(25) NOT NULL,
        User_Level VARCHAR(30) NOT NULL,
        Actual_Skills VARCHAR(300) NOT NULL,
        Recommended_Skills VARCHAR(300) NOT NULL,
        Recommended_Courses VARCHAR(600) NOT NULL
    );
"""
cursor.execute(table_sql)
connection.commit()

# Function to get AI response
def get_gemini_response(input, pdf_content, prompt):
    model = genai.GenerativeModel('gemini-1.5-flash')
    response = model.generate_content([input, pdf_content[0], prompt])
    return response.text

# Extract text from PDF
def input_pdf_text(uploaded_file):
    reader = pdf.PdfReader(uploaded_file)
    text = "".join(page.extract_text() or "" for page in reader.pages)
    return text

# Function to show PDF inside Streamlit
def show_pdf(uploaded_file):
    base64_pdf = base64.b64encode(uploaded_file.getvalue()).decode('utf-8')
    pdf_display = f'<iframe src="data:application/pdf;base64,{base64_pdf}" width="700" height="1000" type="application/pdf"></iframe>'
    st.markdown(pdf_display, unsafe_allow_html=True)

# Insert data into MySQL
def insert_data(name, email, res_score, no_of_pages, reco_field, cand_level, skills, recommended_skills, courses):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    insert_sql = f"""
    INSERT INTO user_data (Name, Email_ID, Resume_Score, Timestamp, Page_No, 
                           Predicted_Field, User_Level, Actual_Skills, 
                           Recommended_Skills, Recommended_Courses) 
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    values = (name, email, str(res_score), timestamp, str(no_of_pages), reco_field, 
              cand_level, skills, recommended_skills, courses)
    
    cursor.execute(insert_sql, values)
    connection.commit()

# Fetch stored data
def fetch_data():
    cursor.execute("SELECT * FROM user_data")
    rows = cursor.fetchall()
    return pd.DataFrame(rows)

# Streamlit App Configuration
st.set_page_config(page_title="ATS Resume Expert")
st.header("AI Resume Screening and Ranking System")

# Display Logo
logo_path = 'Logo/resumescrore.webp'
if os.path.exists(logo_path):
    img = Image.open(logo_path).resize((300, 300))
    st.image(img)
else:
    st.warning("⚠️ Logo not found! Please check the file path.")

input_text = st.text_area("Job Description:", key="input")
uploaded_file = st.file_uploader("Upload your resume (PDF)...", type=["pdf"])

if uploaded_file:
    st.write("✅ PDF Uploaded Successfully")
    show_pdf(uploaded_file)

submit1 = st.button("Tell Me About the Resume")
submit3 = st.button("Percentage Match")
submit2 = st.button("Missing Keywords")
submit4 = st.button("Recommended Courses")
submit5 = st.button("Resume Tips")

# Input Prompts
input_prompt1 = "You are an HR expert reviewing resumes..."
input_prompt3 = "Analyze the resume and provide a match percentage..."
input_prompt2 = "Find missing keywords..."
input_prompt4 = "Suggest courses..."
input_prompt5 = "Give resume improvement tips..."

# If a resume is uploaded, extract its details
if uploaded_file:
    pdf_content = [input_pdf_text(uploaded_file)]
    no_of_pages = len(pdf.PdfReader(uploaded_file).pages)

    # Placeholder data (Modify to extract actual details)
    name = "John Doe"
    email = "johndoe@example.com"
    resume_score = "85%"  
    reco_field = "Data Science"
    cand_level = "Intermediate"
    actual_skills = "Python, SQL, ML"
    recommended_skills = "Deep Learning, NLP"
    recommended_courses = "ML Specialization by Andrew Ng"

# Button Logic
if submit1 and uploaded_file:
    response = get_gemini_response(input_prompt1, pdf_content, input_text)
    st.subheader("Resume Analysis")
    st.write(response)

elif submit3 and uploaded_file:
    response = get_gemini_response(input_prompt3, pdf_content, input_text)

    # Extract match percentage
    match = re.search(r'\d+', response)
    percentage_match = int(match.group()) if match else 0
    percentage_match = min(max(percentage_match, 0), 100)

    st.subheader("📊 ATS Percentage Match")
    st.write(f"🔍 Your Resume Matches **{percentage_match}%** with the Job Description")

    # Insert data into the database with real values
    insert_data(name, email, percentage_match, no_of_pages, reco_field, cand_level, actual_skills, recommended_skills, recommended_courses)
    st.success(f"✅ Match Score: {percentage_match}% - Data saved!")

elif submit2 and uploaded_file:
    response = get_gemini_response(input_prompt2, pdf_content, input_text)
    st.subheader("Missing Keywords")
    st.write(response)

elif submit4 and uploaded_file:
    response = get_gemini_response(input_prompt4, pdf_content, input_text)
    st.subheader("Recommended Courses")
    st.write(response)

elif submit5 and uploaded_file:
    response = get_gemini_response(input_prompt5, pdf_content, input_text)
    st.subheader("Resume Tips")
    st.write(response)

# Show Stored Data
if st.button("📂 Show Stored Data"):
    st.dataframe(fetch_data())

# # Like & Comment Section
# if "likes" not in st.session_state:
#     st.session_state.likes = 0
# if "comments" not in st.session_state:
#     st.session_state.comments = []

# col1, col2, col3 = st.columns([1, 3, 2])
# with col1:
#     if st.button("👍 Like"):
#         st.session_state.likes += 1
# with col2:
#     st.markdown(f"❤️ {st.session_state.likes} Likes", unsafe_allow_html=True)

# comment = st.text_input("💬 Add a comment...")
# if st.button("Post Comment") and comment:
#     st.session_state.comments.append(comment)
#     st.success("✅ Comment added!")

# for c in st.session_state.comments:
#     st.markdown(f"💬 **{c}**")

# Sample lists of video URLs (Replace with actual YouTube video links)
resume_videos = [
    "https://youtu.be/y3R9e2L8I9E?si=wfZCAYSf_ccHwc07"
]

interview_videos = [
    "https://youtu.be/otkpUBKqCCQ?si=GNPnYiONAyi3qSlR"
]

# Function to extract YouTube video titles (Ensure this function is defined)
def fetch_yt_video(url):
    return " How to make Ultimate Resume ? Step by step guide for Software Engineers"  # Replace this with actual YouTube title extraction logic

# Resume Writing Video
st.header("**Bonus Video for Resume Writing Tips💡**")
resume_vid = random.choice(resume_videos)  # Select a random video
res_vid_title = fetch_yt_video(resume_vid)  # Fetch title
st.subheader(f"✅ **{res_vid_title}**")
st.video(resume_vid)  # Display video

def fetch_yt_video(url):
    return " Job Interviews | 5 Super Tips to Crack Online Job Interviews "  # Replace this with actual YouTube title 
# Interview Preparation Video
st.header("**Bonus Video for Interview👨‍💼 Tips💡**")
interview_vid = random.choice(interview_videos)  # Select a random video
int_vid_title = fetch_yt_video(interview_vid)  # Fetch title
st.subheader(f"✅ **{int_vid_title}**")
st.video(interview_vid)  # Display video

# Remove unnecessary connection.commit() here
# Only use connection.commit() after database operations
