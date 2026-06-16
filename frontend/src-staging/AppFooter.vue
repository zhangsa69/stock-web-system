<template>
  <footer class="app-footer">
    <p>AI 股票财报分析平台 · 基于 Hermes Agent 驱动的智能财务分析</p>
    <p class="app-footer__disclaimer">本平台分析结果仅供参考，不构成投资建议。投资有风险，入市需谨慎。</p>
  </footer>
</template>

<style scoped>
.app-footer {
  background: var(--cb-surface-dark, #0a0b0d);
  border-top: 1px solid var(--cb-hairline-dark, rgba(255,255,255,0.08));
  padding: 64px 24px;
  text-align: center;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  font-size: 13px;
  font-weight: 300;
  color: var(--cb-muted-soft, rgba(255,255,255,0.4));
  line-height: 1.8;
}
.app-footer__disclaimer {
  color: rgba(255,255,255,0.25);
  font-size: 12px;
  margin-top: 4px;
}
</style>
