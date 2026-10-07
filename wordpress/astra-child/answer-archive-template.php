<?php
/**
 * Template Name: Mirror Talk Insights Library
 * Public privacy-screened themes plus browser-local saved reflections.
 */
if (!defined('ABSPATH')) { exit; }
get_header();
?>
<main id="primary" class="site-main mt-insights-library">
    <header class="mt-insights-library__hero"><div class="mt-insights-library__shell">
        <p class="mt-section-kicker"><?php esc_html_e('Ask Mirror Talk archive', 'astra-child'); ?></p>
        <h1><?php esc_html_e('Insights worth returning to.', 'astra-child'); ?></h1>
        <p><?php esc_html_e('Explore recurring questions from our curated reflection prompts, then return to insights you privately saved on this device. Free-form visitor questions are never published.', 'astra-child'); ?></p>
        <a class="mt-button" href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>"><?php esc_html_e('Ask your own question', 'astra-child'); ?></a>
    </div></header>

    <section class="mt-insights-library__shell mt-insights-library__content" aria-labelledby="mt-community-insights-title">
        <div class="mt-insights-library__heading"><div><p class="mt-section-kicker"><?php esc_html_e('From the Ask Mirror Talk archive', 'astra-child'); ?></p><h2 id="mt-community-insights-title"><?php esc_html_e('Questions many of us carry', 'astra-child'); ?></h2></div><span data-mt-community-count><?php esc_html_e('Loading…', 'astra-child'); ?></span></div>
        <div class="mt-insights-library__grid" data-mt-community-archive aria-live="polite"><article class="mt-insight-empty"><span aria-hidden="true">✦</span><h3><?php esc_html_e('Gathering thoughtful reflections…', 'astra-child'); ?></h3></article></div>
    </section>

    <section class="mt-insights-library__shell mt-insights-library__content mt-insights-library__private" aria-labelledby="mt-saved-insights-title">
        <div class="mt-saved-moments" data-mt-saved-moments hidden>
            <div class="mt-insights-library__heading"><div><p class="mt-section-kicker"><?php esc_html_e('Your listening journey', 'astra-child'); ?></p><h2><?php esc_html_e('Moments you kept', 'astra-child'); ?></h2></div><span data-mt-moments-count></span></div>
            <div class="mt-insights-library__grid" data-mt-moments-grid></div>
        </div>
        <div class="mt-insights-library__heading"><div><p class="mt-section-kicker"><?php esc_html_e('Private on this device', 'astra-child'); ?></p><h2 id="mt-saved-insights-title"><?php esc_html_e('Your saved insights', 'astra-child'); ?></h2></div><span data-mt-insights-count></span></div>
        <div class="mt-insights-library__grid" data-mt-insights-archive></div>
        <noscript><p><?php esc_html_e('Enable JavaScript to view the insights saved privately in this browser.', 'astra-child'); ?></p></noscript>
    </section>
</main>
<script>
(() => {
  const escape = (value) => { const node = document.createElement('span'); node.textContent = String(value || ''); return node.innerHTML; };
  const publicRoot = document.querySelector('[data-mt-community-archive]');
  const publicCount = document.querySelector('[data-mt-community-count]');
  const apiBase = window.MirrorTalkSite?.apiBase || 'https://ask-mirror-talk-production.up.railway.app';
  fetch(`${apiBase}/api/answer-archive?limit=24`, { headers: { Accept: 'application/json' }, credentials: 'omit' })
    .then((response) => { if (!response.ok) throw new Error('Archive unavailable'); return response.json(); })
    .then((payload) => {
      const items = Array.isArray(payload.archive)
        ? payload.archive.filter((item) => item && item.privacy === 'curated_prompt')
        : [];
      publicCount.textContent = `${items.length} reflections`;
      if (!items.length) {
        publicRoot.innerHTML = '<article class="mt-insight-empty"><span aria-hidden="true">✦</span><h3>The archive is growing.</h3><p>Curated community prompts will appear here as the conversations develop.</p></article>';
        return;
      }
      publicRoot.innerHTML = items.map((item) => `<article class="mt-insight-card"><p class="mt-insight-card__meta">Asked ${Number(item.asked_count || 1)} time${Number(item.asked_count || 1) === 1 ? '' : 's'} · Privacy-screened</p><h3>${escape(item.question)}</h3><p>${escape(item.answer_snippet)}</p><a href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>?question=${encodeURIComponent(item.question)}">Explore this question →</a></article>`).join('');
    })
    .catch(() => {
      publicCount.textContent = 'Archive temporarily unavailable';
      publicRoot.innerHTML = '<article class="mt-insight-empty"><span aria-hidden="true">✦</span><h3>The archive is resting.</h3><p>Your private saved insights are still available below.</p></article>';
    });

  const root = document.querySelector('[data-mt-insights-archive]');
  const count = document.querySelector('[data-mt-insights-count]');
  let insights = [];
  let moments = [];
  try { moments = JSON.parse(localStorage.getItem('mt_saved_moments_v1') || '[]'); } catch (_) {}
  const momentsSection = document.querySelector('[data-mt-saved-moments]');
  const momentsGrid = document.querySelector('[data-mt-moments-grid]');
  if (Array.isArray(moments) && moments.length) {
    momentsSection.hidden = false;
    document.querySelector('[data-mt-moments-count]').textContent = `${moments.length} saved`;
    momentsGrid.innerHTML = moments.map((moment, index) => `<article class="mt-insight-card mt-moment-card"><p class="mt-insight-card__meta">${escape(moment.timeLabel || 'Saved moment')} · Private on this device</p><h3>${escape(moment.title || 'Mirror Talk moment')}</h3><div><button type="button" data-mt-resume-moment="${index}">Continue listening</button><button type="button" data-mt-reflect-saved="${index}">Reflect on this</button></div></article>`).join('');
    momentsGrid.addEventListener('click', (event) => {
      const resume = event.target.closest('[data-mt-resume-moment]');
      const reflect = event.target.closest('[data-mt-reflect-saved]');
      const selected = resume || reflect;
      if (!selected) return;
      const index = Number(resume ? resume.dataset.mtResumeMoment : reflect.dataset.mtReflectSaved);
      const moment = moments[index]; if (!moment) return;
      if (resume) document.dispatchEvent(new CustomEvent('mt:resume-moment', { detail: moment }));
      if (reflect) {
        const target = new URL('<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>');
        target.searchParams.set('intent', 'saved_moment_reflection');
        target.searchParams.set('episode', moment.title || 'Mirror Talk episode');
        target.searchParams.set('at', moment.timeLabel || 'saved moment');
        target.searchParams.set('prefill', `I saved a moment from “${moment.title || 'Mirror Talk'}” at ${moment.timeLabel || 'this point'}. Help me reflect on why it stayed with me.`);
        location.assign(target.toString());
      }
    });
  }
  try { insights = JSON.parse(localStorage.getItem('amt_saved_insights') || '[]'); } catch (_) {}
  const renderPrivate = () => {
    if (!Array.isArray(insights) || !insights.length) {
      count.textContent = '0 saved';
      root.innerHTML = '<article class="mt-insight-empty"><span aria-hidden="true">✦</span><h3>No saved insights yet.</h3><p>After receiving an Ask Mirror Talk reflection, choose “Save insight.” It will remain only on this device.</p><a class="mt-button" href="<?php echo esc_url(home_url('/ask-mirror-talk/')); ?>">Begin a reflection</a></article>';
      return;
    }
    count.textContent = `${insights.length} saved`;
    root.innerHTML = insights.map((item, index) => {
      const saved = item.timestamp || item.savedAt || item.createdAt;
      const date = saved ? new Date(saved).toLocaleDateString(undefined, { year: 'numeric', month: 'short', day: 'numeric' }) : 'Saved insight';
      return `<article class="mt-insight-card"><p class="mt-insight-card__meta">${escape(item.theme || 'Reflection')} · ${escape(date)}</p><h3>${escape(item.question || item.title || 'A saved reflection')}</h3><p>${escape(item.answer || item.text || item.excerpt || '').slice(0, 560)}</p><button type="button" data-mt-remove-insight="${index}">Remove from this device</button></article>`;
    }).join('');
  };
  renderPrivate();
  root.addEventListener('click', (event) => {
    const button = event.target.closest('[data-mt-remove-insight]'); if (!button) return;
    insights.splice(Number(button.dataset.mtRemoveInsight), 1);
    localStorage.setItem('amt_saved_insights', JSON.stringify(insights));
    renderPrivate();
  });
})();
</script>
<?php get_footer(); ?>
