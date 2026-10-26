# Mergington High School Activities API

A super simple FastAPI application that allows students to view and sign up for extracurricular activities.

## Features

- View all available extracurricular activities
- Teacher login and logout
- Only authenticated teachers can register or unregister students

## Getting Started

1. Install the dependencies:

   ```
   pip install fastapi uvicorn
   ```

2. Run the application:

   ```
   uvicorn app:app --app-dir src --reload
   ```

3. Open your browser and go to:
   - API documentation: http://localhost:8000/docs
   - Alternative documentation: http://localhost:8000/redoc

## API Endpoints

| Method | Endpoint                                                          | Description                                                         |
| ------ | ----------------------------------------------------------------- | ------------------------------------------------------------------- |
| GET    | `/activities`                                                     | Get all activities with their details and current participant count |
| POST   | `/auth/login`                                                     | Log in as a teacher                                                 |
| GET    | `/auth/session`                                                   | Check the current teacher session                                   |
| POST   | `/auth/logout`                                                    | Log out the current teacher                                         |
| POST   | `/activities/{activity_name}/signup?email=student@mergington.edu` | Register a student (teachers only)                                  |
| DELETE | `/activities/{activity_name}/unregister?email=student@mergington.edu` | Unregister a student (teachers only)                              |

## Teacher accounts

Create a teacher account interactively; the password is stored as a salted
PBKDF2 hash in `src/teachers.json`, which is excluded from version control:

```sh
python src/create_teacher.py
```

The login session expires after eight hours. Set `SESSION_SECRET` to a stable,
random secret in the server environment to keep sessions valid across restarts.
Without it, a fresh secret is generated each time the server starts.

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

Activity data is stored in memory and resets when the server restarts.
