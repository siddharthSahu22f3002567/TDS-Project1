import os
import requests
from flask import Flask, request, jsonify
import subprocess
import json
from datetime import datetime
import sqlite3
from pathlib import Path

app = Flask(__name__)

# LLM API Call
def call_llm_api(prompt):
    api_url = "https://api.openai-proxy.com/v1/completions"
    headers = {
        "Authorization": f"Bearer {os.environ['AIPROXY_TOKEN']}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
        "prompt": prompt,
        "max_tokens": 100
    }
    response = requests.post(api_url, headers=headers, json=data)
    if response.status_code == 200:
        return response.json()["choices"][0]["text"].strip()
    else:
        raise Exception(f"LLM API Error: {response.status_code} - {response.text}")

# Task Execution Logic
@app.route('/run', methods=['POST'])
def run_task():
    task_description = request.args.get('task')
    
    try:
        # A1: Install and run datagen.py
        if "datagen.py" in task_description:
            email = os.environ.get("USER_EMAIL", "user@example.com")
            subprocess.run(["pip", "install", "uv"], check=True)
            subprocess.run(["python", "datagen.py", email], check=True)
            return jsonify({"message": "Data generation complete."}), 200

        # A2: Format file with prettier
        elif "prettier" in task_description:
            subprocess.run(["npx", "prettier", "--write", "/data/format.md"], check=True)
            return jsonify({"message": "File formatted with Prettier."}), 200

        # A3: Count Wednesdays
        elif "count Wednesdays" in task_description:
            with open('/data/dates.txt', 'r') as f:
                dates = f.readlines()
            wednesday_count = sum(1 for date in dates if datetime.strptime(date.strip(), "%Y-%m-%d").weekday() == 2)
            with open('/data/dates-wednesdays.txt', 'w') as f:
                f.write(str(wednesday_count))
            return jsonify({"message": "Wednesdays counted."}), 200

        # A4: Sort contacts
        elif "sort contacts" in task_description:
            with open('/data/contacts.json', 'r') as f:
                contacts = json.load(f)
            contacts.sort(key=lambda x: (x['last_name'], x['first_name']))
            with open('/data/contacts-sorted.json', 'w') as f:
                json.dump(contacts, f, indent=4)
            return jsonify({"message": "Contacts sorted."}), 200

        # A5: Get first lines of recent logs
        elif "recent logs" in task_description:
            logs = sorted(Path('/data/logs/').glob('*.log'), key=lambda x: x.stat().st_mtime, reverse=True)
            recent_lines = [open(log).readline().strip() for log in logs[:10]]
            with open('/data/logs-recent.txt', 'w') as f:
                f.write('\n'.join(recent_lines))
            return jsonify({"message": "Recent log lines extracted."}), 200

        # A6: Create docs index
        elif "index Markdown files" in task_description:
            index = {}
            for md_file in Path('/data/docs/').glob('*.md'):
                with open(md_file, 'r') as f:
                    for line in f:
                        if line.startswith('# '):
                            index[md_file.name] = line.strip('# ').strip()
                            break
            with open('/data/docs/index.json', 'w') as f:
                json.dump(index, f, indent=4)
            return jsonify({"message": "Markdown index created."}), 200

        # A7: Extract email sender with LLM
        elif "extract sender’s email address" in task_description:
            with open('/data/email.txt', 'r') as f:
                email_content = f.read()
            prompt = f"Extract the sender's email address from this content:\n{email_content}"
            result = call_llm_api(prompt)
            with open('/data/email-sender.txt', 'w') as f:
                f.write(result)
            return jsonify({"message": "Email sender extracted."}), 200

        # A8: Extract credit card number with LLM
        elif "extract the credit card number" in task_description:
            prompt = "Extract the credit card number from the following image: /data/credit-card.png"
            result = call_llm_api(prompt)
            with open('/data/credit-card.txt', 'w') as f:
                f.write(result.replace(" ", ""))
            return jsonify({"message": "Credit card number extracted."}), 200

        # A9: Find similar comments with embeddings
        elif "find the most similar pair of comments" in task_description:
            with open('/data/comments.txt', 'r') as f:
                comments = f.readlines()
            prompt = f"Find the most similar pair of comments from this list:\n{comments}"
            result = call_llm_api(prompt)
            with open('/data/comments-similar.txt', 'w') as f:
                f.write(result)
            return jsonify({"message": "Most similar comments identified."}), 200

        # A10: Calculate total sales for Gold tickets
        elif "total sales of Gold tickets" in task_description:
            conn = sqlite3.connect('/data/ticket-sales.db')
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(units * price) FROM tickets WHERE type = 'Gold'")
            total_sales = cursor.fetchone()[0]
            conn.close()
            with open('/data/ticket-sales-gold.txt', 'w') as f:
                f.write(str(total_sales))
            return jsonify({"message": "Total sales calculated."}), 200

        else:
            return jsonify({"error": "Task not recognized."}), 400

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/read', methods=['GET'])
def read_file():
    file_path = request.args.get('path')
    if not file_path.startswith('/data/'):
        return jsonify({"error": "Access denied."}), 403
    if not Path(file_path).exists():
        return jsonify({"error": "File not found."}), 404
    with open(file_path, 'r') as f:
        content = f.read()
    return content, 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)