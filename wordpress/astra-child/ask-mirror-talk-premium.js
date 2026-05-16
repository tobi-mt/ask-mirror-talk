/**
 * Ask Mirror Talk — Premium Features
 * v5.9.17
 * 
 * Implements:
 * - Track A: User Experience (Question coaching, Onboarding, Response formatting)
 * - Track B: Engagement (Conversational memory, Pattern recognition, Progress viz)
 * - Track C: Technical Foundation (Offline mode, Local-first, Export/import)
 * - Track D: Retention & Growth (Notification intelligence, Insight library)
 */

(function() {
  'use strict';

  console.log('✨ Ask Mirror Talk Premium Features v5.9.18 loaded');

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK C: TECHNICAL FOUNDATION - DATA LAYER (IndexedDB)
  // ═══════════════════════════════════════════════════════════════

  const DB_NAME = 'AskMirrorTalkDB';
  const DB_VERSION = 1;
  let db = null;

  /**
   * Initialize IndexedDB for local-first architecture
   */
  function initDatabase() {
    return new Promise((resolve, reject) => {
      if (db) return resolve(db);

      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        db = request.result;
        resolve(db);
      };

      request.onupgradeneeded = (event) => {
        const database = event.target.result;

        // Reflections store
        if (!database.objectStoreNames.contains('reflections')) {
          const reflectionsStore = database.createObjectStore('reflections', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          reflectionsStore.createIndex('timestamp', 'timestamp', { unique: false });
          reflectionsStore.createIndex('theme', 'theme', { unique: false });
          reflectionsStore.createIndex('emotion', 'emotion', { unique: false });
          reflectionsStore.createIndex('starred', 'starred', { unique: false });
        }

        // Insights library
        if (!database.objectStoreNames.contains('insights')) {
          const insightsStore = database.createObjectStore('insights', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          insightsStore.createIndex('timestamp', 'timestamp', { unique: false });
          insightsStore.createIndex('reflectionId', 'reflectionId', { unique: false });
          insightsStore.createIndex('tags', 'tags', { unique: false, multiEntry: true });
        }

        // Pattern recognition cache
        if (!database.objectStoreNames.contains('patterns')) {
          const patternsStore = database.createObjectStore('patterns', { keyPath: 'type' });
        }

        // Engagement metrics
        if (!database.objectStoreNames.contains('engagement')) {
          const engagementStore = database.createObjectStore('engagement', { 
            keyPath: 'date' 
          });
        }

        // Offline queue
        if (!database.objectStoreNames.contains('offlineQueue')) {
          const queueStore = database.createObjectStore('offlineQueue', { 
            keyPath: 'id', 
            autoIncrement: true 
          });
          queueStore.createIndex('timestamp', 'timestamp', { unique: false });
        }
      };
    });
  }

  /**
   * Save reflection to local database
   */
  async function saveReflection(data) {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['reflections'], 'readwrite');
        const store = transaction.objectStore('reflections');
        
        const reflection = {
          question: data.question,
          answer: data.answer,
          citations: data.citations || [],
          theme: detectTheme(data.question),
          emotion: detectEmotion(data.question),
          timestamp: Date.now(),
          starred: false,
          metadata: data.metadata || {}
        };

        const request = store.add(reflection);
        
        request.onsuccess = () => {
          updateEngagementMetrics();
          updatePatternCache();
          resolve(request.result);
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to save reflection:', error);
      return null;
    }
  }

  /**
   * Get reflection history (last N reflections)
   */
  async function getReflectionHistory(limit = 10) {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['reflections'], 'readonly');
        const store = transaction.objectStore('reflections');
        const index = store.index('timestamp');
        const request = index.openCursor(null, 'prev');
        
        const results = [];
        request.onsuccess = (event) => {
          const cursor = event.target.result;
          if (cursor && results.length < limit) {
            results.push(cursor.value);
            cursor.continue();
          } else {
            resolve(results);
          }
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get history:', error);
      return [];
    }
  }

  /**
   * Search reflections
   */
  async function searchReflections(query) {
    try {
      await initDatabase();
      const history = await getReflectionHistory(100);
      const lowerQuery = query.toLowerCase();
      
      return history.filter(r => 
        r.question.toLowerCase().includes(lowerQuery) ||
        r.answer.toLowerCase().includes(lowerQuery)
      );
    } catch (error) {
      console.error('Failed to search reflections:', error);
      return [];
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK A: USER EXPERIENCE - QUESTION COACHING
  // ═══════════════════════════════════════════════════════════════

  const QUESTION_PATTERNS = {
    'why am i': {
      reframe: 'What am I learning about',
      reason: 'Shift from self-judgment to curiosity',
      icon: '🔄'
    },
    'what\'s wrong with': {
      reframe: 'What patterns do I notice in',
      reason: 'Move from deficit to awareness',
      icon: '🔍'
    },
    'should i': {
      reframe: 'What matters most to me about',
      reason: 'Connect to your values',
      icon: '💎'
    },
    'how do i fix': {
      reframe: 'How can I grow through',
      reason: 'See challenges as opportunities',
      icon: '🌱'
    },
    'why can\'t i': {
      reframe: 'What\'s one small step toward',
      reason: 'Break overwhelm into action',
      icon: '🪜'
    },
    'am i broken': {
      reframe: 'What am I healing in myself around',
      reason: 'You\'re not broken, you\'re evolving',
      icon: '🦋'
    },
    'why does': {
      reframe: 'What can I learn from',
      reason: 'Turn frustration into insight',
      icon: '💡'
    },
    'is it normal to': {
      reframe: 'What does it mean to me that I',
      reason: 'Honor your unique experience',
      icon: '🌟'
    }
  };

  const DEPTH_PROMPTS = [
    'What\'s underneath that feeling?',
    'What would happen if you let yourself feel this fully?',
    'What does this say about what matters to you?',
    'If this pattern could speak, what would it tell you?',
    'What are you protecting yourself from?'
  ];

  /**
   * Analyze question quality and provide coaching
   */
  function coachQuestion(question) {
    const lowerQ = question.toLowerCase();
    
    // Check for reframable patterns
    for (const [pattern, coaching] of Object.entries(QUESTION_PATTERNS)) {
      if (lowerQ.includes(pattern)) {
        return {
          type: 'reframe',
          original: question,
          suggested: coaching.reframe,
          reason: coaching.reason,
          icon: coaching.icon
        };
      }
    }

    // Check question depth (length is a proxy)
    if (question.length < 20) {
      return {
        type: 'depth',
        prompt: DEPTH_PROMPTS[Math.floor(Math.random() * DEPTH_PROMPTS.length)],
        icon: '🎯'
      };
    }

    // All good!
    if (question.length > 50) {
      return {
        type: 'encourage',
        message: 'This question feels thoughtful and specific. Beautiful.',
        icon: '✨'
      };
    }

    return null;
  }

  /**
   * Show question coaching UI
   */
  function showQuestionCoaching(coaching, inputElement) {
    if (!coaching) return;

    const coachContainer = document.querySelector('#amt-question-coach');
    if (!coachContainer) return;

    let html = '<div class="amt-question-coach-inner">';
    
    if (coaching.type === 'reframe') {
      html += `
        <span class="amt-question-coach-kicker">${coaching.icon} Try reframing</span>
        <p class="amt-question-coach-text">${coaching.reason}</p>
        <div class="amt-question-coach-actions">
          <button type="button" class="amt-question-coach-btn amt-coach-reframe-btn" data-reframe="${coaching.suggested}">
            <span class="amt-question-coach-btn-label">Suggested</span>
            <span class="amt-question-coach-btn-text">${coaching.suggested}...</span>
          </button>
          <button type="button" class="amt-question-coach-btn amt-coach-continue-btn">
            <span class="amt-question-coach-btn-label">Keep as-is</span>
            <span class="amt-question-coach-btn-text">Continue with my question</span>
          </button>
        </div>
      `;
    } else if (coaching.type === 'depth') {
      html += `
        <span class="amt-question-coach-kicker">${coaching.icon} Go deeper</span>
        <p class="amt-question-coach-text">${coaching.prompt}</p>
        <div class="amt-question-coach-actions">
          <button type="button" class="amt-question-coach-btn amt-coach-continue-btn">
            <span class="amt-question-coach-btn-label">Keep going</span>
            <span class="amt-question-coach-btn-text">I'll add more detail</span>
          </button>
        </div>
      `;
    } else if (coaching.type === 'encourage') {
      html += `
        <span class="amt-question-coach-kicker">${coaching.icon}</span>
        <p class="amt-question-coach-text">${coaching.message}</p>
      `;
    }

    html += '</div>';
    coachContainer.innerHTML = html;
    coachContainer.style.display = 'block';

    // Wire up buttons
    const reframeBtn = coachContainer.querySelector('.amt-coach-reframe-btn');
    if (reframeBtn) {
      reframeBtn.addEventListener('click', () => {
        const newStart = reframeBtn.dataset.reframe;
        const original = inputElement.value;
        const rest = original.substring(original.indexOf(' ') + 1);
        inputElement.value = `${newStart} ${rest}`;
        inputElement.focus();
        coachContainer.style.display = 'none';
      });
    }

    const continueBtn = coachContainer.querySelector('.amt-coach-continue-btn');
    if (continueBtn) {
      continueBtn.addEventListener('click', () => {
        coachContainer.style.display = 'none';
        inputElement.focus();
      });
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK B: ENGAGEMENT - PATTERN RECOGNITION
  // ═══════════════════════════════════════════════════════════════

  const THEME_KEYWORDS = {
    relationships: ['relationship', 'partner', 'love', 'family', 'friend', 'connection', 'alone', 'lonely'],
    identity: ['who am i', 'identity', 'authentic', 'myself', 'true self', 'purpose', 'meaning'],
    anxiety: ['anxious', 'worry', 'fear', 'scared', 'overwhelm', 'stress', 'panic'],
    growth: ['grow', 'change', 'better', 'improve', 'learn', 'develop', 'evolve'],
    grief: ['loss', 'grief', 'sad', 'mourn', 'miss', 'gone', 'death'],
    confidence: ['confidence', 'self-esteem', 'worth', 'value', 'enough', 'capable'],
    boundaries: ['boundary', 'boundaries', 'no', 'limit', 'protect', 'space'],
    forgiveness: ['forgive', 'forgiveness', 'let go', 'release', 'grudge', 'resentment'],
    vulnerability: ['vulnerable', 'vulnerability', 'open up', 'share', 'trust'],
    healing: ['heal', 'healing', 'recover', 'overcome', 'trauma', 'past']
  };

  const EMOTION_KEYWORDS = {
    joy: ['happy', 'joy', 'excited', 'grateful', 'blessed', 'wonderful'],
    sadness: ['sad', 'down', 'depressed', 'hopeless', 'empty', 'numb'],
    anger: ['angry', 'frustrated', 'furious', 'rage', 'mad', 'irritated'],
    fear: ['afraid', 'scared', 'terrified', 'anxious', 'worried', 'nervous'],
    shame: ['ashamed', 'embarrassed', 'guilty', 'bad', 'wrong', 'stupid'],
    confusion: ['confused', 'lost', 'uncertain', 'don\'t know', 'unclear'],
    peace: ['calm', 'peace', 'serene', 'content', 'centered', 'balanced']
  };

  /**
   * Detect primary theme from question
   */
  function detectTheme(question) {
    const lowerQ = question.toLowerCase();
    let bestMatch = { theme: 'general', score: 0 };

    for (const [theme, keywords] of Object.entries(THEME_KEYWORDS)) {
      const matches = keywords.filter(kw => lowerQ.includes(kw)).length;
      if (matches > bestMatch.score) {
        bestMatch = { theme, score: matches };
      }
    }

    return bestMatch.theme;
  }

  /**
   * Detect primary emotion from question
   */
  function detectEmotion(question) {
    const lowerQ = question.toLowerCase();
    let bestMatch = { emotion: 'neutral', score: 0 };

    for (const [emotion, keywords] of Object.entries(EMOTION_KEYWORDS)) {
      const matches = keywords.filter(kw => lowerQ.includes(kw)).length;
      if (matches > bestMatch.score) {
        bestMatch = { emotion, score: matches };
      }
    }

    return bestMatch.emotion;
  }

  /**
   * Analyze patterns in reflection history
   */
  async function analyzePatterns() {
    const history = await getReflectionHistory(50);
    
    // Theme frequency
    const themeCount = {};
    const emotionCount = {};
    const timeOfDay = { morning: 0, afternoon: 0, evening: 0, night: 0 };

    history.forEach(r => {
      // Count themes
      themeCount[r.theme] = (themeCount[r.theme] || 0) + 1;
      
      // Count emotions
      emotionCount[r.emotion] = (emotionCount[r.emotion] || 0) + 1;
      
      // Time of day patterns
      const hour = new Date(r.timestamp).getHours();
      if (hour >= 5 && hour < 12) timeOfDay.morning++;
      else if (hour >= 12 && hour < 17) timeOfDay.afternoon++;
      else if (hour >= 17 && hour < 21) timeOfDay.evening++;
      else timeOfDay.night++;
    });

    // Find most common
    const topTheme = Object.entries(themeCount)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'general';
    
    const topEmotion = Object.entries(emotionCount)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'neutral';
    
    const bestTime = Object.entries(timeOfDay)
      .sort(([,a], [,b]) => b - a)[0]?.[0] || 'evening';

    return {
      topTheme,
      topEmotion,
      bestTime,
      themeCount,
      emotionCount,
      timeOfDay,
      totalReflections: history.length
    };
  }

  /**
   * Update pattern cache after each reflection
   */
  async function updatePatternCache() {
    try {
      await initDatabase();
      const patterns = await analyzePatterns();
      
      const transaction = db.transaction(['patterns'], 'readwrite');
      const store = transaction.objectStore('patterns');
      
      store.put({ type: 'current', data: patterns, updated: Date.now() });
    } catch (error) {
      console.error('Failed to update pattern cache:', error);
    }
  }

  /**
   * Get cached patterns
   */
  async function getCachedPatterns() {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['patterns'], 'readonly');
        const store = transaction.objectStore('patterns');
        const request = store.get('current');
        
        request.onsuccess = () => resolve(request.result?.data || null);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to get cached patterns:', error);
      return null;
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK B: ENGAGEMENT - CONVERSATIONAL MEMORY
  // ═══════════════════════════════════════════════════════════════

  /**
   * Generate contextual greeting based on history
   */
  async function generateContextualGreeting() {
    const history = await getReflectionHistory(5);
    
    if (history.length === 0) {
      return {
        text: 'What brings you here today?',
        type: 'first_time'
      };
    }

    const lastReflection = history[0];
    const daysSince = Math.floor((Date.now() - lastReflection.timestamp) / (1000 * 60 * 60 * 24));

    if (daysSince === 0) {
      return {
        text: `Welcome back. Still exploring ${lastReflection.theme}?`,
        type: 'same_day'
      };
    } else if (daysSince === 1) {
      return {
        text: `Good to see you return. What's on your heart today?`,
        type: 'next_day'
      };
    } else if (daysSince < 7) {
      return {
        text: `Welcome back. Last time you asked about ${lastReflection.theme}—how's that sitting with you?`,
        type: 'recent'
      };
    } else if (daysSince < 30) {
      return {
        text: `It's been a while. What's calling you back to reflection?`,
        type: 'returning'
      };
    } else {
      return {
        text: `Welcome back after some time away. What matters to you today?`,
        type: 'long_absence'
      };
    }
  }

  /**
   * Suggest follow-up questions based on history
   */
  async function suggestFollowUps() {
    const history = await getReflectionHistory(3);
    if (history.length === 0) return [];

    const lastTheme = history[0].theme;
    const themes = [...new Set(history.map(r => r.theme))];

    const suggestions = [];

    // Pattern-based follow-ups
    if (themes.length === 1) {
      suggestions.push(`What keeps bringing me back to ${lastTheme}?`);
      suggestions.push(`What am I learning about myself through ${lastTheme}?`);
    } else {
      suggestions.push(`How do ${themes[0]} and ${themes[1]} connect in my life?`);
    }

    // Time-based follow-ups
    const daysSinceFirst = Math.floor((Date.now() - history[history.length - 1].timestamp) / (1000 * 60 * 60 * 24));
    if (daysSinceFirst > 7) {
      suggestions.push('What has shifted in me over the past week?');
    }

    return suggestions.slice(0, 2);
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK A: USER EXPERIENCE - ONBOARDING FLOW
  // ═══════════════════════════════════════════════════════════════

  /**
   * Check if user needs onboarding
   */
  function needsOnboarding() {
    try {
      return !localStorage.getItem('amt_onboarded');
    } catch (e) {
      return false;
    }
  }

  /**
   * Show first-time onboarding experience
   */
  async function showOnboarding() {
    const history = await getReflectionHistory(1);
    if (history.length > 0) {
      // Already used the app, mark as onboarded
      localStorage.setItem('amt_onboarded', '1');
      return;
    }

    const container = document.querySelector('.ask-mirror-talk');
    if (!container) return;

    // Create onboarding overlay
    const overlay = document.createElement('div');
    overlay.className = 'amt-onboarding-overlay';
    overlay.innerHTML = `
      <div class="amt-onboarding-card">
        <h3>Welcome to Ask Mirror Talk</h3>
        <p>This is a space for honest self-reflection, powered by wisdom from the Mirror Talk podcast.</p>
        
        <div class="amt-onboarding-example">
          <div class="amt-onboarding-example-label">Instead of asking:</div>
          <div class="amt-onboarding-example-poor">"Why am I so bad at relationships?"</div>
          
          <div class="amt-onboarding-example-label">Try asking:</div>
          <div class="amt-onboarding-example-good">"What patterns do I notice in my relationships, and what are they teaching me?"</div>
        </div>

        <div class="amt-onboarding-promise">
          <strong>Your reflections are private.</strong> They're stored securely on your device and never shared.
        </div>

        <button type="button" class="amt-onboarding-start">Begin Your First Reflection</button>
      </div>
    `;

    container.insertBefore(overlay, container.firstChild);

    // Handle start button
    overlay.querySelector('.amt-onboarding-start').addEventListener('click', () => {
      overlay.remove();
      localStorage.setItem('amt_onboarded', '1');
      
      // Pre-fill with a gentle starter question
      const input = document.querySelector('#ask-mirror-talk-input');
      if (input) {
        input.value = 'What does it mean to live authentically?';
        input.focus();
        input.setSelectionRange(input.value.length, input.value.length);
      }
    });
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK C: TECHNICAL FOUNDATION - OFFLINE MODE
  // ═══════════════════════════════════════════════════════════════

  /**
   * Queue reflection for offline submission
   */
  async function queueOfflineReflection(question) {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['offlineQueue'], 'readwrite');
        const store = transaction.objectStore('offlineQueue');
        
        const item = {
          question,
          timestamp: Date.now(),
          status: 'pending'
        };

        const request = store.add(item);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to queue offline reflection:', error);
      return null;
    }
  }

  /**
   * Process offline queue when back online
   */
  async function processOfflineQueue() {
    try {
      await initDatabase();
      const transaction = db.transaction(['offlineQueue'], 'readwrite');
      const store = transaction.objectStore('offlineQueue');
      const request = store.getAll();

      request.onsuccess = () => {
        const items = request.result;
        items.forEach(async (item) => {
          if (item.status === 'pending') {
            // Submit via main app's submission handler
            const submitEvent = new CustomEvent('amt:offline-submit', {
              detail: { question: item.question, queueId: item.id }
            });
            document.dispatchEvent(submitEvent);
          }
        });
      };
    } catch (error) {
      console.error('Failed to process offline queue:', error);
    }
  }

  /**
   * Remove item from offline queue
   */
  async function removeFromOfflineQueue(id) {
    try {
      await initDatabase();
      const transaction = db.transaction(['offlineQueue'], 'readwrite');
      const store = transaction.objectStore('offlineQueue');
      store.delete(id);
    } catch (error) {
      console.error('Failed to remove from offline queue:', error);
    }
  }

  /**
   * Check if online and process queue
   */
  window.addEventListener('online', () => {
    console.log('✅ Back online - processing offline queue');
    processOfflineQueue();
  });

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK C: TECHNICAL FOUNDATION - EXPORT/IMPORT
  // ═══════════════════════════════════════════════════════════════

  /**
   * Export all reflections to JSON
   */
  async function exportReflections() {
    try {
      await initDatabase();
      const history = await getReflectionHistory(1000);
      const patterns = await getCachedPatterns();

      const exportData = {
        version: '5.9.18',
        exportedAt: new Date().toISOString(),
        reflections: history,
        patterns: patterns,
        stats: {
          total: history.length,
          themes: [...new Set(history.map(r => r.theme))],
          dateRange: {
            first: history[history.length - 1]?.timestamp,
            last: history[0]?.timestamp
          }
        }
      };

      const blob = new Blob([JSON.stringify(exportData, null, 2)], { 
        type: 'application/json' 
      });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `mirror-talk-reflections-${new Date().toISOString().split('T')[0]}.json`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);

      return true;
    } catch (error) {
      console.error('Failed to export reflections:', error);
      return false;
    }
  }

  /**
   * Import reflections from JSON
   */
  async function importReflections(file) {
    try {
      const text = await file.text();
      const data = JSON.parse(text);

      if (!data.version || !data.reflections) {
        throw new Error('Invalid export file format');
      }

      await initDatabase();
      const transaction = db.transaction(['reflections'], 'readwrite');
      const store = transaction.objectStore('reflections');

      let imported = 0;
      for (const reflection of data.reflections) {
        // Remove id to let auto-increment assign new ones
        delete reflection.id;
        await store.add(reflection);
        imported++;
      }

      await updatePatternCache();

      return { success: true, imported };
    } catch (error) {
      console.error('Failed to import reflections:', error);
      return { success: false, error: error.message };
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK D: RETENTION - NOTIFICATION INTELLIGENCE
  // ═══════════════════════════════════════════════════════════════

  /**
   * Track engagement times
   */
  async function updateEngagementMetrics() {
    try {
      await initDatabase();
      const today = new Date().toISOString().split('T')[0];
      const hour = new Date().getHours();

      const transaction = db.transaction(['engagement'], 'readwrite');
      const store = transaction.objectStore('engagement');
      const request = store.get(today);

      request.onsuccess = () => {
        const existing = request.result || { date: today, hours: {} };
        existing.hours[hour] = (existing.hours[hour] || 0) + 1;
        store.put(existing);
      };
    } catch (error) {
      console.error('Failed to update engagement metrics:', error);
    }
  }

  /**
   * Learn optimal notification time
   */
  async function learnOptimalTime() {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['engagement'], 'readonly');
        const store = transaction.objectStore('engagement');
        const request = store.getAll();

        request.onsuccess = () => {
          const days = request.result;
          const hourCounts = {};

          days.forEach(day => {
            Object.entries(day.hours).forEach(([hour, count]) => {
              hourCounts[hour] = (hourCounts[hour] || 0) + count;
            });
          });

          const bestHour = Object.entries(hourCounts)
            .sort(([,a], [,b]) => b - a)[0]?.[0];

          resolve(parseInt(bestHour, 10) || 19); // Default to 7 PM
        };
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to learn optimal time:', error);
      return 19; // Default to 7 PM
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK D: RETENTION - INSIGHT LIBRARY
  // ═══════════════════════════════════════════════════════════════

  /**
   * Save insight to library
   */
  async function saveInsight(text, reflectionId, tags = []) {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['insights'], 'readwrite');
        const store = transaction.objectStore('insights');
        
        const insight = {
          text,
          reflectionId,
          tags,
          timestamp: Date.now()
        };

        const request = store.add(insight);
        request.onsuccess = () => resolve(request.result);
        request.onerror = () => reject(request.error);
      });
    } catch (error) {
      console.error('Failed to save insight:', error);
      return null;
    }
  }

  /**
   * Get all insights
   */
  async function getInsights(tag = null) {
    try {
      await initDatabase();
      return new Promise((resolve, reject) => {
        const transaction = db.transaction(['insights'], 'readonly');
        const store = transaction.objectStore('insights');
        
        if (tag) {
          const index = store.index('tags');
          const request = index.getAll(tag);
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        } else {
          const request = store.getAll();
          request.onsuccess = () => resolve(request.result);
          request.onerror = () => reject(request.error);
        }
      });
    } catch (error) {
      console.error('Failed to get insights:', error);
      return [];
    }
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ TRACK B: ENGAGEMENT - PROGRESS VISUALIZATION
  // ═══════════════════════════════════════════════════════════════

  /**
   * Generate progress summary
   */
  async function generateProgressSummary() {
    const history = await getReflectionHistory(100);
    const patterns = await getCachedPatterns();

    if (history.length === 0) {
      return {
        message: 'Start your reflection journey today',
        stats: {}
      };
    }

    const daysSinceFirst = Math.floor(
      (Date.now() - history[history.length - 1].timestamp) / (1000 * 60 * 60 * 24)
    );

    const weeklyAverage = history.length / (daysSinceFirst / 7 || 1);

    let narrative = '';
    if (weeklyAverage > 5) {
      narrative = 'You\'ve built a strong reflection practice. ';
    } else if (weeklyAverage > 2) {
      narrative = 'You\'re developing a consistent rhythm. ';
    } else {
      narrative = 'Every reflection matters. ';
    }

    if (patterns && patterns.topTheme !== 'general') {
      narrative += `You often explore ${patterns.topTheme}—that theme is calling you.`;
    }

    return {
      message: narrative,
      stats: {
        total: history.length,
        daysSinceFirst,
        weeklyAverage: weeklyAverage.toFixed(1),
        topTheme: patterns?.topTheme || 'general',
        topEmotion: patterns?.topEmotion || 'neutral',
        bestTime: patterns?.bestTime || 'evening'
      }
    };
  }

  // ═══════════════════════════════════════════════════════════════
  // ██ PUBLIC API - Expose functions to main widget
  // ═══════════════════════════════════════════════════════════════

  window.AskMirrorTalkPremium = {
    // Data layer
    saveReflection,
    getReflectionHistory,
    searchReflections,
    
    // Question coaching
    coachQuestion,
    showQuestionCoaching,
    
    // Pattern recognition
    analyzePatterns,
    getCachedPatterns,
    detectTheme,
    detectEmotion,
    
    // Conversational memory
    generateContextualGreeting,
    suggestFollowUps,
    
    // Onboarding
    needsOnboarding,
    showOnboarding,
    
    // Offline mode
    queueOfflineReflection,
    processOfflineQueue,
    removeFromOfflineQueue,
    
    // Export/Import
    exportReflections,
    importReflections,
    
    // Notification intelligence
    learnOptimalTime,
    updateEngagementMetrics,
    
    // Insight library
    saveInsight,
    getInsights,
    
    // Progress visualization
    generateProgressSummary
  };

  // ═══════════════════════════════════════════════════════════════
  // ██ INITIALIZATION
  // ═══════════════════════════════════════════════════════════════

  // Wait for DOM to be fully ready
  function initializePremiumFeatures() {
    // Initialize database
    initDatabase().then(() => {
      console.log('✅ Local database initialized');
      
      // Check if onboarding needed
      if (needsOnboarding()) {
        setTimeout(showOnboarding, 500);
      }
      
      // Update engagement metrics on page load
      updateEngagementMetrics();
    }).catch(error => {
      console.error('Failed to initialize database:', error);
    });

    // Wire up question coaching to input field
    const input = document.querySelector('#ask-mirror-talk-input');
    if (input) {
      let coachingTimeout;
      input.addEventListener('input', () => {
        clearTimeout(coachingTimeout);
        coachingTimeout = setTimeout(() => {
          const coaching = coachQuestion(input.value);
          showQuestionCoaching(coaching, input);
        }, 1500); // Wait 1.5s after user stops typing
      });
    } else {
      console.warn('Premium: Input field not found - question coaching disabled');
    }

    console.log('✨ Premium features ready');
  }

  // Initialize when DOM is ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initializePremiumFeatures);
  } else {
    initializePremiumFeatures();
  }

})();
