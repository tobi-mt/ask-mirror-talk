# Mirror Talk SEO and Content Intelligence Blueprint

## Brand promise

**Mirror Talk — A place for conversations that help you see yourself, your life and your next step more clearly.**

The site journey is:

**Listen → Read → Explore → Reflect → Ask → Connect → Return**

SEO should make the podcast library more discoverable without turning private
Ask Mirror Talk interactions into public content.

## Search architecture

### Homepage

- Purpose: brand, promise and primary journeys
- Suggested title: `Mirror Talk Podcast | Soulful Conversations for Personal Growth`
- Suggested description: `Explore thoughtful podcast conversations and grounded reflections on purpose, faith, resilience, relationships and personal growth—or bring your own question to Ask Mirror Talk.`
- Primary schema: `WebSite`, `Organization`, `PodcastSeries`

### Ask Mirror Talk

- Purpose: private reflection product
- Suggested title: `Ask Mirror Talk | Podcast Wisdom for Life’s Questions`
- Suggested description: `Ask what is on your heart and receive a thoughtful reflection grounded in real moments from the Mirror Talk podcast archive.`
- Primary schema: `WebApplication` or `SoftwareApplication`
- Do not publish personalized questions or answers in structured data.

### Episode pages

- One canonical URL per episode.
- Unique title using the human outcome before the guest name where natural.
- Editorial summary, key ideas, chapter timestamps, guest biography, citations,
  transcript or substantial edited notes, and related-topic links.
- Primary schema: `PodcastEpisode`, plus `Article` only when the page contains a substantial article.
- Append the contextual “Reflect on this conversation” bridge.

### Topic hubs

Use native WordPress categories for the first six hubs:

1. Purpose
2. Resilience
3. Relationships
4. Faith & Spirituality
5. Healing
6. Leadership

Each hub needs a unique editorial introduction, featured cornerstone content,
recent conversations and an editable contextual Ask prompt. Avoid thin tag archives.

### Insights Library

- Only editor-approved WordPress posts.
- Never mirror the raw Ask Mirror Talk database.
- Use `Article` schema for substantial reflections.
- Link every insight to its source episode and relevant topic hub.

## Internal-link rules

Every episode should link to:

- one primary topic hub;
- two or three related conversations;
- one relevant curated insight where available;
- the contextual Ask Mirror Talk reflection;
- the guest’s authoritative website when useful.

Every topic hub should link to:

- its cornerstone explanation;
- the strongest episodes for new visitors;
- recent episodes;
- a contextual Ask prompt;
- adjacent topic hubs.

## Metadata ownership

Use exactly one SEO plugin. The selected plugin owns:

- document title;
- meta description;
- canonical URL;
- robots directives;
- Open Graph and Twitter cards;
- XML sitemap;
- schema graph and breadcrumbs.

The theme provides semantic HTML and visible content but does not duplicate the
SEO plugin’s metadata.

## Indexing policy

Index:

- homepage;
- substantial episode pages;
- curated insights;
- complete topic hubs;
- About, Contact and key offering pages.

Review or noindex:

- internal search results;
- thin tag archives;
- attachment pages;
- staging environments;
- utility, account or notification pages;
- any page built from private or unreviewed user questions.

## Editorial quality gate

Before an episode article is indexed, confirm:

- one clear search intent;
- a unique title and description;
- a descriptive H1;
- original editorial copy beyond an embed;
- meaningful image alternative text;
- source episode and guest links;
- transcript or detailed show notes;
- relevant internal links;
- contextual Ask prompt;
- human review for health, trauma, faith and financial claims.

## Measurement

Track only with informed consent where required. Recommended aggregate outcomes:

- organic entrances by topic hub;
- episode-to-episode exploration rate;
- episode-to-Ask transition rate;
- Ask submission completion rate;
- source citation use;
- return visits;
- newsletter or community conversion;
- negative feedback and safety escalations as product guardrails.
