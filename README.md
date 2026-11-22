<div class="ks-badges">
  <span class="ks-badge python">
    <span class="ks-icon">🐍</span>
    <span>Python Backend</span>
  </span>
  <span class="ks-divider">|</span>
  <span class="ks-badge telegram">
    <span class="ks-icon">✈️</span>
    <span>Telegram Bot &amp; API</span>
  </span>
  <span class="ks-divider">|</span>
  <span class="ks-badge vercel">
    <span class="ks-icon">▲</span>
    <span>Vercel Deployment</span>
  </span>
</div>

<style>
  .ks-badges {
    display: inline-flex;
    flex-wrap: wrap;
    align-items: center;
    justify-content: center;
    gap: 10px;
    font-family: system-ui, -apple-system, "Segoe UI", Roboto, sans-serif;
    font-weight: 600;
    font-size: 14px;
  }

  .ks-badge {
    display: inline-flex;
    align-items: center;
    gap: 7px;
    padding: 7px 14px;
    border-radius: 999px;
    color: #ffffff;
    border: 1px solid rgba(255, 255, 255, 0.16);
    box-shadow: 0 6px 18px rgba(0, 0, 0, 0.25), inset 0 1px 0 rgba(255, 255, 255, 0.2);
    transition: transform 0.2s ease, box-shadow 0.2s ease;
  }

  .ks-badge:hover {
    transform: translateY(-2px);
    box-shadow: 0 10px 22px rgba(0, 0, 0, 0.35), inset 0 1px 0 rgba(255, 255, 255, 0.3);
  }

  .ks-badge.python {
    background: linear-gradient(135deg, #2563eb, #1d4ed8);
  }

  .ks-badge.telegram {
    background: linear-gradient(135deg, #0ea5e9, #0284c7);
  }

  .ks-badge.vercel {
    background: linear-gradient(135deg, #18181b, #09090b);
  }

  .ks-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.14);
    font-size: 13px;
  }

  .ks-divider {
    color: #94a3b8;
    font-weight: 700;
    user-select: none;
  }
</style>
