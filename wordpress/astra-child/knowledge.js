(() => {
  'use strict';
  const config = window.MirrorTalkKnowledge || {};
  if (!config.postId) return;
  const consentKey = 'amt_analytics_consent_v1';
  const historyKey = 'mt_content_history_v1';
  const allowed = () => { try { return localStorage.getItem(consentKey) === 'granted'; } catch (_) { return false; } };
  if (!allowed()) return;
  let history = [];
  try { history = JSON.parse(localStorage.getItem(historyKey) || '[]'); } catch (_) {}
  history = history.filter((item) => item && Number(item.id) !== Number(config.postId));
  history.unshift({ id: Number(config.postId), title: String(config.title || '').slice(0, 180), url: String(config.url || ''), topics: Array.isArray(config.safeTopics) ? config.safeTopics.slice(0, 5) : [], time: Date.now() });
  try { localStorage.setItem(historyKey, JSON.stringify(history.slice(0, 20))); } catch (_) {}
  if (Array.isArray(config.safeTopics) && config.safeTopics[0] && window.MirrorTalkTrack) {
    window.MirrorTalkTrack('safe_topic_view', { path: location.pathname, search_term: String(config.safeTopics[0]).slice(0, 80) });
  }
  const related = document.querySelector('[data-mt-personalized-related]');
  const reason = document.querySelector('[data-mt-personalization-reason]');
  if (!related || !reason || history.length < 2) return;
  const recent = history.slice(1).flatMap((item) => item.topics || []).filter(Boolean);
  if (!recent.length) return;
  reason.hidden = false;
  reason.textContent = 'Suggestions may reflect pages you chose to read on this device. This history stays in your browser and can be cleared with site data.';
})();
