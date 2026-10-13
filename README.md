# Database Lab 2 Part II — Login + Personal Todo List (Python/Flask)

## Team
- Student 1 name: عمر محمد عبدالله ابوالنجا
- Student 1 ID: 2404155
- Who did what: completed the project individually.

## Technology
- Python
- Flask
- MySQL
- mysql-connector-python
- bcrypt
- HTML/CSS/JavaScript
- Plain SQL (no ORM)

The lab allows students to choose their language/framework. This version uses Python + Flask.

## 1. Install Python
Install Python 3.11+ and make sure `python --version` works in the terminal.

## 2. Create a virtual environment (recommended)
Windows PowerShell:
```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks activation, you can still install packages with:
```powershell
python -m pip install -r requirements.txt
```

## 3. Install packages
```powershell
python -m pip install -r requirements.txt
```

## 4. Create the database
Open MySQL Workbench and run:
`database/schema.sql`

This creates:
- database `registration`
- table `users`
- table `todos`

## 5. Create .env
Copy `.env.example` to `.env` and put your own MySQL password in `DB_PASSWORD`.
Do not commit `.env`.

Example:
```text
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=YOUR_MYSQL_PASSWORD
DB_NAME=registration
SECRET_KEY=YOUR_LONG_RANDOM_SECRET
PORT=5000
```

## 6. Run
```powershell
python app.py
```

Open:
`http://localhost:5000`

## Required features R1-R10
- R1 Register with name, email, password, confirm password; duplicate email message.
- R2 Login/logout; invalid credentials message.
- R3 Private todo list; only logged-in user's todos, newest first.
- R4 Add todo.
- R5 Edit todo title.
- R6 Mark done/undone.
- R7 Delete with confirmation.
- R8 Browser/server validation using the exact lab messages.
- R9 bcrypt password hashing, parameterized SQL, user_id from session.
- R10 Responsive UI, feedback, empty state, name/logout.

## Required SQL
The application uses the lab's required SQL patterns with MySQL `%s` placeholders:
- Signup: INSERT INTO users (email, name, password_hash) VALUES (%s, %s, %s)
- Login: SELECT user_id, name, password_hash FROM users WHERE email = %s
- Show list: SELECT todo_id, title, is_done, created_at FROM todos WHERE user_id = %s ORDER BY todo_id DESC
- Add: INSERT INTO todos (user_id, title) VALUES (%s, %s)
- Edit: UPDATE todos SET title = %s WHERE todo_id = %s AND user_id = %s
- Mark done: UPDATE todos SET is_done = %s WHERE todo_id = %s AND user_id = %s
- Delete: DELETE FROM todos WHERE todo_id = %s AND user_id = %s

## Answers
### (a) Why UPDATE/DELETE have AND user_id?
The todo id comes from the browser. Adding `AND user_id = session_user_id` ensures a logged-in user can only change/delete their own todo. If removed, knowing another todo_id could allow changing/deleting someone else's todo.

### (b) What happens with a nonexistent user_id?
The foreign key rejects the insert because `todos.user_id` must reference an existing `users.user_id`.

### (c) Why hash instead of storing password?
A password hash is designed to verify the password without storing the original password in the database. This reduces the damage if the database is exposed.

### (d) Why check empty name if NOT NULL exists?
`NOT NULL` rejects SQL NULL, but an empty string `''` is still a non-NULL value. The application must therefore validate empty input itself.

## Screenshots

1. Register validation errors
![alt text](<screenshots/Screenshot 2026-10-13 033026.png>)
2. Login page
![alt text](<screenshots/Screenshot 2026-10-13 033104.png>)
3. Todo list with multiple todos and one completed
![alt text](<screenshots/Screenshot 2026-10-13 033234.png>)
4. Responsive phone-sized view
![alt text](<screenshots/Screenshot 2026-10-13 033410.png>)

## GitHub checklist
- README.md completed with names/IDs/contributions.
- database/schema.sql included.
- .env ignored and not uploaded.
- .env.example contains fake values only.
- Four screenshots added.
- Explain the code as a team before submission.
