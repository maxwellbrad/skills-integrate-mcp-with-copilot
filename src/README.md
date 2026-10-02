# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Sign in as a student or staff member
- Students can manage only their own activity registrations
- Staff can manage registrations for students

## Configure Accounts

Set a persistent session-signing secret and choose a private account file before starting the server:

```sh
export AUTH_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export AUTH_USERS_FILE="$PWD/src/users.json"
```

Create student and staff accounts. The command prompts for each password and stores only a salted PBKDF2-HMAC hash:

```sh
python -m src.manage_users --email student@mergington.edu --role student
python -m src.manage_users --email staff@mergington.edu --role staff
```

For HTTPS deployments, also set `AUTH_COOKIE_SECURE=true`. Account records are stored in `src/users.json` by default; that file is ignored by Git. Do not commit account files or share the session secret.

## Getting Started

1. Install the dependencies:

   ```
   pip install -r requirements.txt
   ```

2. Run the application:

   ```
   uvicorn src.app:app --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                      | Sign in and receive an HTTP-only session cookie                     |
| POST   | `/auth/logout`                                                     | End the current session                                             |
| GET    | `/auth/me`                                                         | Get the signed-in account                                           |
| POST   | `/activities/{activity_name}/signup`                              | Sign up as the current student; staff may supply `?email=...`        |
| DELETE | `/activities/{activity_name}/unregister`                          | Unregister yourself; staff may supply `?email=...`                   |

## Data Model

The application uses a simple data model with meaningful identifiers:

1. **Activities** - Uses activity name as identifier:

   - Description
   - Schedule
   - Maximum number of participants allowed
   - List of student emails who are signed up

2. **Students** - Uses email as identifier:
   - Name
   - Grade level

Activity and registration data is stored in memory and resets on restart. Accounts are stored separately in the configured JSON file.

Run the API tests with:

```sh
python -m unittest discover -s tests
```
