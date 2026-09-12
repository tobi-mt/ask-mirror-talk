# Ask Mirror Talk v6.0.0 - Premium Reflection Redesign

Version 6 introduces a new, isolated premium visual system while preserving the existing DOM, JavaScript behavior, APIs, storage, analytics, and accessibility contracts.

## Visual direction

- Warm editorial palette built around deep plum, reflective cream, coral, muted gold, and restorative sage.
- Stronger typography hierarchy with an editorial serif voice for reflection content and a highly readable system sans-serif interface.
- More generous desktop spacing and intentionally compact mobile spacing.
- Layered paper surfaces, restrained glass effects, softer borders, and consistent elevation.
- Clearer active navigation, primary actions, trust panels, citations, prompts, and progress surfaces.
- Subtle panel and hover motion with full reduced-motion support.
- High-contrast focus treatment for users requesting increased contrast.

## Safety and performance

- The redesign is contained in `ask-mirror-talk-redesign.css` and loads after existing functional styles, making rollback a one-line enqueue change.
- No IDs, JavaScript selectors, event handlers, API behavior, or stored data formats changed.
- Heavy Ask Mirror Talk assets remain limited to the canonical product page and shortcode pages.
- Audio preview metadata is loaded before media playback rather than eagerly downloading episode audio.

## Product-quality improvements included

- Blocked notification instructions appear only after an explicit notification-settings action.
- Honest onboarding privacy language distinguishes local notes from anonymously processed questions.
- Programmatic onboarding prompts update all dependent UI state.
- Question-coach and citation-support grammar is improved.
- The 10,000-DAU measurement foundation and growth scorecard from v5.9.32 are included.
