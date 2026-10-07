# Mirror Talk Theme 8.4.0

## Evidence-led SEO learning

Mirror Talk Intelligence can now learn from verified Google Search Console query-to-page performance without rewriting articles or chasing noisy signals.

### Automatic focus keywords

- Selects each post's focus keyword from the real queries that produced its impressions and clicks.
- Stores impressions, clicks and average position as inspectable evidence.
- Adds the learned keyword to Article/PodcastEpisode structured data alongside editorial tags.
- Exposes the focus keyword and learning state through the existing SEO REST field.

### Guarded search-title experiments

- Changes only the search/social meta title; the visible article headline is never rewritten.
- Starts no more than two experiments per weekly cycle.
- Requires at least 100 verified baseline impressions for the exact page.
- Runs a single variant for at least 21 days and accommodates Search Console's reporting delay.
- Requires at least 100 impressions for each side, an absolute CTR gain of 0.5 percentage points, a relative gain of 8% and a one-sided statistical threshold before keeping a title.
- Automatically restores the baseline when the evidence is weak or negative.
- Records baseline, variant, timing, keyword, metrics and decision.
- Queues affected URLs through IndexNow and preserves SEO revision history.
- Never repeats the same experiment for the same focus keyword.

### Controls and transparency

- New **SEO Learning** section inside **Mirror Talk Intelligence**.
- Highest-confidence opportunity table with observed query, impressions, clicks, CTR, position and recommended response.
- Experiment status and complete decision history.
- “Run learning cycle now” administrator action.
- Global pause restores every running experiment immediately.
- Per-post **Keep this post under manual SEO control** override.
- Existing manually written SEO titles are never taken over by automation.
- An editor change made during a running experiment immediately ends automation for that post and preserves the editor's title.
- Average query position is impression-weighted rather than averaging daily averages equally.

Automatic learning is enabled by default but remains deliberately conservative. Posts without adequate verified data stay unchanged.
