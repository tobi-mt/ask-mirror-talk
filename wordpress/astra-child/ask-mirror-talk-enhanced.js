/**
 * Ask Mirror Talk - Enhanced UX Features
 * Priority 1 Quick Wins Implementation
 * 
 * Features:
 * - Ripple effects on buttons
 * - Progress indicators with time estimation
 * - Success celebrations
 * - Skeleton loaders
 * - Haptic feedback (iOS)
 * - Reading time calculation
 * - Word count during streaming
 * - Smooth animations
 * - Better mobile UX
 */

(function() {
  'use strict';

  console.log('🎨 Ask Mirror Talk Enhanced UX loaded');

  // ─── Configuration ─────────────────────────────────────────
  const CONFIG = {
    WORDS_PER_MINUTE: 200, // Average reading speed
    HAPTIC_ENABLED: 'vibrate' in navigator,
    CELEBRATION_ENABLED: true
  };

  // ─── Haptic Feedback ───────────────────────────────────────
  function triggerHaptic(pattern = [10]) {
    if (CONFIG.HAPTIC_ENABLED) {
      try {
        navigator.vibrate(pattern);
      } catch (e) {
        console.warn('Haptic feedback failed:', e);
      }
    }
  }

  // ─── Ripple Effect ─────────────────────────────────────────
  function addRippleEffect(button) {
    if (!button) return;

    button.classList.add('amt-ripple');
    
    button.addEventListener('click', function(e) {
      button.classList.remove('active');
      void button.offsetWidth; // Force reflow
      button.classList.add('active');
      
      setTimeout(() => {
        button.classList.remove('active');
      }, 600);

      triggerHaptic([5]);
    });
  }

  // ─── Calculate Reading Time ────────────────────────────────
  function calculateReadingTime(text) {
    if (!text) return 0;
    const wordCount = text.trim().split(/\s+/).length;
    const minutes = Math.ceil(wordCount / CONFIG.WORDS_PER_MINUTE);
    return minutes;
  }

  // ─── Add Reading Time Badge ────────────────────────────────
  function addReadingTimeBadge(container, text) {
    const readingTime = calculateReadingTime(text);
    if (readingTime < 1) return;

    const existingBadge = container.querySelector('.amt-reading-time');
    if (existingBadge) {
      existingBadge.remove();
    }

    const badge = document.createElement('div');
    badge.className = 'amt-reading-time amt-fade-in';
    badge.innerHTML = `
      <span class="amt-reading-time-icon">📖</span>
      <span>${readingTime} min read</span>
    `;
    
    container.insertBefore(badge, container.firstChild);
  }

  // ─── Progress Indicator ────────────────────────────────────
  function createProgressIndicator() {
    const container = document.createElement('div');
    container.className = 'amt-progress-container amt-slide-down';
    container.innerHTML = `
      <div class="amt-progress-bar">
        <div class="amt-progress-fill" style="width: 0%"></div>
      </div>
      <div class="amt-progress-text">
        <span class="amt-progress-label">Searching wisdom...</span>
        <div class="amt-progress-stats">
          <span class="amt-progress-stat">
            <span class="amt-progress-icon">⚡</span>
            <span class="amt-progress-time">~3s</span>
          </span>
        </div>
      </div>
    `;
    return container;
  }

  // ─── Update Progress ───────────────────────────────────────
  function updateProgress(container, progress, status = '', timeEstimate = '') {
    const fill = container.querySelector('.amt-progress-fill');
    const label = container.querySelector('.amt-progress-label');
    const time = container.querySelector('.amt-progress-time');
    
    if (fill) {
      fill.style.width = `${Math.min(progress, 100)}%`;
    }
    if (label && status) {
      label.textContent = status;
    }
    if (time && timeEstimate) {
      time.textContent = timeEstimate;
    }
  }

  // ─── Streaming Stats ───────────────────────────────────────
  function createStreamingStats() {
    const stats = document.createElement('div');
    stats.className = 'amt-streaming-stats';
    stats.innerHTML = `
      <div class="amt-streaming-stat">
        <span class="amt-streaming-icon">✨</span>
        <span class="amt-streaming-label">Streaming...</span>
      </div>
      <div class="amt-streaming-stat">
        <span class="amt-word-count">0 words</span>
      </div>
    `;
    return stats;
  }

  // ─── Update Word Count ─────────────────────────────────────
  function updateWordCount(statsElement, text) {
    const wordCount = text.trim().split(/\s+/).filter(w => w.length > 0).length;
    const wordCountSpan = statsElement.querySelector('.amt-word-count');
    if (wordCountSpan) {
      wordCountSpan.textContent = `${wordCount} words`;
    }
  }

  // ─── Success Celebration ───────────────────────────────────
  function celebrate(container) {
    if (!CONFIG.CELEBRATION_ENABLED) return;

    // Add celebration class
    container.classList.add('amt-celebrate');
    setTimeout(() => {
      container.classList.remove('amt-celebrate');
    }, 500);

    // Trigger haptic feedback
    triggerHaptic([10, 50, 10]);

    // Create confetti (lightweight version)
    createConfetti(container);
  }

  // ─── Create Confetti ───────────────────────────────────────
  function createConfetti(container) {
    const colors = ['#d4a574', '#8b7355', '#7ba8a8', '#6b9d6e'];
    const confettiCount = 12;

    for (let i = 0; i < confettiCount; i++) {
      const confetti = document.createElement('div');
      confetti.className = 'amt-confetti';
      confetti.style.left = `${Math.random() * 100}%`;
      confetti.style.top = '50%';
      confetti.style.background = colors[Math.floor(Math.random() * colors.length)];
      confetti.style.animationDelay = `${Math.random() * 0.3}s`;
      confetti.style.animationDuration = `${0.8 + Math.random() * 0.4}s`;
      
      container.appendChild(confetti);
      
      setTimeout(() => {
        confetti.remove();
      }, 1500);
    }
  }

  // ─── Skeleton Loader ───────────────────────────────────────
  function createSkeletonLoader() {
    const skeleton = document.createElement('div');
    skeleton.className = 'amt-skeleton-container amt-fade-in';
    skeleton.innerHTML = `
      <div class="amt-skeleton amt-skeleton-line"></div>
      <div class="amt-skeleton amt-skeleton-line"></div>
      <div class="amt-skeleton amt-skeleton-line"></div>
      <div class="amt-skeleton amt-skeleton-line"></div>
    `;
    return skeleton;
  }

  // ─── Smooth Scroll to Element ──────────────────────────────
  function smoothScrollTo(element, offset = 0) {
    if (!element) return;
    
    const elementPosition = element.getBoundingClientRect().top + window.pageYOffset;
    const offsetPosition = elementPosition - offset;

    window.scrollTo({
      top: offsetPosition,
      behavior: 'smooth'
    });
  }

  // ─── Add Tooltips ──────────────────────────────────────────
  function addTooltips() {
    // Add tooltips to citations
    document.querySelectorAll('.ask-mirror-talk-citations a').forEach(link => {
      if (!link.hasAttribute('data-tooltip')) {
        link.classList.add('amt-tooltip');
        link.setAttribute('data-tooltip', 'Listen to full episode');
      }
    });
  }

  // ─── Enhanced Citation Hover ───────────────────────────────
  function enhanceCitations() {
    document.querySelectorAll('.ask-mirror-talk-citations li').forEach(item => {
      item.addEventListener('mouseenter', function() {
        triggerHaptic([3]);
      });
    });
  }

  // ─── Local Storage for Recent Questions ────────────────────
  const RecentQuestions = {
    MAX_RECENT: 20,
    
    get() {
      try {
        const recent = localStorage.getItem('amt_recent_questions');
        return recent ? JSON.parse(recent) : [];
      } catch (e) {
        console.warn('Failed to get recent questions:', e);
        return [];
      }
    },
    
    add(question, answer, citations) {
      try {
        const recent = this.get();
        const newItem = {
          question,
          answer,
          citations,
          timestamp: Date.now()
        };
        
        recent.unshift(newItem);
        
        // Keep only MAX_RECENT items
        if (recent.length > this.MAX_RECENT) {
          recent.pop();
        }
        
        localStorage.setItem('amt_recent_questions', JSON.stringify(recent));
      } catch (e) {
        console.warn('Failed to save recent question:', e);
      }
    },
    
    clear() {
      try {
        localStorage.removeItem('amt_recent_questions');
      } catch (e) {
        console.warn('Failed to clear recent questions:', e);
      }
    }
  };

  // ─── Prefetch Resources ────────────────────────────────────
  function prefetchResources() {
    // Prefetch API endpoints for faster responses
    const API_BASE = window.AskMirrorTalk?.apiUrl || 'https://ask-mirror-talk-production.up.railway.app';
    
    // Use link rel=prefetch for DNS and preconnect
    const link = document.createElement('link');
    link.rel = 'preconnect';
    link.href = API_BASE;
    document.head.appendChild(link);
  }

  // ─── Enhanced Form Handling ────────────────────────────────
  function enhanceFormSubmission() {
    const form = document.querySelector('#ask-mirror-talk-form');
    const submitBtn = document.querySelector('#ask-mirror-talk-submit');
    const output = document.querySelector('#ask-mirror-talk-output');
    const responseContainer = document.querySelector('.ask-mirror-talk-response');
    
    if (!form || !submitBtn) return;

    // Add ripple effect to submit button
    addRippleEffect(submitBtn);

    // Store original submit handler if it exists
    const originalSubmit = form.onsubmit;

    form.addEventListener('submit', function(e) {
      // Don't prevent default - let original handler run
      
      // Add progress indicator
      setTimeout(() => {
        if (responseContainer && !responseContainer.querySelector('.amt-progress-container')) {
          const progress = createProgressIndicator();
          responseContainer.insertBefore(progress, responseContainer.firstChild);
          responseContainer.style.display = '';
          
          // Simulate progress
          let currentProgress = 0;
          const progressInterval = setInterval(() => {
            currentProgress += 5;
            if (currentProgress <= 90) {
              updateProgress(progress, currentProgress, 'Analyzing your question...', `~${Math.ceil((100 - currentProgress) / 20)}s`);
            } else {
              clearInterval(progressInterval);
            }
          }, 150);
          
          // Store interval ID for cleanup
          progress.dataset.intervalId = progressInterval;
        }
      }, 100);

      // Trigger haptic feedback
      triggerHaptic([10, 30, 10]);
    });

    // Monitor for response completion
    const observer = new MutationObserver((mutations) => {
      mutations.forEach((mutation) => {
        if (mutation.type === 'childList' || mutation.type === 'characterData') {
          const progress = responseContainer?.querySelector('.amt-progress-container');
          
          if (progress) {
            const intervalId = progress.dataset.intervalId;
            if (intervalId) {
              clearInterval(parseInt(intervalId));
            }
            
            // Complete progress
            updateProgress(progress, 100, 'Complete!', '');
            setTimeout(() => {
              progress.classList.add('amt-fade-out');
              setTimeout(() => progress.remove(), 300);
            }, 500);
          }

          // Add reading time badge
          if (output && output.textContent.trim()) {
            addReadingTimeBadge(responseContainer, output.textContent);
            
            // Celebrate on first answer
            if (!sessionStorage.getItem('amt_celebrated')) {
              celebrate(responseContainer);
              sessionStorage.setItem('amt_celebrated', 'true');
            }
            
            // Save to recent questions
            const question = document.querySelector('#ask-mirror-talk-input')?.value;
            if (question) {
              RecentQuestions.add(question, output.textContent, []);
            }
          }

          // Enhance citations
          enhanceCitations();
          addTooltips();
        }
      });
    });

    if (output) {
      observer.observe(output, {
        childList: true,
        characterData: true,
        subtree: true
      });
    }
  }

  // ─── Initialize Enhancements ───────────────────────────────
  function init() {
    console.log('🚀 Initializing UX enhancements...');

    // Prefetch resources
    prefetchResources();

    // Enhance form
    enhanceFormSubmission();

    // Add ripple effects to all buttons
    document.querySelectorAll('.amt-qotd-ask, .amt-suggestion-btn, .amt-topic-btn, .amt-followup-btn').forEach(btn => {
      addRippleEffect(btn);
    });

    // Enhance existing citations
    enhanceCitations();
    addTooltips();

    console.log('✅ UX enhancements ready');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }

  // Export utilities for external use
  window.AskMirrorTalkEnhanced = {
    triggerHaptic,
    celebrate,
    calculateReadingTime,
    RecentQuestions
  };

})();
