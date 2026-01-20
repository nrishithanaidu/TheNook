import os
from openai import OpenAI
from flask import Flask, request, jsonify
from flask_cors import CORS
from sqlalchemy import create_engine, Column, String, Integer
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.dialects.postgresql import ARRAY
import urllib.parse

# -------------------------
# OPENAI CLIENT
# -------------------------

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# -------------------------
# DATABASE (currently unused, kept for later)
# -------------------------

user = "postgres"
password = urllib.parse.quote_plus("TheNook@Rishitha1594")
host = "db.tnogvzlpaqzzxcmplopa.supabase.co"
port = "6543"
dbname = "postgres"

DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Book(Base):
    __tablename__ = "books"
    id = Column(String, primary_key=True)
    title = Column(String)
    genre = Column(String)
    rating = Column(Integer)
    status = Column(String)
    moods = Column(ARRAY(String))

# -------------------------
# CHATBOT APP
# -------------------------

app = Flask(__name__)
CORS(app)

@app.route("/chat", methods=["POST"])
def chat():
    data = request.json or {}
    user_message = data.get("message", "").strip()

    if not user_message:
        return jsonify({"reply": "Say something."})

    response = client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {"role": "system", "content": "You are Nook, a thoughtful media companion."},
            {"role": "user", "content": user_message}
        ]
    )

    reply = response.choices[0].message.content
    return jsonify({"reply": reply})

if __name__ == "__main__":
    app.run(port=6000, debug=True)
