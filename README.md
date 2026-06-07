# FastAPI AI Chat Backend

Backend API for the AI Chat application built with FastAPI, PostgreSQL, JWT Authentication, and Gemini AI.

## Requirements

- Python 3.11.4
- PostgreSQL
- pip

## Project Setup

### 1. Clone the Repository

Clone repo with ssh or https

### 2. Create a Virtual Environment

#### Windows

```bash
py -3.11 -m venv venv
```

Activate:

```bash
venv\Scripts\activate
```

#### Linux / macOS

```bash
python3.11 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Create PostgreSQL Database

Connect to PostgreSQL and create a database:

```sql
CREATE DATABASE ai_chat_db;
```

### 5. Configure Environment Variables

Create a `.env` file in the project root:

```env
DATABASE_URL=

GEMINI_API_KEY=

JWT_SECRET_KEY=
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

Example:

```env
DATABASE_URL=postgresql://postgres:password@localhost:5432/ai_chat_db

GEMINI_API_KEY=your_gemini_api_key

JWT_SECRET_KEY=your_super_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=60
```

## Running the Application

Start the development server:

```bash
uvicorn app.main:app --reload
```

If your entry file is located elsewhere, adjust the module path accordingly.

Example:

```bash
uvicorn main:app --reload
```

The API will be available at:

```text
http://localhost:8000
```

## API Documentation

Swagger UI:

```text
http://localhost:8000/docs
```

ReDoc:

```text
http://localhost:8000/redoc
```

## Development Workflow

Activate virtual environment:

### Windows

```bash
venv\Scripts\activate
```

### Linux / macOS

```bash
source venv/bin/activate
```

Install new package:

```bash
pip install <package-name>
```

Update requirements:

```bash
pip freeze > requirements.txt
```

Deactivate virtual environment:

```bash
deactivate
```

## Environment Variables

| Variable           | Description                        |
| ------------------ | ---------------------------------- |
| DATABASE_URL       | PostgreSQL connection string       |
| GEMINI_API_KEY     | Google Gemini API key              |
| JWT_SECRET_KEY     | Secret key used to sign JWT tokens |
| JWT_ALGORITHM      | JWT signing algorithm              |
| JWT_EXPIRE_MINUTES | JWT expiration time in minutes     |

## Recommended Project Structure

```text
.
├── app/
│   ├── api/
│   ├── core/
│   ├── models/
│   ├── schemas/
│   ├── services/
│   └── main.py
├── requirements.txt
├── .env
├── .gitignore
└── README.md
```

## Notes

- Never commit `.env` files to source control.
- Keep `JWT_SECRET_KEY` secure and unique for each environment.
- Store production secrets using a secure secret management solution.
- Use separate databases for development, staging, and production.
