<?php
/**
 * Template Name: Mirror Talk Answer Archive
 *
 * SEO-friendly page showing frequently asked questions and their answers.
 * Usage: Create a WordPress page, set its template to "Mirror Talk Answer Archive".
 */

if (!defined('ABSPATH')) {
    exit;
}

$api_url = 'https://ask-mirror-talk-production.up.railway.app/api/answer-archive?limit=50';
$response = wp_remote_get($api_url, ['timeout' => 15]);

$archive = [];
if (!is_wp_error($response) && wp_remote_retrieve_response_code($response) === 200) {
    $body = json_decode(wp_remote_retrieve_body($response), true);
    $archive = $body['archive'] ?? [];
}

get_header();
?>

<main id="amt-archive-page" class="amt-archive-page">
  <div class="amt-archive-inner">

    <header class="amt-archive-header">
      <h1>Mirror Talk: Frequently Asked Questions</h1>
      <p class="amt-archive-subtitle">
        Explore answers from the Mirror Talk podcast on personal growth, healing, relationships, and faith.
        Questions are answered from <?php echo esc_html(count($archive)); ?>+ hours of podcast episodes.
      </p>
      <a href="/ask-mirror-talk" class="amt-archive-cta">Ask your own question →</a>
    </header>

    <?php if (empty($archive)): ?>
      <p class="amt-archive-empty">No archived answers found. <a href="/ask-mirror-talk">Be the first to ask a question!</a></p>
    <?php else: ?>

    <!-- FAQ Schema for SEO -->
    <script type="application/ld+json">
    {
      "@context": "https://schema.org",
      "@type": "FAQPage",
      "mainEntity": [
        <?php
        $schema_items = array_slice($archive, 0, 20);
        $schema_json = array_map(function($item) {
            return json_encode([
                '@type' => 'Question',
                'name'  => $item['question'],
                'acceptedAnswer' => [
                    '@type' => 'Answer',
                    'text'  => wp_strip_all_tags($item['answer_snippet'] ?? ''),
                ],
            ]);
        }, $schema_items);
        echo implode(",\n        ", $schema_json);
        ?>
      ]
    }
    </script>

    <div class="amt-archive-list">
      <?php foreach ($archive as $item): ?>
      <article class="amt-archive-item" itemscope itemtype="https://schema.org/Question">
        <h2 class="amt-archive-question" itemprop="name">
          <?php echo esc_html($item['question']); ?>
        </h2>
        <?php if ($item['asked_count'] > 1): ?>
        <span class="amt-archive-count">Asked <?php echo esc_html($item['asked_count']); ?> times</span>
        <?php endif; ?>
        <div class="amt-archive-answer" itemprop="acceptedAnswer" itemscope itemtype="https://schema.org/Answer">
          <p itemprop="text"><?php echo esc_html($item['answer_snippet']); ?>…</p>
        </div>
        <a href="/ask-mirror-talk/?autoask=<?php echo urlencode($item['question']); ?>" class="amt-archive-explore">
          Get the full answer →
        </a>
      </article>
      <?php endforeach; ?>
    </div>

    <?php endif; ?>

    <div class="amt-archive-footer">
      <a href="/ask-mirror-talk" class="amt-archive-cta">Ask a new question →</a>
    </div>

  </div>
</main>

<style>
.amt-archive-page {
  max-width: 860px;
  margin: 0 auto;
  padding: 48px 24px 80px;
}
.amt-archive-inner {}
.amt-archive-header {
  text-align: center;
  margin-bottom: 48px;
}
.amt-archive-header h1 {
  font-size: clamp(1.6rem, 4vw, 2.4rem);
  margin-bottom: 12px;
}
.amt-archive-subtitle {
  color: #666;
  max-width: 600px;
  margin: 0 auto 20px;
  line-height: 1.6;
}
.amt-archive-cta {
  display: inline-block;
  background: #2e2a24;
  color: #f7c948;
  padding: 12px 28px;
  border-radius: 10px;
  text-decoration: none;
  font-weight: 600;
  transition: opacity 0.2s;
}
.amt-archive-cta:hover { opacity: 0.85; color: #f7c948; }
.amt-archive-list {
  display: flex;
  flex-direction: column;
  gap: 28px;
}
.amt-archive-item {
  border: 1px solid #e5e0d8;
  border-radius: 14px;
  padding: 24px 28px;
  background: #fdfbf8;
  transition: box-shadow 0.2s;
}
.amt-archive-item:hover {
  box-shadow: 0 4px 20px rgba(0,0,0,0.08);
}
.amt-archive-question {
  font-size: 1.15rem;
  margin: 0 0 6px;
  color: #2e2a24;
}
.amt-archive-count {
  font-size: 0.78rem;
  color: #999;
  display: block;
  margin-bottom: 10px;
}
.amt-archive-answer p {
  color: #555;
  line-height: 1.65;
  margin: 0 0 12px;
}
.amt-archive-explore {
  font-size: 0.88rem;
  color: #8b6c3e;
  text-decoration: none;
  font-weight: 500;
}
.amt-archive-explore:hover { text-decoration: underline; }
.amt-archive-footer {
  text-align: center;
  margin-top: 48px;
}
.amt-archive-empty {
  text-align: center;
  color: #888;
  padding: 40px;
}
</style>

<?php get_footer(); ?>
