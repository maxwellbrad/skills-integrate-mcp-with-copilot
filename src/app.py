"""
High School Management System API

A super simple FastAPI application that allows students to view and sign up
for extracurricular activities at Mergington High School.
"""

from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
import os
from pathlib import Path
from .auth import (
    SESSION_TTL_SECONDS,
    decode_session_token,
    encode_session_token,
    load_users,
    verify_password,
)

app = FastAPI(title="Mergington High School API",
              description="API for viewing and signing up for extracurricular activities")

# Mount the static files directory
current_dir = Path(__file__).parent
app.mount("/static", StaticFiles(directory=os.path.join(Path(__file__).parent,
          "static")), name="static")


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user(request: Request) -> dict[str, str]:
    email = decode_session_token(request.cookies.get("session", ""))
    account = load_users().get(email or "")
    if not account:
        raise HTTPException(status_code=401, detail="Please sign in")
    return {"email": email, "role": account["role"]}


def cookie_is_secure() -> bool:
    return os.environ.get("AUTH_COOKIE_SECURE", "false").lower() == "true"

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


@app.post("/auth/login")
def login(credentials: LoginRequest, response: Response):
    email = credentials.email.strip().lower()
    account = load_users().get(email)
    if not account or not verify_password(credentials.password, account["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")

    response.set_cookie(
        "session",
        encode_session_token(email),
        max_age=SESSION_TTL_SECONDS,
        httponly=True,
        secure=cookie_is_secure(),
        samesite="lax",
    )
    return {"email": email, "role": account["role"]}


@app.post("/auth/logout")
def logout(response: Response):
    response.delete_cookie("session", httponly=True, samesite="lax", secure=cookie_is_secure())
    return {"message": "Signed out"}


@app.get("/auth/me")
def current_user(user: dict[str, str] = Depends(get_current_user)):
    return user


@app.get("/activities")
def get_activities():
    return activities


@app.post("/activities/{activity_name}/signup")
def signup_for_activity(
    activity_name: str,
    email: str | None = None,
    user: dict[str, str] = Depends(get_current_user),
):
    """Sign up a student for an activity"""
    if user["role"] == "student":
        if email and email.strip().lower() != user["email"]:
            raise HTTPException(status_code=403, detail="Students can only sign themselves up")
        email = user["email"]
    elif not email or not email.strip():
        raise HTTPException(status_code=422, detail="Staff must provide a student email")
    else:
        email = email.strip().lower()

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
    activity_name: str,
    email: str | None = None,
    user: dict[str, str] = Depends(get_current_user),
):
    """Unregister a student from an activity"""
    if user["role"] == "student":
        if email and email.strip().lower() != user["email"]:
            raise HTTPException(status_code=403, detail="Students can only unregister themselves")
        email = user["email"]
    elif not email or not email.strip():
        raise HTTPException(status_code=422, detail="Staff must provide a student email")
    else:
        email = email.strip().lower()

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
