"""Cloud-ready Insider Threat Monitoring dashboard (Flask)."""
import os
import logging
from datetime import datetime

from flask import Flask, jsonify, render_template

from log_generator import generate_logs
from risk_engine import parse_logs, user_summary, event_breakdown

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

LOG_COUNT = int(os.environ.get("LOG_COUNT", "2000"))
S3_BUCKET = os.environ.get("S3_BUCKET")  # optional: raw logs are archived to S3


def archive_to_s3(lines):
    """Store raw logs in S3 (uses the EC2 instance's IAM role, no keys in code)."""
    if not S3_BUCKET:
        return
    try:
        import boto3
        key = f"raw-logs/{datetime.utcnow():%Y/%m/%d/%H%M%S}.log"
        boto3.client("s3").put_object(Bucket=S3_BUCKET, Key=key, Body="\n".join(lines).encode())
        app.logger.info("Archived raw logs to s3://%s/%s", S3_BUCKET, key)
    except Exception as exc:  # the dashboard must keep working if S3 is unavailable
        app.logger.warning("S3 archive failed: %s", exc)


LINES = generate_logs(LOG_COUNT, seed=42)
archive_to_s3(LINES)
DF = parse_logs(LINES)


@app.route("/")
def index():
    return render_template("dashboard.html")


@app.route("/api/users")
def api_users():
    return jsonify(user_summary(DF).to_dict(orient="records"))


@app.route("/api/events")
def api_events():
    return jsonify(event_breakdown(DF).to_dict())


@app.route("/api/recent")
def api_recent():
    return jsonify(DF.tail(15).to_dict(orient="records"))


@app.route("/health")
def health():
    return jsonify(status="ok", events=int(len(DF)))


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=7860)
