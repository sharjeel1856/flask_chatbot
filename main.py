from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify
import pandas as pd
from difflib import get_close_matches
import json
import os

app = Flask(__name__)

# Load secret key from environment variable (with fallback for dev)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_dev_secret_key")

# Dataset path
DATASET_PATH = "DATASET_CLEANED.xlsx"

# JSON file for persisting unread messages count
UNREAD_FILE = "unread_messages.json"

# Labels & domain mapping
labels = {
    "Admission": "Dr Gohar",
    "Scholarship": "Dr Naeem",
    "Student Affairs": "Sir Sibtual Hassan",
    "Academics": "Teacher Kinza",
    "Migration": "Dr Asim Zeb"
}

sheets = ["Sheet1", "Sheet2", "Sheet3"]

# Load QA data from all sheets into qa_dict
qa_dict = {}
for sheet in sheets:
    df = pd.read_excel(DATASET_PATH, sheet_name=sheet, usecols=[0, 1], header=None, dtype=str)
    df.dropna(inplace=True)
    df = df[df[0].str.strip() != ""]
    df.columns = ["Question", "Answer"]
    qa_dict.update(dict(zip(df["Question"], df["Answer"])))

# Load unread messages from JSON or initialize
if os.path.exists(UNREAD_FILE):
    with open(UNREAD_FILE, "r") as f:
        unread_messages = json.load(f)
else:
    unread_messages = {teacher: 0 for teacher in labels.values()}

def save_unread_messages():
    with open(UNREAD_FILE, "w") as f:
        json.dump(unread_messages, f)

common_responses = {
    "hi": "Hello! How can I assist you today?",
    "hello": "Hi there! What can I do for you?",
    "hey": "Hey! How can I help you?",
    "good morning": "Good morning! How can I assist you today?",
    "good afternoon": "Good afternoon! What can I do for you?",
    "good evening": "Good evening! How can I help you?",
    "bye": "Goodbye! Have a great day!",
    "goodbye": "See you later! Take care!",
    "thank you": "You're welcome!",
    "thanks": "You're welcome!",
    "welcome": "Thank you! How can I assist you further?",
    "how are you": "I'm just a bot, but I'm here to help you! How can I assist you today?",
    "what's up": "Not much, just here to help you! What can I do for you?"
}

domain_keywords = {
    "Admission": ["admission", "admit", "apply", "form", "test", "document", "verification", "eligibility", "deadline"],
    "Scholarship": ["scholarship", "financial aid", "grant", "funding", "tuition", "discount", "fee waiver"],
    "Student Affairs": ["event", "club", "extracurricular", "activity", "engagement", "student life", "hostel", "facility"],
    "Academics": ["exam", "course", "grade", "attendance", "syllabus", "result", "academic", "lecture", "assignment"],
    "Migration": ["migration", "transfer", "relocation", "visa", "immigration", "international", "abroad"]
}

def get_answer_from_dataset(question):
    matches = get_close_matches(question, qa_dict.keys(), n=1, cutoff=0.6)
    if matches:
        return qa_dict[matches[0]]
    return None

def classify_query(query):
    query = query.lower()
    domain_match_counts = {domain: 0 for domain in domain_keywords.keys()}
    
    for domain, keywords in domain_keywords.items():
        for keyword in keywords:
            if keyword in query:
                domain_match_counts[domain] += 1
    
    max_matches = max(domain_match_counts.values())
    if max_matches > 0:
        best_domain = [domain for domain, count in domain_match_counts.items() if count == max_matches][0]
        teacher = labels[best_domain]
        return best_domain, teacher
    
    # Default domain and teacher
    teacher = labels["Student Affairs"]
    return "Student Affairs", teacher

@app.route("/", methods=["GET", "POST"])
def home():
    chatbot_response = session.get("bot_response", "")
    if request.method == "POST":
        question = request.form.get("student_query", "").strip().lower()
        
        if question in common_responses:
            chatbot_response = common_responses[question]
        else:
            answer = get_answer_from_dataset(question)
            if answer:
                chatbot_response = answer
            else:
                domain, teacher = classify_query(question)
                session['unanswered_question'] = question
                session['assigned_teacher'] = teacher
                # Increment unread count & save
                unread_messages[teacher] = unread_messages.get(teacher, 0) + 1
                save_unread_messages()
                return redirect(url_for("teacher_input"))
        session["bot_response"] = chatbot_response
    return render_template_string(chatbot_template, chatbot_response=chatbot_response)

chatbot_template = """
<!DOCTYPE html>
<html>
<head>
    <title>AUST Guidance Chatbot</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .chat-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 400px;
            padding: 20px;
        }
        h2 {
            text-align: center;
            color: #333;
        }
        form {
            display: flex;
            flex-direction: column;
        }
        input[type="text"] {
            padding: 10px;
            margin-bottom: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
        }
        button {
            padding: 10px;
            background-color: #007bff;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 16px;
        }
        button:hover {
            background-color: #0056b3;
        }
        .response {
            margin-top: 20px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <h2>AUST Guidance Bot</h2>
        <form method="POST">
            <input type="text" name="student_query" placeholder="Ask a question...">
            <button type="submit">Ask</button>
        </form>
        <div class="response">
            <p>{{ chatbot_response }}</p>
        </div>
    </div>
</body>
</html>
"""

teacher_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Teacher Assistant</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            background-color: #f4f4f9;
            margin: 0;
            padding: 0;
            display: flex;
            justify-content: center;
            align-items: center;
            height: 100vh;
        }
        .teacher-container {
            background: white;
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
            width: 500px;
            padding: 20px;
        }
        h3 {
            text-align: center;
            color: #333;
        }
        .teacher-list {
            display: flex;
            flex-wrap: wrap;
            gap: 10px;
            justify-content: center;
            margin-bottom: 20px;
        }
        .teacher-list button {
            padding: 10px 20px;
            background-color: #28a745;
            color: white;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            font-size: 14px;
        }
        .teacher-list button:hover {
            background-color: #218838;
        }
        .unread {
            background: red;
            color: white;
            padding: 3px 7px;
            border-radius: 50%;
            font-size: 12px;
            margin-left: 5px;
        }
        textarea {
            width: 100%;
            padding: 10px;
            border: 1px solid #ccc;
            border-radius: 5px;
            font-size: 16px;
            margin-bottom: 10px;
        }
        .response {
            margin-top: 20px;
            padding: 10px;
            background-color: #e9ecef;
            border-radius: 5px;
            color: #333;
        }
    </style>
</head>
<body>
    <div class="teacher-container">
        <h3>Teachers</h3>
        <div class="teacher-list">
            {% for teacher, count in unread.items() %}
                <button onclick="selectTeacher('{{ teacher }}')">{{ teacher }}
                    {% if count > 0 %}
                        <span class="unread">{{ count }}</span>
                    {% endif %}
                </button>
            {% endfor %}
        </div>
        
        {% if assigned_teacher %}
            <h4>Answer for: {{ assigned_teacher }}</h4>
            <p><strong>Question:</strong> {{ question }}</p>
            <form method="POST">
                <textarea name="teacher_response" placeholder="Write your answer here..." required></textarea>
                <button type="submit">Submit</button>
            </form>
        {% else %}
            <p>Select a teacher above to see unanswered questions.</p>
        {% endif %}
        
        {% if bot_response %}
            <div class="response">
                <strong>Bot will say:</strong> <p>{{ bot_response }}</p>
            </div>
        {% endif %}
    </div>
<script>
function selectTeacher(teacher) {
    window.location.href = '/teacher?teacher=' + encodeURIComponent(teacher);
}
</script>
</body>
</html>
"""

@app.route("/teacher", methods=["GET", "POST"])
def teacher_input():
    assigned_teacher = session.get("assigned_teacher")
    question = session.get("unanswered_question")
    bot_response = session.get("bot_response", "")

    if request.method == "POST":
        response = request.form.get("teacher_response", "").strip()
        if response and assigned_teacher and question:
            # Load existing sheet data
            df_existing = pd.read_excel(DATASET_PATH, sheet_name="Sheet1", header=None, dtype=str)
            df_existing.columns = ["Question", "Answer"]
            # Append new entry
            new_entry = pd.DataFrame({"Question": [question], "Answer": [response]})
            new_df = pd.concat([df_existing, new_entry], ignore_index=True)
            # Write full data back
            with pd.ExcelWriter(DATASET_PATH, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
                new_df.to_excel(writer, sheet_name="Sheet1", index=False, header=False)
            # Update in-memory dictionary
            qa_dict[question] = response
            # Reset unread count & save
            unread_messages[assigned_teacher] = 0
            save_unread_messages()
            # Clear session and redirect to home
            session.pop('unanswered_question', None)
            session.pop('assigned_teacher', None)
            session["bot_response"] = response
            return redirect(url_for("home"))

    # For GET request, optionally get teacher param from URL to show question assigned to that teacher
    selected_teacher = request.args.get("teacher")
    # Show assigned question only if teacher matches
    if selected_teacher and unread_messages.get(selected_teacher, 0) > 0:
        # Find unanswered question assigned to that teacher in session or elsewhere
        # For simplicity, showing session question only if matches
        if selected_teacher == assigned_teacher and question:
            assigned_teacher = selected_teacher
        else:
            assigned_teacher = None
            question = None
    else:
        # If no selection, clear assigned question to avoid confusion
        assigned_teacher = None
        question = None

    return render_template_string(
        teacher_template,
        unread=unread_messages,
        assigned_teacher=assigned_teacher,
        question=question,
        bot_response=bot_response
    )

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=False)

