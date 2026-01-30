from fastapi import FastAPI, Depends
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from BACKEND.latest_water_api import get_latest_water_snapshot
from BACKEND.search_data_engine import get_district_stats
from BACKEND.analysis_engine import get_analysis
from BACKEND.prediction_engine import get_prediction

import joblib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODEL_PATH = os.path.join(BASE_DIR, "MODELS", "recharge_rf_model.pkl")
MODEL_PATH = os.path.abspath(MODEL_PATH)
recharge_model = joblib.load(MODEL_PATH)


DATABASE_URL = "sqlite:///./users.db"

engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False}
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

class User(Base):

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, index=True)
    password = Column(String, nullable=False)
    user_role = Column(String, default="citizen")



def force_all_users_citizen():
    db = SessionLocal()
    db.query(User).update({User.user_role: "citizen"})
    db.commit()
    db.close()

Base.metadata.create_all(bind=engine)
force_all_users_citizen()

app = FastAPI()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()



@app.post("/register")
def register(name: str, email: str, password: str, db: Session = Depends(get_db)):

    existing_user = db.query(User).filter(User.email == email).first()

    if existing_user:
        return {"status": "fail", "message": "Email already exists"}

    user = User(
        name=name,
        email=email,
        password=password,
        user_role="citizen"
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return {"status": "success"}


@app.get("/email_present")
def email_present(email: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if user:
        return {"present": True}

    return {"present": False}


@app.post("/login")
def login(email: str, password: str, db: Session = Depends(get_db)):

    user = db.query(User).filter(User.email == email).first()

    if not user:
        return {"status": "fail"}

    if password!=user.password:
        return {"status": "fail"}

    return {
        "status": "success",
        "name": user.name,
        "email": user.email
    }


@app.get("/")
def root():
    return {"server": "running"}


@app.get("/all_users")
def get_all_users(db: Session = Depends(get_db)):
    users = db.query(User).all()

    data = []

    for u in users:
        data.append({
            "name": u.name,
            "email": u.email,
            "user_role": u.user_role
        })

    return data


@app.get("/latest_water_map_data")
def latest_water_map_data():
    return get_latest_water_snapshot()


@app.get("/district_stats")
def district_stats(state: str, district: str):
    return get_district_stats(state, district)

@app.get("/analysis_data")
def analysis(state: str, district: str):
    return get_analysis(state, district)

@app.get("/predict")
def predict(state: str, district: str, date: str):

    result = get_prediction(state, district, date)

    if not result:
        return {
            "status": "no_data"
        }

    recharge = recharge_model.predict([[result["predicted_wl"]]])[0]

    return {
        "status": "ok",
        "predicted_wl": result["predicted_wl"],
        "predicted_recharge": round(float(recharge), 2),
        "weekly_chart": {
            "history": result["history"],
            "prediction": result["prediction"]
        }
    }
