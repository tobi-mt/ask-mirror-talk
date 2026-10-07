# Mirror Talk Theme 8.4.3

This release improves the accuracy and reliability of the live Mirror Talk SEO control centre.

- Sends an explicit zero-length entity for Google's empty sitemap `PUT` requests, preventing HTTP 411 responses on strict HTTP/2 hosting transports.
- Separates definitive broken links from blocked, rate-limited, timed-out and transient checks.
- Treats HTTP 404/410, DNS failures and certificate hostname failures as actionable broken links.
- Treats HTTP 401/403/405/429, timeouts and server-side failures as unverified rather than falsely broken.
- Updates both Mirror Talk SEO and Mirror Talk Intelligence to use the same link-health classification.
- Retains all 8.4.2 SEO-learning brand-safety and relevance protections.
