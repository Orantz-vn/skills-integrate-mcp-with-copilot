"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=current_dir / "static"), name="static")

TEACHERS_FILE = Path(os.environ.get("TEACHERS_FILE", current_dir / "teachers.json"))
SESSION_SECRET = os.environ.get("SESSION_SECRET")
if SESSION_SECRET:
    SESSION_SECRET = SESSION_SECRET.encode("utf-8")
else:
    SESSION_SECRET = secrets.token_bytes(32)
SESSION_COOKIE = "teacher_session"
SESSION_DURATION = 8 * 60 * 60
PASSWORD_HASH_ITERATIONS = 600_000


class LoginRequest(BaseModel):
    username: str
    password: str


def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    password_hash = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS
    )
    return f"pbkdf2_sha256${PASSWORD_HASH_ITERATIONS}${salt.hex()}${password_hash.hex()}"


def verify_password(password: str, encoded_hash: str) -> bool:
    if not isinstance(encoded_hash, str):
        return False
    try:
        algorithm, iterations, salt, expected_hash = encoded_hash.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual_hash = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), bytes.fromhex(salt), int(iterations)
        )
        return hmac.compare_digest(actual_hash.hex(), expected_hash)
    except (ValueError, TypeError):
        return False


def create_session(username: str) -> str:
    payload = base64.urlsafe_b64encode(
        json.dumps(
            {"username": username, "expires": int(time.time()) + SESSION_DURATION}
        ).encode("utf-8")
    ).decode("ascii").rstrip("=")
    signature = hmac.new(SESSION_SECRET, payload.encode("ascii"), hashlib.sha256)
    return f"{payload}.{signature.hexdigest()}"


def get_session_username(token: str | None) -> str | None:
    if not token:
        return None
    try:
        payload, signature = token.rsplit(".", 1)
        expected_signature = hmac.new(
            SESSION_SECRET, payload.encode("ascii"), hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(signature, expected_signature):
            return None
        session = json.loads(
            base64.urlsafe_b64decode(payload + "=" * (-len(payload) % 4))
        )
        if session["expires"] <= time.time():
            return None
        return session["username"]
    except (ValueError, KeyError, TypeError, json.JSONDecodeError):
        return None


def require_teacher(request: Request) -> str:
    username = get_session_username(request.cookies.get(SESSION_COOKIE))
    if username is None:
        raise HTTPException(status_code=401, detail="Teacher login required")
    return username


@app.post("/auth/login")
def login(credentials: LoginRequest, request: Request, response: Response):
    try:
        teachers = json.loads(TEACHERS_FILE.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise HTTPException(
            status_code=503,
            detail="Teacher credentials are not configured. See src/README.md.",
        ) from error
    except (OSError, json.JSONDecodeError) as error:
        raise HTTPException(
            status_code=500, detail="Teacher credentials could not be loaded"
        ) from error

    if not isinstance(teachers, dict):
        raise HTTPException(
            status_code=500, detail="Teacher credentials file must contain an object"
        )
    teacher = teachers.get(credentials.username)
    if not isinstance(teacher, dict) or not verify_password(
        credentials.password, teacher.get("password_hash", "")
    ):
        raise HTTPException(status_code=401, detail="Invalid username or password")

    response.set_cookie(
        key=SESSION_COOKIE,
        value=create_session(credentials.username),
        max_age=SESSION_DURATION,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        path="/",
    )
    return {"username": credentials.username}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie(
        key=SESSION_COOKIE, httponly=True, samesite="strict", path="/"
    )
    return {"message": "Logged out"}


@app.get("/auth/session")
def get_auth_session(request: Request):
    username = get_session_username(request.cookies.get(SESSION_COOKIE))
    if username is None:
        return {"authenticated": False}
    return {"authenticated": True, "username": username}

# In-memory activity database
activities = {
    "Chess Club": {
        "description": "Learn strategies and compete in chess tournaments",
        "schedule": "Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 12,
        "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
    },
    "Programming Class": {
        "description": "Learn programming fundamentals and build software projects",
        "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
        "max_participants": 20,
        "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
    },
    "Gym Class": {
        "description": "Physical education and sports activities",
        "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
        "max_participants": 30,
        "participants": ["john@mergington.edu", "olivia@mergington.edu"]
    },
    "Soccer Team": {
        "description": "Join the school soccer team and compete in matches",
        "schedule": "Tuesdays and Thursdays, 4:00 PM - 5:30 PM",
        "max_participants": 22,
        "participants": ["liam@mergington.edu", "noah@mergington.edu"]
    },
    "Basketball Team": {
        "description": "Practice and play basketball with the school team",
        "schedule": "Wednesdays and Fridays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["ava@mergington.edu", "mia@mergington.edu"]
    },
    "Art Club": {
        "description": "Explore your creativity through painting and drawing",
        "schedule": "Thursdays, 3:30 PM - 5:00 PM",
        "max_participants": 15,
        "participants": ["amelia@mergington.edu", "harper@mergington.edu"]
    },
    "Drama Club": {
        "description": "Act, direct, and produce plays and performances",
        "schedule": "Mondays and Wednesdays, 4:00 PM - 5:30 PM",
        "max_participants": 20,
        "participants": ["ella@mergington.edu", "scarlett@mergington.edu"]
    },
    "Math Club": {
        "description": "Solve challenging problems and participate in math competitions",
        "schedule": "Tuesdays, 3:30 PM - 4:30 PM",
        "max_participants": 10,
        "participants": ["james@mergington.edu", "benjamin@mergington.edu"]
    },
    "Debate Team": {
        "description": "Develop public speaking and argumentation skills",
        "schedule": "Fridays, 4:00 PM - 5:30 PM",
        "max_participants": 12,
        "participants": ["charlotte@mergington.edu", "henry@mergington.edu"]
    }
}


@app.get("/")
def root():
    return RedirectResponse(url="/static/index.html")


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(activity_name: str, email: str, _: str = Depends(require_teacher)):
    """Sign up a student for an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is not already signed up
    if email in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is already signed up"
        )

    # Add student
    activity["participants"].append(email)
    return {"message": f"Signed up {email} for {activity_name}"}


@app.delete("/activities/{activity_name}/unregister")
def unregister_from_activity(
    activity_name: str, email: str, _: str = Depends(require_teacher)
):
    """Unregister a student from an activity"""
    # Validate activity exists
    if activity_name not in activities:
        raise HTTPException(status_code=404, detail="Activity not found")

    # Get the specific activity
    activity = activities[activity_name]

    # Validate student is signed up
    if email not in activity["participants"]:
        raise HTTPException(
            status_code=400,
            detail="Student is not signed up for this activity"
        )

    # Remove student
    activity["participants"].remove(email)
    return {"message": f"Unregistered {email} from {activity_name}"}
