// Constants for DOM element IDs
const DOM_ELEMENTS = {
    TOPIC_LIST: 'topicList',
    QUESTION_INPUT: 'questionInput',
    RESPONSE_OUTPUT: 'responseOutput',
    ERROR_MESSAGE: 'errorMessage',
    SUBMIT_BUTTON: 'submitButton',
    HEALTH_STATUS: 'healthStatus'  // Added for health status
};

// Constants for API endpoints
const API_ENDPOINTS = {
    TOPICS: '/api/topics',
    QUERY: '/api/query',
    HEALTH: '/api/health'  // Added for health check
};

/**
 * Checks backend health by calling the health endpoint.
 * Updates the health status in the DOM.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function checkHealth() {
    const healthStatus = document.getElementById(DOM_ELEMENTS.HEALTH_STATUS);
    if (!healthStatus) {
        console.error('Health status element not found');
        return;
    }

    try {
        const response = await fetch(API_ENDPOINTS.HEALTH);
        if (!response.ok) {
            throw new Error(`Health check failed: ${response.status}`);
        }
        const data = await response.json();
        if (data.status === 'healthy') {
            healthStatus.textContent = 'Backend: Healthy';
            healthStatus.className = 'health-status healthy';
        } else {
            throw new Error('Backend unhealthy');
        }
    } catch (error) {
        console.error('Health check error:', error);
        healthStatus.textContent = 'Backend: Unhealthy';
        healthStatus.className = 'health-status unhealthy';
    }
}

/**
 * Retrieves available topics from the backend API.
 * 
 * @async
 * @returns {Promise<string[]>} Array of available topics
 * @throws {Error} If API request fails
 */
async function fetchTopics() {
    try {
        document.getElementById(DOM_ELEMENTS.SUBMIT_BUTTON).classList.add('loading');
        const response = await fetch(API_ENDPOINTS.TOPICS);
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const data = await response.json();
        return data.topics || [];
    } catch (error) {
        console.error('Error fetching topics:', error);
        return [];
    } finally {
        document.getElementById(DOM_ELEMENTS.SUBMIT_BUTTON).classList.remove('loading');
    }
}

/**
 * Initializes the topic list in the DOM by fetching and rendering available topics.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function initializeTopicList() {
    const topicList = document.getElementById(DOM_ELEMENTS.TOPIC_LIST);
    if (!topicList) {
        console.error('Topic list container not found in DOM');
        return;
    }

    try {
        topicList.innerHTML = '<div class="loading">Loading topics...</div>';
        const topics = await fetchTopics();
        topicList.innerHTML = '';
        topics.forEach(topic => {
            const topicElement = createTopicCheckbox(topic);
            topicList.appendChild(topicElement);
        });
    } catch (error) {
        console.error('Error initializing topic list:', error);
        topicList.innerHTML = '<div class="error">Failed to load topics</div>';
    }
}

/**
 * Creates a topic checkbox element with proper ARIA attributes.
 * 
 * @param {string} topic - The topic name
 * @returns {HTMLElement} The created checkbox element
 */
function createTopicCheckbox(topic) {
    const div = document.createElement('div');
    div.className = 'topic-item';
    
    const checkbox = document.createElement('input');
    checkbox.type = 'checkbox';
    checkbox.id = `topic-${topic}`;
    checkbox.name = 'topics';
    checkbox.value = topic;
    checkbox.setAttribute('aria-checked', 'false');
    
    checkbox.addEventListener('change', () => {
        checkbox.setAttribute('aria-checked', checkbox.checked.toString());
    });
    
    const label = document.createElement('label');
    label.htmlFor = `topic-${topic}`;
    label.className = 'topic-label';
    label.textContent = topic;
    
    div.appendChild(checkbox);
    div.appendChild(label);
    return div;
}

/**
 * Submits a query to the backend API with optional topic filtering.
 * 
 * @async
 * @returns {Promise<void>}
 */
async function submitQuery() {
    const questionInput = document.getElementById(DOM_ELEMENTS.QUESTION_INPUT);
    const responseOutput = document.getElementById(DOM_ELEMENTS.RESPONSE_OUTPUT);
    const errorMessage = document.getElementById(DOM_ELEMENTS.ERROR_MESSAGE);
    const submitButton = document.getElementById(DOM_ELEMENTS.SUBMIT_BUTTON);

    if (!questionInput || !responseOutput || !submitButton) {
        console.error('Required DOM elements not found');
        return;
    }

    if (errorMessage) {
        errorMessage.style.display = 'none';
        errorMessage.setAttribute('aria-hidden', 'true');
    }

    const question = questionInput.value.trim();
    if (!question) {
        responseOutput.textContent = 'Please enter a question.';
        return;
    }

    try {
        submitButton.disabled = true;
        submitButton.classList.add('loading');
        responseOutput.textContent = 'Processing your query...';

        const selectedTopics = Array.from(
            document.querySelectorAll('input[name="topics"]:checked')
        ).map(checkbox => checkbox.value);

        const response = await fetch(API_ENDPOINTS.QUERY, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ 
                question, 
                topics: selectedTopics 
            })
        });

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        const data = await response.json();
        responseOutput.textContent = data.answer || 'No answer received';
    } catch (error) {
        console.error('Error submitting query:', error);
        responseOutput.textContent = 'Error processing your query. Please try again.';
        
        if (errorMessage) {
            errorMessage.textContent = error.message;
            errorMessage.style.display = 'block';
            errorMessage.setAttribute('aria-hidden', 'false');
        }
    } finally {
        submitButton.disabled = false;
        submitButton.classList.remove('loading');
    }
}

/**
 * Initializes the application when the DOM is fully loaded.
 */
document.addEventListener('DOMContentLoaded', () => {
    initializeTopicList();
    checkHealth(); // Initial health check
    setInterval(checkHealth, 60000); // Check every 60s
});