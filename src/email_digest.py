"""Email digest — send daily briefing via email."""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import date


def send_digest(smtp_host: str, smtp_port: int, sender_email: str,
                sender_password: str, recipient_email: str,
                briefing_data: dict) -> bool:
    """Send a formatted daily briefing email."""
    try:
        subject = f"🍡 Mochi's Briefing — {briefing_data.get('date', date.today().isoformat())}"
        html = _build_html(briefing_data)

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Mochi's Assistant <{sender_email}>"
        msg["To"] = recipient_email

        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(smtp_host, smtp_port) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, recipient_email, msg.as_string())

        return True
    except Exception as e:
        print(f"[Email] Failed to send: {e}")
        return False


def _build_html(data: dict) -> str:
    """Build a beautiful HTML email from briefing data."""
    d = data.get("date", date.today().isoformat())

    # Focus
    focus = data.get("focus", {})
    energy = focus.get("energy_forecast", "Have a great day!")
    tip = focus.get("tip", "")

    # Summary card
    sc = data.get("summary_card", {})
    insights = sc.get("insights", [])
    score = sc.get("overall_score")

    # Schedules
    schedules = data.get("schedules_today", [])

    # Tasks
    tasks = data.get("tasks", {})
    task_list = tasks.get("prioritized_tasks", [])
    urgent = [t for t in task_list if t.get("quadrant") == "DO NOW" and t.get("status") != "done"]

    # Weather
    weather = data.get("weather", {})

    # Nudges
    nudges = data.get("nudges", [])

    # Goals
    goals_list = data.get("goals", [])

    # Sleep rec
    sleep_rec = data.get("sleep_rec", {})

    html = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"><meta name="viewport" content="width=device-width"></head>
<body style="font-family:-apple-system,'Segoe UI',sans-serif;background:#FFF0F3;margin:0;padding:20px;">
<div style="max-width:600px;margin:0 auto;background:#fff;border-radius:20px;overflow:hidden;box-shadow:0 4px 20px rgba(248,164,184,0.2);">

<!-- Header -->
<div style="background:linear-gradient(135deg,#F8A4B8,#F9C5D1);padding:24px;text-align:center;color:#fff;">
<h1 style="margin:0;font-size:22px;">🍡 Good Morning!</h1>
<p style="margin:6px 0 0;font-size:14px;opacity:0.9;">{d}</p>
</div>

<div style="padding:20px;">
"""

    # Weather
    if weather.get("has_data"):
        w = weather["current"]
        html += f"""<div style="background:#F0F4FF;padding:12px;border-radius:12px;margin-bottom:14px;">
<b style="font-size:18px;">{w['temp']}°C</b> <span style="color:#9C7A8A;font-size:12px;">{weather['city']} · {w['description']} · Feels {w['feels_like']}°C</span>
"""
        for r in weather.get("reminders", [])[:2]:
            html += f"<div style='font-size:12px;margin-top:4px;'>{r['icon']} {r['text']}</div>"
        html += "</div>"

    # Summary score
    if score is not None:
        html += f"""<div style="text-align:center;margin-bottom:14px;">
<span style="font-size:32px;font-weight:700;color:#E87A95;">{score}</span>
<span style="font-size:12px;color:#9C7A8A;">/100 yesterday</span></div>"""

    # Insights
    if insights:
        for i in insights[:4]:
            html += f"<div style='font-size:12px;padding:4px 0;color:#6B4C5A;'>• {i}</div>"
        html += "<br>"

    # Nudges
    if nudges:
        html += "<div style='background:#FFF0F5;padding:12px;border-radius:12px;margin-bottom:14px;'>"
        html += "<b style='font-size:12px;color:#E87A95;'>💌 Mochi Says</b><br>"
        for n in nudges[:4]:
            html += f"<div style='font-size:11px;padding:3px 0;'>{n.get('icon','')} {n['text']}</div>"
        html += "</div>"

    # Today's schedule
    if schedules:
        html += "<div style='margin-bottom:14px;'><b style='font-size:13px;color:#E87A95;'>📅 Today's Schedule</b>"
        for s in sorted(schedules, key=lambda x: x.get("time_start", "")):
            loc = f" · 📍{s['location']}" if s.get("location") else ""
            html += f"<div style='font-size:12px;padding:4px 0;border-bottom:1px solid #FFDBE5;'><b>{s.get('time_start','')}-{s.get('time_end','')}</b> {s['title']}{loc}</div>"
        html += "</div>"

    # Urgent tasks
    if urgent:
        html += "<div style='margin-bottom:14px;'><b style='font-size:13px;color:#E87A95;'>🔥 Urgent Tasks</b>"
        for t in urgent[:5]:
            dl = f" ({t['deadline']})" if t.get("deadline") else ""
            html += f"<div style='font-size:12px;padding:3px 0;'>• {t['title']}{dl}</div>"
        html += "</div>"

    # Energy forecast
    html += f"""<div style="background:linear-gradient(135deg,#FFDBE5,#F0E6FF);padding:12px;border-radius:12px;margin-bottom:14px;">
<div style="font-size:12px;font-style:italic;">{energy}</div>
<div style="font-size:11px;margin-top:6px;">💡 {tip}</div></div>"""

    # TOPIK
    for g in goals_list:
        s = g.get("summary", {})
        if s.get("days_left") is not None:
            html += f"""<div style="font-size:12px;padding:8px;background:#FFF5F7;border-radius:8px;margin-bottom:10px;">
🇰🇷 <b>{g['title']}</b>: {s['days_left']} days left · {s.get('adjusted_daily_target',20)} words today · Streak: {s.get('streak',0)}d</div>"""

    # Sleep rec
    if sleep_rec.get("suggested_bedtime"):
        html += f"<div style='font-size:11px;color:#9C7A8A;'>😴 Suggested bedtime tonight: <b>{sleep_rec['suggested_bedtime']}</b></div>"

    html += """
</div>
<div style="text-align:center;padding:14px;font-size:10px;color:#C9AEBB;">
Mochi's Assistant · <a href="http://localhost:5050" style="color:#F8A4B8;">Open Dashboard</a>
</div>
</div></body></html>"""

    return html
