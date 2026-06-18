import os
import sys
import requests
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

POLAND_TZ = timezone(timedelta(hours=2))  # CEST

# -------------------------------------------------------
# Lista odbiorców — dodaj kolejne adresy email poniżej:
RECIPIENTS = [
    "mikulski.powiadomienia@gmail.com",
    # "kolega@gmail.com",
    # "inny@przykład.pl",
]
# -------------------------------------------------------

API_KEY = os.environ['FOOTBALL_API_KEY']
EMAIL = os.environ['EMAIL_ADDRESS']
APP_PASSWORD = os.environ['EMAIL_APP_PASSWORD']

yesterday = (datetime.now(POLAND_TZ) - timedelta(days=1)).date()
yesterday_str = yesterday.isoformat()

response = requests.get(
    'https://api.football-data.org/v4/competitions/WC/matches',
    headers={'X-Auth-Token': API_KEY},
    params={'dateFrom': yesterday_str, 'dateTo': yesterday_str, 'status': 'FINISHED'},
)
response.raise_for_status()
matches = response.json().get('matches', [])

if not matches:
    print("Brak zakończonych meczów z wczoraj — email nie zostanie wysłany.")
    sys.exit(0)

date_polish = yesterday.strftime('%d.%m.%Y')
subject = f"Mundial 2026 — Wyniki z {date_polish}"

rows = []
for m in sorted(matches, key=lambda x: x['utcDate']):
    home = m['homeTeam']['name']
    away = m['awayTeam']['name']
    score = m['score']['fullTime']
    hg = score.get('home', '?')
    ag = score.get('away', '?')
    label = m.get('group') or m.get('stage', '')
    rows.append(
        f"<tr><td style='padding:6px 12px;font-size:20px;font-weight:bold'>"
        f"{home} {hg} — {ag} {away}</td>"
        f"<td style='padding:6px 12px;color:#888'>{label}</td></tr>"
    )

body = f"""
<html><body style='font-family:sans-serif;color:#222'>
<h2 style='color:#1a6b2f'>⚽ Wyniki Mundialu — {date_polish}</h2>
<table border='0' cellpadding='0' cellspacing='0'>
  <tr style='background:#f0f0f0'>
    <th style='padding:6px 12px;text-align:left'>Wynik</th>
    <th style='padding:6px 12px;text-align:left'>Runda</th>
  </tr>
  {''.join(rows)}
</table>
</body></html>
"""

msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = EMAIL
msg['To'] = ', '.join(RECIPIENTS)
msg.attach(MIMEText(body, 'html'))

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL, APP_PASSWORD)
    smtp.sendmail(EMAIL, RECIPIENTS, msg.as_string())

print(f"Wysłano: {subject} → {RECIPIENTS}")
