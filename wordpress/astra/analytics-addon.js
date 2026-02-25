/**
 * Analytics Add-on for Ask Mirror Talk Widget v3.4.0
 * 
 * Adds citation click tracking and feedback without changing existing widget code.
 * Captures qa_log_id from:
 *   1. SSE streaming (via window._amtLastQALogId set by the main widget)
 *   2. Non-streaming fetch (intercepted JSON response)
 *   3. WordPress AJAX wrapper responses
 */

(function() {
    'use strict';
    
    const API_BASE_URL = 'https://ask-mirror-talk-production.up.railway.app';
    let currentQALogId = null;
    
    // Store original fetch at module scope so trackCitationClick and submitFeedback can use it
    const originalFetch = window.fetch.bind(window);
    
    // Wait for DOM to be ready
    function init() {
        console.log('✅ Ask Mirror Talk Analytics Add-on v3.4.0 loaded');
        
        // Intercept fetch calls to capture qa_log_id from non-streaming responses
        interceptFetch();
        
        // Watch for qa_log_id from SSE streaming (set on window by main widget)
        watchForStreamingQALogId();
        
        // Watch for citation links being added to the DOM
        observeDOM();
    }
    
    /**
     * Poll for window._amtLastQALogId which is set by the main widget
     * after an SSE streaming answer completes (the "done" event).
     * This is the PRIMARY path — SSE is the default answer flow.
     */
    function watchForStreamingQALogId() {
        let lastSeen = null;
        
        // Use a MutationObserver on the output element to detect when streaming ends
        // (citations appear after the answer is done streaming)
        const checkGlobal = () => {
            const globalId = window._amtLastQALogId;
            if (globalId && globalId !== lastSeen) {
                lastSeen = globalId;
                currentQALogId = globalId;
                console.log('✅ QA Session ID captured from SSE stream:', currentQALogId);
                
                // Citations are rendered by the main widget; add tracking after a short delay
                setTimeout(() => {
                    addCitationTracking();
                    addFeedbackButtons();
                }, 500);
            }
        };
        
        // Poll every 500ms — lightweight and reliable
        setInterval(checkGlobal, 500);
    }
    
    // Store the qa_log_id when a non-streaming question is answered
    function interceptFetch() {
        window.fetch = function(...args) {
            return originalFetch(...args).then(response => {
                const url = typeof args[0] === 'string' ? args[0] : (args[0]?.url || '');
                
                // Only intercept non-streaming /ask or WordPress AJAX calls (not /ask/stream)
                const isNonStreamingAsk = (url.includes('/ask') && !url.includes('/ask/stream')) || 
                    (url.includes('admin-ajax.php') && args[1]?.body && 
                     typeof args[1].body === 'string' && args[1].body.includes('ask_mirror_talk'));
                
                if (isNonStreamingAsk) {
                    // Clone so the original consumer isn't affected
                    const clonedResponse = response.clone();
                    clonedResponse.json().then(data => {
                        // Handle WordPress AJAX wrapper: {success: true, data: {qa_log_id: ...}}
                        const qaData = data.data || data;
                        if (qaData.qa_log_id) {
                            currentQALogId = qaData.qa_log_id;
                            console.log('✅ QA Session ID captured from fetch:', currentQALogId);
                            
                            setTimeout(() => {
                                addCitationTracking();
                                addFeedbackButtons();
                            }, 1000);
                        }
                    }).catch(() => {
                        // Response wasn't JSON (e.g. streaming) — ignore silently
                    });
                }
                
                return response;
            });
        };
    }
    
    // Observe DOM changes to detect when citations are rendered
    function observeDOM() {
        let debounceTimer = null;
        let isProcessing = false;
        const observer = new MutationObserver((mutations) => {
            // Skip mutations triggered by our own DOM changes
            if (isProcessing) return;
            
            const hasCitations = mutations.some(mutation =>
                Array.from(mutation.addedNodes).some(node =>
                    node.nodeType === 1 && (
                        (node.classList && (
                            node.classList.contains('citation-link') ||
                            node.classList.contains('citation-item')
                        )) ||
                        (node.querySelector && node.querySelector('.citation-link'))
                    )
                )
            );
            
            if (hasCitations && currentQALogId) {
                // Debounce: wait for all citations to be added before processing
                clearTimeout(debounceTimer);
                debounceTimer = setTimeout(() => {
                    isProcessing = true;
                    addCitationTracking();
                    addFeedbackButtons();
                    isProcessing = false;
                }, 300);
            }
        });
        
        // Start observing
        observer.observe(document.body, {
            childList: true,
            subtree: true
        });
    }
    
    /**
     * Add click tracking to all citation links
     */
    function addCitationTracking() {
        // Find all citation links - they have data-episode-id attribute
        const citationLinks = document.querySelectorAll('a[data-episode-id]:not([data-tracking-enabled]), .citation-link:not([data-tracking-enabled])');
        
        if (citationLinks.length === 0) return;
        
        citationLinks.forEach(link => {
            link.setAttribute('data-tracking-enabled', 'true');
            
            link.addEventListener('click', function(e) {
                // Get episode_id and timestamp from data attributes
                const episodeId = this.dataset.episodeId;
                const timestamp = this.dataset.timestamp || null;
                
                if (episodeId && currentQALogId) {
                    trackCitationClick(episodeId, timestamp);
                }
            });
        });
        
        console.log(`✅ Citation tracking added to ${citationLinks.length} links`);
    }
    
    /**
     * Track a citation click
     */
    async function trackCitationClick(episodeId, timestamp = null) {
        if (!currentQALogId) {
            console.warn('⚠️ No QA log ID available for tracking');
            return;
        }
        
        try {
            const payload = {
                qa_log_id: currentQALogId,
                episode_id: parseInt(episodeId)
            };
            
            if (timestamp !== null) {
                payload.timestamp = parseFloat(timestamp);
            }
            
            await originalFetch(`${API_BASE_URL}/api/citation/click`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });
            
            console.log('✅ Citation click tracked:', { episodeId, timestamp });
            
        } catch (error) {
            console.error('❌ Citation tracking failed:', error);
        }
    }
    
    /**
     * Add feedback buttons to the answer container
     */
    function addFeedbackButtons() {
        // Find the citations container - feedback goes after citations
        const citationsContainer = document.querySelector('.ask-mirror-talk-citations');
        if (!citationsContainer) {
            console.warn('⚠️ Citations container not found for feedback buttons');
            console.warn('Available containers:', {
                askMirrorTalk: document.querySelector('.ask-mirror-talk'),
                citations: document.querySelector('#ask-mirror-talk-citations'),
                response: document.querySelector('.ask-mirror-talk-response')
            });
            return;
        }
        
        // Check if feedback section already exists
        if (document.getElementById('amt-feedback-section')) {
            return;
        }
        
        // Create feedback section
        const feedbackHTML = `
            <div id="amt-feedback-section" class="amt-feedback-section">
                <div class="amt-feedback-question">
                    Was this answer helpful?
                </div>
                <div class="amt-feedback-buttons">
                    <button class="amt-feedback-btn amt-feedback-positive" data-type="positive">
                        👍 Yes, helpful
                    </button>
                    <button class="amt-feedback-btn amt-feedback-negative" data-type="negative">
                        👎 Not helpful
                    </button>
                </div>
                <div class="amt-feedback-thanks">
                    ✅ Thank you for your feedback!
                </div>
            </div>
        `;
        
        citationsContainer.insertAdjacentHTML('beforeend', feedbackHTML);
        
        // Add click handlers
        document.querySelectorAll('.amt-feedback-btn').forEach(btn => {
            btn.addEventListener('click', function() {
                const feedbackType = this.dataset.type;
                submitFeedback(feedbackType);
            });
        });
        
        console.log('✅ Feedback buttons added');
    }
    
    /**
     * Submit user feedback
     */
    async function submitFeedback(feedbackType) {
        if (!currentQALogId) {
            console.warn('⚠️ No QA log ID available for feedback');
            return;
        }
        
        try {
            await originalFetch(`${API_BASE_URL}/api/feedback`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    qa_log_id: currentQALogId,
                    feedback_type: feedbackType,
                    rating: feedbackType === 'positive' ? 5 : 1
                })
            });
            
            console.log('✅ Feedback submitted:', feedbackType);
            
            // Show thank you message
            const buttonsDiv = document.querySelector('.amt-feedback-buttons');
            const thanksDiv = document.querySelector('.amt-feedback-thanks');
            
            if (buttonsDiv) buttonsDiv.style.display = 'none';
            if (thanksDiv) {
                thanksDiv.style.display = 'block';
                thanksDiv.textContent = feedbackType === 'positive' 
                    ? '✅ Thank you! Glad we could help.' 
                    : '✅ Thank you for your feedback. We\'ll work to improve.';
            }
            
        } catch (error) {
            console.error('❌ Feedback submission failed:', error);
        }
    }
    
    /**
     * Extract episode ID from citation element
     */
    function extractEpisodeIdFromText(element) {
        // Try to find episode_id from nearby elements or data attributes
        const citationCard = element.closest('[data-episode-id]');
        if (citationCard) {
            return citationCard.dataset.episodeId;
        }
        
        // Look for episode ID in sibling elements
        const container = element.closest('.citation-item, .episode-item');
        if (container) {
            const idElement = container.querySelector('[data-episode-id]');
            if (idElement) return idElement.dataset.episodeId;
        }
        
        return null;
    }
    
    // Initialize when DOM is ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
})();
