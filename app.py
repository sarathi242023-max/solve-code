from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import subprocess
import tempfile
import os
import uuid

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change-this-secret-key")

problems = {
    "python": [
        {"id": 1, "title": "Hello World", "difficulty": "Easy",
         "description": "Write a Python program to print Hello World.",
         "input": "No input", "output": "Hello World",
         "starter": 'print("Hello World")'},
        {"id": 2, "title": "Add Two Numbers", "difficulty": "Easy",
         "description": "Read two integers and print their sum.",
         "input": "10 20", "output": "30",
         "starter": 'a, b = map(int, input().split())\nprint(a + b)'},
        {"id": 3, "title": "Even or Odd", "difficulty": "Easy",
         "description": "Check whether a given number is even or odd.",
         "input": "24", "output": "Even",
         "starter": 'n = int(input())\nif n % 2 == 0:\n    print("Even")\nelse:\n    print("Odd")'}
    ],
    "c": [
        {"id": 1, "title": "Hello World", "difficulty": "Easy",
         "description": "Write a C program to print Hello World.",
         "input": "No input", "output": "Hello World",
         "starter": '#include <stdio.h>\n\nint main() {\n    printf("Hello World");\n    return 0;\n}'},
        {"id": 2, "title": "Add Two Numbers", "difficulty": "Easy",
         "description": "Read two integers and print their sum.",
         "input": "10 20", "output": "30",
         "starter": '#include <stdio.h>\n\nint main() {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    printf("%d", a + b);\n    return 0;\n}'},
        {"id": 3, "title": "Biggest Number", "difficulty": "Easy",
         "description": "Find the biggest of two numbers.",
         "input": "20 40", "output": "40",
         "starter": '#include <stdio.h>\n\nint main() {\n    int a, b;\n    scanf("%d %d", &a, &b);\n    if (a > b) printf("%d", a);\n    else printf("%d", b);\n    return 0;\n}'}
    ],
    "cpp": [
        {"id": 1, "title": "Hello World", "difficulty": "Easy",
         "description": "Write a C++ program to print Hello World.",
         "input": "No input", "output": "Hello World",
         "starter": '#include <iostream>\nusing namespace std;\n\nint main() {\n    cout << "Hello World";\n    return 0;\n}'},
        {"id": 2, "title": "Add Two Numbers", "difficulty": "Easy",
         "description": "Read two integers and print their sum.",
         "input": "10 20", "output": "30",
         "starter": '#include <iostream>\nusing namespace std;\n\nint main() {\n    int a, b;\n    cin >> a >> b;\n    cout << a + b;\n    return 0;\n}'},
        {"id": 3, "title": "Even or Odd", "difficulty": "Easy",
         "description": "Check whether a number is even or odd.",
         "input": "24", "output": "Even",
         "starter": '#include <iostream>\nusing namespace std;\n\nint main() {\n    int n;\n    cin >> n;\n    if (n % 2 == 0) cout << "Even";\n    else cout << "Odd";\n    return 0;\n}'}
    ]
}

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login")
def login():
    return render_template("login.html")

@app.route("/signup")
def signup():
    return render_template("signup.html")

@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))
    return render_template("dashboard.html", problems=problems)

@app.route("/problem/<language>/<int:problem_id>")
def problem(language, problem_id):
    if language not in problems:
        return "Language not found", 404
    selected = next((p for p in problems[language] if p["id"] == problem_id), None)
    if not selected:
        return "Problem not found", 404
    return render_template("problem.html", language=language, problem=selected)

@app.route("/api/login", methods=["POST"])
def api_login():
    data = request.get_json(silent=True) or {}
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not email or not password:
        return jsonify(success=False, message="Email and password are required."), 400
    session["user"] = email
    return jsonify(success=True, redirect="/dashboard")

@app.route("/api/signup", methods=["POST"])
def api_signup():
    data = request.get_json(silent=True) or {}
    name = data.get("name", "").strip()
    email = data.get("email", "").strip()
    password = data.get("password", "")
    if not name or not email or not password:
        return jsonify(success=False, message="All fields are required."), 400
    session["user"] = email
    return jsonify(success=True, redirect="/dashboard")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("home"))

@app.route("/api/problems/<language>")
def get_problems(language):
    if language not in problems:
        return jsonify(success=False, message="Language not found"), 404
    return jsonify(success=True, problems=problems[language])

@app.route("/api/run", methods=["POST"])
def run_code():
    data = request.get_json(silent=True) or {}
    language = data.get("language")
    code = data.get("code")
    user_input = data.get("input", "")

    if not language or not code:
        return jsonify(success=False, output="Language and code are required."), 400

    filename = None
    executable = None
    try:
        ext = {"python": ".py", "c": ".c", "cpp": ".cpp"}.get(language)
        if not ext:
            return jsonify(success=False, output="Unsupported language."), 400

        filename = os.path.join(tempfile.gettempdir(), f"solve_code_{uuid.uuid4()}{ext}")
        with open(filename, "w", encoding="utf-8") as f:
            f.write(code)

        if language == "python":
            cmd = ["python", filename]
        else:
            compiler = "gcc" if language == "c" else "g++"
            executable = filename.rsplit(".", 1)[0]
            compile_result = subprocess.run(
                [compiler, filename, "-o", executable],
                capture_output=True, text=True, timeout=5
            )
            if compile_result.returncode != 0:
                return jsonify(success=False, output=compile_result.stderr)
            cmd = [executable]

        result = subprocess.run(
            cmd, input=user_input, text=True,
            capture_output=True, timeout=5
        )
        output = result.stdout
        if result.stderr:
            output += ("\n" if output else "") + result.stderr
        return jsonify(success=result.returncode == 0, output=output or "No output")
    except subprocess.TimeoutExpired:
        return jsonify(success=False, output="Program execution timed out.")
    except FileNotFoundError:
        return jsonify(success=False, output="Required compiler/runtime is not installed on this computer.")
    except Exception as exc:
        return jsonify(success=False, output=str(exc))
    finally:
        for path in (filename, executable):
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
