<div align="center">

# Captcha-api

<p><strong>Project Directory &amp; Structure Overview</strong></p>

</div>

---

<div style="background-color: #0d1117; color: #e6edf3; border: 1px solid #30363d; border-radius: 8px; padding: 20px; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, monospace; max-width: 640px; margin: 16px auto; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);">
  <div style="display: flex; align-items: center; justify-content: space-between; border-bottom: 1px solid #21262d; padding-bottom: 10px; margin-bottom: 14px; font-size: 13px; color: #8b949e;">
    <span>Directory Tree</span>
    <span style="background-color: #161b22; border: 1px solid #30363d; padding: 2px 8px; border-radius: 4px; font-size: 11px;">Flask / Python</span>
  </div>
  <pre style="margin: 0; font-size: 14px; line-height: 1.65; overflow-x: auto; color: #e6edf3;"><span style="color: #79c0ff; font-weight: 600;">Captcha-api/</span>
<span style="color: #8b949e;">├──</span> <span style="color: #a5d6ff;">app.py</span>            <span style="color: #8b949e;"># Main application entry point &amp; API routes</span>
<span style="color: #8b949e;">├──</span> <span style="color: #a5d6ff;">requirements.txt</span>  <span style="color: #8b949e;"># Python package dependencies</span>
<span style="color: #8b949e;">└──</span> <span style="color: #79c0ff; font-weight: 600;">templates/</span>
    <span style="color: #8b949e;">└──</span> <span style="color: #d2a8ff;">index.html</span>      <span style="color: #8b949e;"># Frontend template view</span></pre>
</div>

---

## Project Layout

| Path | Role | Description |
| :--- | :--- | :--- |
| `app.py` | Backend | Handles application initialization, CAPTCHA logic, and endpoints. |
| `requirements.txt` | Dependencies | Lists required Python libraries for installation via `pip`. |
| `templates/index.html` | Frontend | HTML template rendered for the web interface. |

## Quick Setup

```bash
git clone <your-repository-url>
cd Captcha-api
pip install -r requirements.txt
python app.py
