/**
 * Ask Mirror Talk - WordPress Widget Analytics Tracking
 * 
 * This code adds citation click tracking and user feedback to the existing widget.
 * Add this to your WordPress widget's JavaScript file.
 * 
 * Version: 2.0 (Analytics Edition)
 * Date: February 20, 2026
 */

(function() {
    'use strict';
    
    const API_BASE_URL = 'https://ask-mirror-talk-production.up.railway.app';
    
    // Store current QA session for tracking
    let currentQALogId = null;
    
    /**
     * Enhanced askQuestion function with analytics tracking
     */
    async function askQuestion(questionText) {
        // Show loading state
        showLoading();
        
        try {
            const response = await fetch(`${API_BASE_URL}/ask`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ question: questionText })
            });
            
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            
            const data = await response.json();
            
            // ✨ NEW: Store qa_log_id for tracking
            currentQALogId = data.qa_log_id;
            console.log('QA Session ID:', currentQALogId);
            
            // Display the answer
            displayAnswer(data);
            
            // ✨ NEW: Initialize tracking on citations
            initializeCitationTracking();
            
            // ✨ NEW: Show feedback buttons
            showFeedbackButtons();
            
        } catch (error) {
            console.error('Error asking question:', error);
            showError('Sorry, something went wrong. Please try again.');
        }
    }
    
    /**
     * Display the answer and citations
     */
    function displayAnswer(data) {
        const answerContainer = document.getElementById('amt-answer-container');
        if (!answerContainer) return;
        
        // Build HTML for answer
        let html = `
            <div class="amt-answer-section">
                <h3>Answer:</h3>
                <div class="amt-answer-text">${data.answer}</div>
            </div>
        `;
        
        // Build HTML for citations
        if (data.citations && data.citations.length > 0) {
            html += `
                <div class="amt-citations-section">
                    <h4>📚 Related Episodes (${data.citations.length}):</h4>
                    <div class="amt-citations-list">
            `;
            
            data.citations.forEach((citation, index) => {
                const timestamp = formatTimestamp(citation.timestamp_start_seconds);
                const episodeUrl = citation.episode_url || citation.audio_url;
                
                html += `
                    <div class="amt-citation-item">
                        <div class="amt-citation-number">${index + 1}</div>
                        <div class="amt-citation-content">
                            <a href="${episodeUrl}" 
                               class="amt-citation-link" 
                               data-episode-id="${citation.episode_id}"
                               data-timestamp="${citation.timestamp_start_seconds}"
                               target="_blank"
                               rel="noopener noreferrer">
                                <strong>${citation.episode_title}</strong>
                            </a>
                            <div class="amt-citation-timestamp">
                                ⏱️ Start at ${timestamp}
                            </div>
                            <div class="amt-citation-excerpt">
                                "${citation.text.substring(0, 150)}..."
                            </div>
                        </div>
                    </div>
                `;
            });
            
            html += `
                    </div>
                </div>
            `;
        }
        
        // ✨ NEW: Add feedback section
        html += `
            <div class="amt-feedback-section" id="amt-feedback-section" style="display: none;">
                <div class="amt-feedback-question">Was this answer helpful?</div>
                <div class="amt-feedback-buttons">
                    <button class="amt-feedback-btn amt-feedback-positive" data-type="positive">
                        👍 Yes, helpful
                    </button>
                    <button class="amt-feedback-btn amt-feedback-negative" data-type="negative">
                        👎 Not helpful
                    </button>
                </div>
                <div class="amt-feedback-thanks" style="display: none;">
                    ✅ Thank you for your feedback!
                </div>
            </div>
        `;
        
        answerContainer.innerHTML = html;
        answerContainer.style.display = 'block';
    }
    
    /**
     * ✨ NEW: Initialize click tracking on all citation links
     */
    function initializeCitationTracking() {
        const citationLinks = document.querySelectorAll('.amt-citation-link');
        
        citationLinks.forEach(link => {
            link.addEventListener('click', function(e) {
                // Don't prevent default - let the link work normally
                
                const episodeId = parseInt(this.dataset.episodeId);
                const timestamp = parseFloat(this.dataset.timestamp) || null;
                
                // Track the click asynchronously (fire and forget)
                trackCitationClick(episodeId, timestamp);
            });
        });
    }
    
    /**
     * ✨ NEW: Track citation click
     */
    async function trackCitationClick(episodeId, timestamp = null) {
        if (!currentQALogId) {
            console.warn('No QA log ID available for tracking');
            return;
        }
        
        try {
            const payload = {
                qa_log_id: currentQALogId,
                episode_id: episodeId
            };
            
            // Include timestamp if available
            if (timestamp !== null) {
                payload.timestamp = timestamp;
            }
            
            await fetch(`${API_BASE_URL}/api/citation/click`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(payload)
            });
            
            console.log('✅ Citation click tracked:', { episodeId, timestamp });
            
        } catch (error) {
            // Fail silently - don't disrupt user experience
            console.error('Citation tracking failed:', error);
        }
    }
    
    /**
     * ✨ NEW: Show feedback buttons
     */
    function showFeedbackButtons() {
        const feedbackSection = document.getElementById('amt-feedback-section');
        if (feedbackSection) {
            feedbackSection.style.display = 'block';
            
            // Initialize feedback button listeners
            const feedbackBtns = document.querySelectorAll('.amt-feedback-btn');
            feedbackBtns.forEach(btn => {
                btn.addEventListener('click', function() {
                    const feedbackType = this.dataset.type;
                    submitFeedback(feedbackType);
                });
            });
        }
    }
    
    /**
     * ✨ NEW: Submit user feedback
     */
    async function submitFeedback(feedbackType) {
        if (!currentQALogId) {
            console.warn('No QA log ID available for feedback');
            return;
        }
        
        try {
            await fetch(`${API_BASE_URL}/api/feedback`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    qa_log_id: currentQALogId,
                    feedback_type: feedbackType,
                    rating: feedbackType === 'positive' ? 5 : 1
                })
            });
            
            console.log('✅ Feedback submitted:', feedbackType);
            
            // Show thank you message and hide buttons
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
            console.error('Feedback submission failed:', error);
        }
    }
    
    /**
     * Format seconds to MM:SS
     */
    function formatTimestamp(seconds) {
        if (!seconds) return '0:00';
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}:${secs.toString().padStart(2, '0')}`;
    }
    
    /**
     * Show loading state
     */
    function showLoading() {
        const answerContainer = document.getElementById('amt-answer-container');
        if (answerContainer) {
            answerContainer.innerHTML = `
                <div class="amt-loading">
                    <div class="amt-spinner"></div>
                    <p>Thinking...</p>
                </div>
            `;
            answerContainer.style.display = 'block';
        }
    }
    
    /**
     * Show error message
     */
    function showError(message) {
        const answerContainer = document.getElementById('amt-answer-container');
        if (answerContainer) {
            answerContainer.innerHTML = `
                <div class="amt-error">
                    <p>⚠️ ${message}</p>
                </div>
            `;
        }
    }
    
    // Export functions for use in your widget
    window.AskMirrorTalk = {
        askQuestion: askQuestion,
        trackCitationClick: trackCitationClick,
        submitFeedback: submitFeedback
    };
    
    // Initialize on DOM ready
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
    
    function init() {
        console.log('Ask Mirror Talk Analytics Tracking initialized');
        
        // Hook up to your existing question form
        const questionForm = document.getElementById('amt-question-form');
        const questionInput = document.getElementById('amt-question-input');
        
        if (questionForm && questionInput) {
            questionForm.addEventListener('submit', function(e) {
                e.preventDefault();
                const question = questionInput.value.trim();
                if (question) {
                    askQuestion(question);
                }
            });
        }
    }
    
})();
