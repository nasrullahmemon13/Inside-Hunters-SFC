from datetime import datetime


def generate_weekly_digest_data(meetings_list, action_items_list):
    """Compiles weekly meeting counts, total hours, decisions, and pending deliverables."""
    total_meetings = len(meetings_list)
    total_duration = sum(m.get('duration_seconds', 0) for m in meetings_list)
    total_hours = round(total_duration / 3600, 1)

    all_decisions = []
    for m in meetings_list:
        decs = m.get('decisions', [])
        for d in decs:
            all_decisions.append({"meeting_title": m.get('title', 'Meeting'), "decision": d})

    open_items = [ai for ai in action_items_list if not ai.get('is_completed', False) and ai.get('status') != 'Completed']
    completed_items = [ai for ai in action_items_list if ai.get('is_completed', False) or ai.get('status') == 'Completed']
    high_priority = [ai for ai in open_items if str(ai.get('priority', '')).lower() == 'high']

    return {
        "generated_at": datetime.now().strftime("%B %d, %Y"),
        "total_meetings": total_meetings,
        "total_hours": total_hours,
        "decisions_count": len(all_decisions),
        "recent_decisions": all_decisions[:6],
        "open_action_items_count": len(open_items),
        "completed_action_items_count": len(completed_items),
        "high_priority_items": high_priority[:5],
        "all_open_items": open_items[:10],
        "recent_meetings": meetings_list[:5]
    }


def render_weekly_digest_html(user_name, digest_data):
    """Renders HTML email template for the weekly digest."""
    urgent_items_html = ""
    if digest_data['high_priority_items']:
        for item in digest_data['high_priority_items']:
            urgent_items_html += f"""
      <div class="item" style="border-left-color: #E16D72;">
        <div class="item-title">{item.get('task', 'Task')}</div>
        <div class="item-meta">Assignee: {item.get('assignee', 'Team')} · Due: {item.get('deadline', 'Upcoming')} · Priority: High</div>
      </div>"""
    else:
        urgent_items_html = '<div style="font-size: 12.5px; color: #9DC198; padding: 6px 0;">✔ No critical blockers or overdue high-priority items.</div>'

    decisions_html = ""
    if digest_data['recent_decisions']:
        for d in digest_data['recent_decisions']:
            decisions_html += f"""
      <div class="item" style="border-left-color: #9DC198;">
        <div class="item-title">{d['decision']}</div>
        <div class="item-meta">From: {d['meeting_title']}</div>
      </div>"""
    else:
        decisions_html = '<div style="font-size: 12.5px; color: #C9B7BA;">No decisions recorded this week.</div>'

    return f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
  body {{ margin: 0; padding: 0; background: #1B1219; font-family: 'Work Sans', -apple-system, sans-serif; color: #F8F1E7; }}
  .container {{ max-width: 600px; margin: 0 auto; background: #241820; border: 1px solid #40303A; border-radius: 12px; overflow: hidden; }}
  .header {{ background: linear-gradient(135deg, #2C1D26, #241820); padding: 32px 28px; border-bottom: 1px solid #40303A; }}
  .brand {{ font-family: monospace; font-size: 13px; color: #F0917A; text-transform: uppercase; letter-spacing: 0.08em; margin-bottom: 8px; }}
  .title {{ font-size: 24px; font-weight: 700; color: #F8F1E7; margin: 0 0 6px; }}
  .subtitle {{ font-size: 13px; color: #C9B7BA; margin: 0; }}
  .content {{ padding: 28px; }}
  .stat-grid {{ display: flex; gap: 12px; margin-bottom: 24px; }}
  .stat-box {{ flex: 1; background: #1F151D; border: 1px solid #40303A; border-radius: 8px; padding: 14px; text-align: center; }}
  .stat-num {{ font-size: 22px; font-weight: 700; color: #F0917A; }}
  .stat-lbl {{ font-size: 11px; color: #C9B7BA; text-transform: uppercase; margin-top: 4px; font-family: monospace; }}
  .section-h {{ font-size: 14px; font-weight: 600; color: #F8F1E7; text-transform: uppercase; letter-spacing: 0.05em; font-family: monospace; margin: 20px 0 10px; border-bottom: 1px solid #40303A; padding-bottom: 6px; }}
  .item {{ background: #1F151D; border-left: 3px solid #F0917A; padding: 10px 14px; border-radius: 4px; margin-bottom: 8px; font-size: 13px; }}
  .item-title {{ font-weight: 600; color: #F8F1E7; }}
  .item-meta {{ font-size: 11px; color: #C9B7BA; font-family: monospace; margin-top: 2px; }}
  .footer {{ padding: 20px 28px; background: #1B1219; border-top: 1px solid #40303A; font-size: 11px; color: #8A7780; text-align: center; font-family: monospace; }}
  .btn {{ display: inline-block; background: #F0917A; color: #2E140C; text-decoration: none; font-weight: 600; font-size: 13px; padding: 10px 20px; border-radius: 999px; margin-top: 14px; }}
</style>
</head>
<body>
<div style="padding: 24px 12px;">
  <div class="container">
    <div class="header">
      <div class="brand">● TalkToText Pro — Intelligence Digest</div>
      <div class="title">Weekly Meeting & Action Digest</div>
      <div class="subtitle">Hello {user_name}, here is your briefing for the week of {digest_data['generated_at']}.</div>
    </div>
    <div class="content">
      <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 20px;">
        <tr>
          <td width="32%" style="background:#1F151D;border:1px solid #40303A;border-radius:8px;padding:12px;text-align:center;">
            <div class="stat-num">{digest_data['total_meetings']}</div>
            <div class="stat-lbl">Meetings</div>
          </td>
          <td width="2%"></td>
          <td width="32%" style="background:#1F151D;border:1px solid #40303A;border-radius:8px;padding:12px;text-align:center;">
            <div class="stat-num">{digest_data['decisions_count']}</div>
            <div class="stat-lbl">Decisions</div>
          </td>
          <td width="2%"></td>
          <td width="32%" style="background:#1F151D;border:1px solid #40303A;border-radius:8px;padding:12px;text-align:center;">
            <div class="stat-num">{digest_data['open_action_items_count']}</div>
            <div class="stat-lbl">Pending Tasks</div>
          </td>
        </tr>
      </table>

      <div class="section-h">⚡ Urgent Action Items ({len(digest_data['high_priority_items'])})</div>
      {urgent_items_html}

      <div class="section-h" style="margin-top: 24px;">🏛 Key Decisions Logged</div>
      {decisions_html}

      <div style="text-align: center; margin-top: 24px;">
        <a href="http://127.0.0.1:5000/dashboard" class="btn">Open TalkToText Pro Workspace →</a>
      </div>
    </div>
    <div class="footer">
      TalkToText Pro AI Meeting Intelligence · Automatic Weekly Briefing
    </div>
  </div>
</div>
</body>
</html>"""
