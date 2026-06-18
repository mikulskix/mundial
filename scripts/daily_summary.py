import os
import sys
import requests
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from team_names import translate

POLAND_TZ = timezone(timedelta(hours=2))  # CEST

# -------------------------------------------------------
# Lista odbiorców — dodaj kolejne adresy email poniżej:
RECIPIENTS = [
    "mikulski.powiadomienia@gmail.com",
   # "olamikulska10@gmail.com",
    # "inny@przykład.pl",
]
# -------------------------------------------------------

API_KEY = os.environ['FOOTBALL_API_KEY']
EMAIL = os.environ['EMAIL_ADDRESS']
APP_PASSWORD = os.environ['EMAIL_APP_PASSWORD']

now = datetime.now(POLAND_TZ)
today = now.date()
yesterday = (now - timedelta(days=1)).date()


def fetch_matches(date_from, date_to, status=None):
    params = {'dateFrom': date_from.isoformat(), 'dateTo': date_to.isoformat()}
    if status:
        params['status'] = status
    r = requests.get(
        'https://api.football-data.org/v4/competitions/WC/matches',
        headers={'X-Auth-Token': API_KEY},
        params=params,
    )
    r.raise_for_status()
    return r.json().get('matches', [])


results = fetch_matches(yesterday, yesterday, status='FINISHED')
upcoming = fetch_matches(today, today)

if not results and not upcoming:
    print("Brak meczów — email nie zostanie wysłany.")
    sys.exit(0)

sections = []

if results:
    yesterday_polish = yesterday.strftime('%d.%m.%Y')
    rows = []
    for m in sorted(results, key=lambda x: x['utcDate']):
        home = translate(m['homeTeam']['name'])
        away = translate(m['awayTeam']['name'])
        score = m['score']['fullTime']
        hg = score.get('home', '?')
        ag = score.get('away', '?')
        label = m.get('group') or m.get('stage', '')
        rows.append(
            f"<tr><td style='padding:6px 12px;font-size:14px'>"
            f"{home} {hg} — {ag} {away}</td>"
            f"<td style='padding:6px 12px;color:#888'>{label}</td></tr>"
        )
    sections.append(f"""
<h2 style='color:#1a6b2f'>⚽ Wyniki z {yesterday_polish}</h2>
<table border='0' cellpadding='0' cellspacing='0'>
  <tr style='background:#f0f0f0'>
    <th style='padding:6px 12px;text-align:left'>Wynik</th>
    <th style='padding:6px 12px;text-align:left'>Runda</th>
  </tr>
  {''.join(rows)}
</table>
""")

if upcoming:
    today_polish = today.strftime('%d.%m.%Y')
    rows = []
    for m in sorted(upcoming, key=lambda x: x['utcDate']):
        utc_time = datetime.fromisoformat(m['utcDate'].replace('Z', '+00:00'))
        local_time = utc_time.astimezone(POLAND_TZ).strftime('%H:%M')
        home = translate(m['homeTeam']['name'])
        away = translate(m['awayTeam']['name'])
        label = m.get('group') or m.get('stage', '')
        rows.append(
            f"<tr><td style='padding:6px 12px;font-size:14px'><b>{local_time}</b></td>"
            f"<td style='padding:6px 12px'>{home} <b>vs</b> {away}</td>"
            f"<td style='padding:6px 12px;color:#888'>{label}</td></tr>"
        )
    sections.append(f"""
<h2 style='color:#1a6b2f;margin-top:24px'>📅 Mecze na dziś ({today_polish})</h2>
<table border='0' cellpadding='0' cellspacing='0'>
  <tr style='background:#f0f0f0'>
    <th style='padding:6px 12px;text-align:left'>Godz.</th>
    <th style='padding:6px 12px;text-align:left'>Mecz</th>
    <th style='padding:6px 12px;text-align:left'>Runda</th>
  </tr>
  {''.join(rows)}
</table>
""")

today_polish = today.strftime('%d.%m.%Y')
subject = f"Mundial 2026 — Poranek {today_polish}"
body = f"<html><body style='font-family:sans-serif;color:#222'>{''.join(sections)}</body></html>"

msg = MIMEMultipart('alternative')
msg['Subject'] = subject
msg['From'] = EMAIL
msg['To'] = ', '.join(RECIPIENTS)
msg.attach(MIMEText(body, 'html'))

with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
    smtp.login(EMAIL, APP_PASSWORD)
    smtp.sendmail(EMAIL, RECIPIENTS, msg.as_string())

print(f"Wysłano: {subject} → {RECIPIENTS}")
