from sqlalchemy import create_engine, Column, Integer, String, Text, Date
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import declarative_base, sessionmaker
import urllib.parse

user = "postgres"
password = urllib.parse.quote_plus("TheNook@Rishitha1594")
host = "db.tnogvzlpaqzzxcmplopa.supabase.co"
port = "6543"
dbname = "postgres"

DATABASE_URL = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{dbname}?sslmode=require"

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
    pool_recycle=300,
    connect_args={"connect_timeout": 30}
)

SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

class Book(Base):
    __tablename__ = "books"

    id = Column(String(100), primary_key=True)
    title = Column(String(200), nullable=False)
    author = Column(String(150))
    genre = Column(String(100))
    rating = Column(Integer)
    review = Column(Text)
    moods = Column(ARRAY(String))
    status = Column(String(20))
    start_date = Column(Date)
    finish_date = Column(Date)
