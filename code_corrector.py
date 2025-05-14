import sqlite3
import time
from tkinter import *

# === DATABASE SETUP ===
DB_PATH = "code_history.db"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS code_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_code TEXT,
            corrected_code TEXT,
            error_message TEXT,
            correction_reason TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

# === ERROR EXPLANATIONS ===
ERROR_EXPLANATIONS = {
    "NameError": "You used a variable that was never defined.",
    "SyntaxError": "There is a syntax issue in your code.",
    "IndentationError": "There is a problem with the code indentation.",
    "TypeError": "You're using the wrong data type or operation.",
    "ZeroDivisionError": "You tried to divide by zero.",
    "AttributeError": "You're trying to access an attribute that doesn't exist.",
    "IndexError": "You're trying to access an invalid index in a list or string."
}

# === AUTO FIXER ===
def auto_fix_code(code):
    import re

    lines = code.split('\n')
    fixed_lines = []

    for line in lines:
        line = line.rstrip()

        # Attempt to fix missing quotes
        quote_count = line.count('"') + line.count("'")
        if quote_count % 2 != 0:
            # Try to detect which quote type was started and auto-close it
            if '"' in line:
                line += '"'
            elif "'" in line:
                line += "'"

        # Add missing parentheses to print if needed
        if line.strip().startswith("print") and not line.strip().endswith(")"):
            match = re.match(r'print\s+(.*)', line)
            if match:
                content = match.group(1).strip()
                line = f"print({content})"

        # Fix assignment in conditions
        if "if " in line and "=" in line and "==" not in line:
            line = line.replace("=", "==")

        fixed_lines.append(line)
    return '\n'.join(fixed_lines)





# === CODE RUNNER ===
def run_code(code):
    try:
        exec(code, {})
        return None  # no error
    except Exception as e:
        return str(e), e.__class__.__name__

# === SAVE TO DB ===
def save_history(original, corrected, error_msg, reason):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        INSERT INTO code_history (original_code, corrected_code, error_message, correction_reason, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (original, corrected, error_msg, reason, time.ctime()))
    conn.commit()
    conn.close()

# === GUI ===
def launch_gui():
    def correct_and_explain():
        original_code = code_input.get("1.0", END).strip()
        corrected_code = auto_fix_code(original_code)
        result = run_code(corrected_code)

        code_output.delete("1.0", END)
        code_output.insert(END, corrected_code)

        if result is None:
            explanation.set("✅ Code ran successfully.")
            save_history(original_code, corrected_code, "", "Code corrected and ran without errors.")
        else:
            error_message, error_type = result
            reason = ERROR_EXPLANATIONS.get(error_type, "Unknown error.")
            explanation.set(f"❌ {error_type}: {reason}")
            save_history(original_code, corrected_code, error_message, reason)

    def view_history():
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("SELECT * FROM code_history ORDER BY id DESC LIMIT 10")
        records = c.fetchall()
        conn.close()

        history_window = Toplevel(root)
        history_window.title("Correction History")

        for rec in records:
            Label(history_window, text=f"#{rec[0]} | {rec[5]}", fg="blue").pack(anchor='w')
            Label(history_window, text="🔸 Original Code:").pack(anchor='w')
            t1 = Text(history_window, height=4, width=100, bg="#fff0f0")
            t1.insert(END, rec[1])
            t1.config(state=DISABLED)
            t1.pack()

            Label(history_window, text="✅ Corrected Code:").pack(anchor='w')
            t2 = Text(history_window, height=4, width=100, bg="#f0fff0")
            t2.insert(END, rec[2])
            t2.config(state=DISABLED)
            t2.pack()

            Label(history_window, text="⚠️ Error Explanation: " + rec[4]).pack(anchor='w')
            Label(history_window, text="").pack()  # Spacer

    root = Tk()
    root.title("Offline Code Corrector App")
    root.geometry("800x700")

    Label(root, text="📝 Enter Python Code:", font=("Arial", 12, "bold")).pack(pady=5)
    code_input = Text(root, height=12, width=100, font=("Consolas", 11))
    code_input.pack(padx=10)

    Button(root, text="⚙️ Correct & Explain", command=correct_and_explain, bg="#e0f7fa").pack(pady=10)

    Label(root, text="🛠 Corrected Code:", font=("Arial", 12, "bold")).pack()
    code_output = Text(root, height=10, width=100, font=("Consolas", 11), bg="#e8f4ea")
    code_output.pack(padx=10)

    explanation = StringVar()
    Label(root, textvariable=explanation, font=("Arial", 11), fg="darkblue").pack(pady=5)

    Button(root, text="📜 View Correction History", command=view_history, bg="#f5f5f5").pack(pady=10)

    root.mainloop()

#update  








# === ENTRY POINT ===
if __name__ == "__main__":
    init_db()
    launch_gui()
