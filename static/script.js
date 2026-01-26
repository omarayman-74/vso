document.addEventListener('DOMContentLoaded', () => {
    const chatForm = document.getElementById('chat-form');
    const userInput = document.getElementById('user-input');
    const chatHistory = document.querySelector('.chat-history');
    const sendBtn = document.getElementById('send-btn');

    // Chat session management
    let currentSessionId = localStorage.getItem('currentSessionId') || 'default_session';
    window.currentSessionId = currentSessionId;
    // Expose necessary variables and functions to window object for global access
    window.currentLanguage = 'en';
    window.translations = {
        'en': {
            'tell_more': 'Tell me more about ',
            'tech_detail': 'Retrieve full details for unit number ',
            'show_payment': 'Show me the payment plan for unit #',
            'tech_payment': 'Show me the detailed payment plan for unit number ',
            'view_website': 'View on Website',
            'watch_video': 'Watch Video',
            'view_payment': 'View Payment Plan',
            'payment_plan': 'Payment Plan'
        },
        'ar': {
            'tell_more': 'قولي تفاصيل أكتر عن ',
            'tech_detail': 'اسأل عن التفاصيل للوحدة رقم ',
            'show_payment': 'وريني نظام السداد للوحدة رقم #',
            'tech_payment': 'عايز تفاصيل خطة الدفع للوحدة رقم ',
            'view_website': 'عرض على الموقع',
            'watch_video': 'مشاهدة الفيديو',
            'view_payment': 'عرض نظام السداد',
            'payment_plan': 'نظام السداد'
        },
        'franco': {
            'tell_more': '2oly tafaseel aktr 3an ',
            'tech_detail': 'esa2al 3an el tafaseel le el unit ra2am ',
            'show_payment': 'wareny nezam el sadad le el unit ra2am #',
            'tech_payment': '3ayez tafaseel 5otat el daf3 le el unit ra2am ',
            'view_website': '3ard 3ala el maw2e3',
            'watch_video': 'shof el video',
            'view_payment': '3ard nezam el sadad',
            'payment_plan': 'nezam el sadad'
        }
    };

    // Auto-focus input
    userInput.focus();

    // Handle form submission
    chatForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const message = userInput.value.trim();
        if (!message) return;

        // Add user message
        addMessage(message, 'user');
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: window.currentSessionId
                })
            });

            const data = await response.json();

            // Update current language from response
            if (data.detected_language) {
                window.currentLanguage = data.detected_language.toLowerCase();
                // Normalize language codes if needed
                if (window.currentLanguage === 'arabic') window.currentLanguage = 'ar';
                if (window.currentLanguage.includes('franco')) window.currentLanguage = 'franco';
            }

            // Remove typing indicator
            removeTypingIndicator(typingId);

            if (response.ok) {
                // Add assistant response (delay cache hits 0.5s for natural feel)
                if (data.cache_hit) {
                    await new Promise(r => setTimeout(r, 500));
                }
                addMessage(data.response, 'assistant', {
                    response_time_ms: data.cache_hit ? 500 : data.response_time_ms,
                    cache_hit: data.cache_hit
                });
            } else {
                const errorMsg = `⚠️ **System Error**: ${data.detail || 'Unknown error'}`;
                addMessage(errorMsg, 'assistant');
            }

        } catch (error) {
            removeTypingIndicator(typingId);
            const errorMsg = `🚫 **Connection Failed**: ${error.message}`;
            addMessage(errorMsg, 'assistant');
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    });

    // Expose handler for property clicks
    window.handlePropertyInquiry = async (unitId, title) => {
        if (userInput.disabled) return;

        // Use global translations
        const lang = window.currentLanguage || 'en';
        const t = window.translations[lang] || window.translations['en'];

        // 1. Show FRIENDLY message in UI (localized for user)
        addMessage(`${t.tell_more}${title}`, 'user');

        // 2. Send STANDARDIZED TECHNICAL query to Backend (always English for consistent processing)
        // But append language hint so backend responds in user's language
        const languageMap = { 'en': 'English', 'ar': 'Arabic', 'franco': 'Franco-Arabic' };
        const userLanguage = languageMap[lang] || 'English';
        const technicalMessage = `Retrieve full details for unit number ${unitId} from the database. [Respond in ${userLanguage}]`;

        await processMessage(technicalMessage);
    };

    async function processMessage(message) {
        userInput.value = '';
        userInput.disabled = true;
        sendBtn.disabled = true;

        // Show typing indicator
        const typingId = showTypingIndicator();

        try {
            // Check sessionId
            const sessionId = localStorage.getItem('currentSessionId') || 'default_session';

            const response = await fetch('/api/chat', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    message: message,
                    session_id: sessionId
                })
            });

            const data = await response.json();

            // Update current language from response
            if (data.detected_language) {
                window.currentLanguage = data.detected_language.toLowerCase();
                // Normalize language codes if needed
                if (window.currentLanguage === 'arabic') window.currentLanguage = 'ar';
                if (window.currentLanguage.includes('franco')) window.currentLanguage = 'franco';
            }

            // Remove typing indicator
            removeTypingIndicator(typingId);

            if (response.ok) {
                // Add assistant response (delay cache hits 0.5s for natural feel)
                if (data.cache_hit) {
                    await new Promise(r => setTimeout(r, 500));
                }
                addMessage(data.response, 'assistant', {
                    response_time_ms: data.cache_hit ? 500 : data.response_time_ms,
                    cache_hit: data.cache_hit
                });
            } else {
                const errorMsg = `⚠️ **System Error**: ${data.detail || 'Unknown error'}`;
                addMessage(errorMsg, 'assistant');
            }

        } catch (error) {
            removeTypingIndicator(typingId);
            const errorMsg = `🚫 **Connection Failed**: ${error.message}`;
            addMessage(errorMsg, 'assistant');
        } finally {
            userInput.disabled = false;
            sendBtn.disabled = false;
            userInput.focus();
        }
    }
    window.processMessage = processMessage;

    function addMessage(content, role, meta = null) {
        window.addMessage = addMessage;
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;

        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';

        if (role === 'assistant') {
            // Process content for unit detail data
            const { cleanText: textWithoutDetail, detailData } = parseUnitDetailData(content);
            // Process content for carousel data
            const { cleanText: textWithoutCarousel, carouselData } = parseCarouselData(textWithoutDetail);
            // Process remaining text for payment plan data
            const { cleanText, planData } = parsePaymentPlanData(textWithoutCarousel);

            // Render carousel if exists (before text)
            if (carouselData) {
                const carouselHTML = renderPropertyCarousel(carouselData);
                const carouselDiv = document.createElement('div');
                carouselDiv.innerHTML = carouselHTML;
                messageDiv.appendChild(carouselDiv);
            }

            // Render images inline FIRST if exists (inside message content)
            let contentHTML = '';
            if (detailData) {
                const imagesCarouselHTML = renderImagesCarousel(detailData);
                if (imagesCarouselHTML) {
                    contentHTML += imagesCarouselHTML;
                }
            }

            // Then render text content
            contentHTML += parseMarkdown(cleanText);
            contentDiv.innerHTML = contentHTML;

            if (meta && typeof meta.response_time_ms !== 'undefined') {
                const metaDiv = document.createElement('div');
                metaDiv.className = 'response-meta';
                const timeValue = Number(meta.response_time_ms) / 1000;
                const timeText = Number.isFinite(timeValue) ? `${timeValue.toFixed(2)}s` : 'n/a';
                const cacheText = meta.cache_hit ? 'cached' : '';
                metaDiv.textContent = cacheText ? `⏱ ${timeText} · ${cacheText}` : `⏱ ${timeText}`;
                contentDiv.appendChild(metaDiv);
            }

            messageDiv.appendChild(contentDiv);

            // Render action buttons (Property Link, Video Link, Payment Plan Request)
            const hasPropertyLink = detailData && detailData.property_link;
            const hasVideoLink = detailData && detailData.video_url && detailData.video_url.trim() !== '';
            const hasPaymentPlan = !!planData;
            const unitId = detailData ? detailData.unit_id : null;

            if (hasPropertyLink || hasVideoLink || hasPaymentPlan || unitId) {
                let actionsHTML = `<div class="unit-detail-actions">`;
                const t = window.translations[window.currentLanguage] || window.translations['en'];

                // Property link button (primary)
                if (hasPropertyLink) {
                    actionsHTML += `
                    <a href="${detailData.property_link}" target="_blank" class="property-link-button">
                        <span class="link-icon">🏡</span>
                        <span class="link-text">${t.view_website}</span>
                    </a>
                    `;
                }

                // Video link button (secondary)
                if (hasVideoLink) {
                    actionsHTML += `
                    <a href="${detailData.video_url}" target="_blank" class="video-link-button">
                        <span class="video-icon">▶️</span>
                        <span class="video-text">${t.watch_video}</span>
                    </a>
                    `;
                }

                // Payment Plan Request button (secondary)
                if (unitId && !hasPaymentPlan) {
                    actionsHTML += `
                    <div class="payment-request-button" onclick="requestPaymentPlan('${unitId}')">
                        <span class="link-icon">💳</span>
                        <span class="link-text">${t.view_payment}</span>
                    </div>
                    `;
                }

                // Payment Plan button (secondary)
                if (hasPaymentPlan) {
                    const ppHTML = renderPaymentPlan(planData);
                    const ppId = 'pp-' + Date.now() + Math.floor(Math.random() * 1000);

                    // We render the button here
                    actionsHTML += `
                    <div class="payment-link-button" onclick="openContentModalFromId('${ppId}')">
                        <span class="link-icon">💳</span>
                        <span class="link-text">${t.payment_plan}</span>
                    </div>
                    `;

                    // But we must append the actual content separately to the DOM
                    // We'll separate this logic: we append the content container after creating the actionsDiv
                    // For now, we store it in a way we can retrieve it.
                    // Actually, let's just append the hidden div to the messageDiv directly
                    const hiddenDiv = document.createElement('div');
                    hiddenDiv.id = ppId;
                    hiddenDiv.style.display = 'none';
                    hiddenDiv.innerHTML = ppHTML;
                    messageDiv.appendChild(hiddenDiv);
                }

                actionsHTML += `</div>`;

                const actionsDiv = document.createElement('div');
                actionsDiv.innerHTML = actionsHTML;
                messageDiv.appendChild(actionsDiv);
            }

        } else {
            contentDiv.textContent = content; // User message is plain text
            messageDiv.appendChild(contentDiv);
        }

        chatHistory.appendChild(messageDiv);
        scrollToBottom();
    }

    function parseCarouselData(text) {
        const marker = '<<PROPERTY_CAROUSEL_DATA>>';
        if (text.includes(marker)) {
            const markerIndex = text.indexOf(marker);

            // Check if marker is at the beginning (prepended)
            if (markerIndex === 0) {
                // Marker is at the start: <<MARKER>>{json}\n\ntext
                const afterMarker = text.substring(marker.length);

                // Find where JSON ends (look for }\n\n pattern or end of first complete JSON object)
                let jsonEndIndex = -1;
                let braceCount = 0;
                let inString = false;
                let escapeNext = false;

                for (let i = 0; i < afterMarker.length; i++) {
                    const char = afterMarker[i];

                    if (escapeNext) {
                        escapeNext = false;
                        continue;
                    }

                    if (char === '\\') {
                        escapeNext = true;
                        continue;
                    }

                    if (char === '"' && !escapeNext) {
                        inString = !inString;
                        continue;
                    }

                    if (!inString) {
                        if (char === '{') braceCount++;
                        if (char === '}') {
                            braceCount--;
                            if (braceCount === 0) {
                                jsonEndIndex = i + 1;
                                break;
                            }
                        }
                    }
                }

                if (jsonEndIndex > 0) {
                    const jsonString = afterMarker.substring(0, jsonEndIndex);
                    const remainingText = afterMarker.substring(jsonEndIndex).trim();

                    try {
                        const carouselData = JSON.parse(jsonString);
                        return { cleanText: remainingText, carouselData };
                    } catch (e) {
                        console.error("Failed to parse carousel JSON (prepended)", e);
                        return { cleanText: text, carouselData: null };
                    }
                }
            } else {
                // Marker is in the middle or end (appended): text\n\n<<MARKER>>{json}
                const parts = text.split(marker);
                const cleanText = parts[0].trim();
                try {
                    const carouselData = JSON.parse(parts[1]);
                    return { cleanText, carouselData };
                } catch (e) {
                    console.error("Failed to parse carousel JSON (appended)", e);
                    return { cleanText: text, carouselData: null };
                }
            }
        }
        return { cleanText: text, carouselData: null };
    }

    function parseUnitDetailData(text) {
        const startMarker = '###UNIT_DETAIL###';
        const endMarker = '###END_DETAIL###';

        if (text.includes(startMarker) && text.includes(endMarker)) {
            const startIndex = text.indexOf(startMarker);
            const endIndex = text.indexOf(endMarker);

            if (startIndex !== -1 && endIndex !== -1 && endIndex > startIndex) {
                const jsonString = text.substring(startIndex + startMarker.length, endIndex);
                const remainingText = text.substring(endIndex + endMarker.length).trim();

                try {
                    const detailData = JSON.parse(jsonString);
                    return { cleanText: remainingText, detailData };
                } catch (e) {
                    console.error("Failed to parse unit detail JSON", e);
                    return { cleanText: text, detailData: null };
                }
            }
        }
        return { cleanText: text, detailData: null };
    }

    function renderImagesCarousel(data) {
        if (!data) return '';

        // Collect all available images
        const images = [];
        if (data.unit_image && data.unit_image.trim() !== '') {
            images.push({
                url: data.unit_image,
                type: 'unit'
            });
        }
        if (data.compound_image && data.compound_image.trim() !== '') {
            images.push({
                url: data.compound_image,
                type: 'compound'
            });
        }
        // Fallback to generic image if specific ones aren't available
        if (images.length === 0 && data.image && data.image.trim() !== '') {
            images.push({
                url: data.image,
                type: 'property'
            });
        }

        // Render images horizontally inline (no separate section)
        if (images.length > 0) {
            let html = '<div class="inline-images-container">';

            images.forEach((img, index) => {
                const delay = index * 0.1;
                html += `<div class="inline-image-card" style="animation-delay: ${delay}s" onclick="openImageModal('${img.url}')"><img src="${img.url}" alt="Property Image" class="inline-image" onerror="this.parentElement.style.display='none';"></div>`;
            });

            html += '</div>';
            return html;
        }

        return '';
    }


    function renderPropertyCarousel(data) {
        if (!data || !data.items || data.items.length === 0) return '';

        // Default labels (English) if not provided
        const defaults = {
            area: "Area",
            bedrooms: "Bed",
            bathrooms: "Bath",
            price: "Price",
            delivery: "Delivery",
            status: "Status",
            developer: "Developer",
            model: "Model",
            ask_details: "Ask Details",
            view_arrow: "→",
            option: "Option",
            unit_id: "ID",
            found: "Found",
            properties: "Properties",
            currency: "EGP",
            floor: "Floor"
        };

        // Merge provided labels with defaults
        const labels = { ...defaults, ...(data.labels || {}) };

        let html = `
        <div class="property-carousel-container">
            <h2>${labels.found} ${data.count} ${labels.properties}</h2>
            <div class="property-carousel">
        `;

        data.items.forEach((item, index) => {
            // Add staggered animation delay
            const delay = index * 0.1;

            html += `
                <div class="property-card" style="animation-delay: ${delay}s" onclick="askAboutProperty('${item.unit_id}', '${item.title.replace(/'/g, "\\'")}')">
                    <div class="property-card-image-container">
                        ${item.image ?
                    `<img src="${item.image}" alt="${item.title}" class="property-card-image" onerror="this.onerror=null;this.src='https://placehold.co/300x200?text=No+Image';">` :
                    `<div class="property-card-image-placeholder"><i class="fas fa-home"></i> <span>No Image</span></div>`
                }
                        <div class="property-badge">${item.status}</div>
                    </div>
                    
                    <div class="property-card-content">
                        <div class="property-card-header">
                            <span class="property-unit-id">${labels.unit_id}: ${item.unit_id}</span>
                            <span class="property-option-label">${labels.option || 'Option'} ${item.option}</span>
                        </div>
                        
                        
                        <div class="property-card-title" title="${item.title}">${item.title}</div>
                        <div class="property-card-developer"><i class="fas fa-building"></i> ${item.developer}</div>
                        
                        ${item.has_promo && item.discount_info ? `
                            <div class="property-card-price-container">
                                <div class="property-original-price">${item.price}</div>
                                <div class="property-discounted-price">${item.discount_info.discounted_price.toLocaleString('en-US', { minimumFractionDigits: 0, maximumFractionDigits: 0 })} ${labels.currency}</div>
                                <div class="discount-badge">${item.discount_info.discount_percentage}% OFF</div>
                            </div>
                            ${item.promo_text ? `<div class="promo-text">${item.promo_text}</div>` : ''}
                        ` : `
                            <div class="property-card-price">${item.price}</div>
                        `}

                        
                        <div class="property-card-details">
                            <div class="property-detail-item">
                                <span class="property-detail-icon">📐</span>
                                <span>${item.area}</span>
                            </div>
                            <div class="property-detail-item">
                                <span class="property-detail-icon">🛏️</span>
                                <span>${item.bedrooms} ${labels.bedrooms}</span>
                            </div>
                            <div class="property-detail-item">
                                <span class="property-detail-icon">🚿</span>
                                <span>${item.bathrooms} ${labels.bathrooms}</span>
                            </div>
                            <div class="property-detail-item">
                                <span class="property-detail-icon">🏢</span>
                                <span>${labels.floor}: ${item.floor}</span>
                            </div>
                            <div class="property-detail-item">
                                <span class="property-detail-icon">📅</span>
                                <span>${item.delivery}</span>
                            </div>
                        </div>
                        
                        <div class="property-card-footer">
                            <button class="property-view-btn">
                                ${labels.ask_details} <span class="arrow">${labels.view_arrow}</span>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        });

        html += `</div></div>`;
        return html;
    }

    // ═══════════════════════════════════════════════════════════════
    // PAYMENT PLAN RENDERING
    // ═══════════════════════════════════════════════════════════════

    function parsePaymentPlanData(text) {
        const marker = '<<PAYMENT_PLAN_DATA>>';
        if (text.includes(marker)) {
            const parts = text.split(marker);
            const cleanText = parts[0].trim();
            try {
                const planData = JSON.parse(parts[1]);
                return { cleanText, planData };
            } catch (e) {
                console.error("Failed to parse payment plan JSON", e);
                return { cleanText: text, planData: null };
            }
        }
        return { cleanText: text, planData: null };
    }

    function renderPaymentPlan(data) {
        if (!data) return '';

        // Formatter helper
        const fmt = (val) => val || 'N/A';
        const isSpec = (val) => val && val !== 'Not specified';

        let html = `
        <div class="payment-plan-container">
            <div class="pp-header">
                <div class="pp-badge">Unit #${data.unit_id}</div>
                <h3>${fmt(data.compound)}</h3>
                <div class="pp-sub">${fmt(data.location)} • ${fmt(data.developer)}</div>
            </div>

            <div class="pp-grid">
                <div class="pp-card info-card">
                    <h4>Property Details</h4>
                    <div class="pp-row"><span>Area</span> <strong>${fmt(data.area)} m²</strong></div>
                    <div class="pp-row"><span>Bedrooms</span> <strong>${fmt(data.bedrooms)}</strong></div>
                    <div class="pp-row highlight"><span>Total Price</span> <strong>${fmt(data.formatted_price)}</strong></div>
                </div>

                <div class="pp-card payment-card">
                    <h4>Initial Payment</h4>
                    ${isSpec(data.down_payment.formatted) ? `
                    <div class="pp-highlight-box">
                        <span class="label">Down Payment (${data.down_payment.percentage}%)</span>
                        <span class="value">${data.down_payment.formatted}</span>
                    </div>` : ''}
                    
                    ${isSpec(data.deposit.formatted) ? `
                    <div class="pp-row border-top">
                        <span>Deposit</span>
                        <strong>${data.deposit.formatted}</strong>
                    </div>` : ''}
                </div>
            </div>
        `;

        if (data.plans && data.plans.length > 0) {
            html += `
            <div class="pp-section-title">Installment Options</div>
            <div class="pp-plans-scroll">
            `;

            data.plans.forEach(plan => {
                html += `
                <div class="pp-plan-card">
                    <div class="plan-years">${plan.years} Years</div>
                    <div class="plan-monthly">
                        <span class="amount">${plan.formatted_monthly}</span>
                        <span class="per">/ month</span>
                    </div>
                    <div class="plan-total">Total: ${plan.formatted_total}</div>
                </div>
                `;
            });

            html += `</div>`;
        } else if (isSpec(data.monthly_installment.formatted)) {
            html += `
            <div class="pp-card single-plan">
                <h4>Monthly Installment</h4>
                <div class="plan-monthly large">
                    <span class="amount">${data.monthly_installment.formatted}</span>
                </div>
            </div>
            `;
        }

        html += `</div>`;
        return html;
    }

    function showTypingIndicator() {
        const id = 'typing-' + Date.now();
        const indicator = document.createElement('div');
        indicator.className = 'message assistant';
        indicator.id = id;
        indicator.innerHTML = `
            <div class="typing-container">
                <div class="typing-indicator">
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                    <div class="typing-dot"></div>
                </div>
            </div>`;
        chatHistory.appendChild(indicator);
        scrollToBottom();
        return id;
    }

    function removeTypingIndicator(id) {
        const el = document.getElementById(id);
        if (el) el.remove();
    }

    function scrollToBottom() {
        chatHistory.scrollTop = chatHistory.scrollHeight;
    }

    function parseMarkdown(text) {
        // Simple Markdown Parser
        let html = text
            // Headers
            .replace(/^### (.*$)/gim, '<h3>$1</h3>')
            .replace(/^## (.*$)/gim, '<h2>$1</h2>')
            .replace(/^# (.*$)/gim, '<h1>$1</h1>')
            // Bold
            .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
            // Italic
            .replace(/\*(.*?)\*/gim, '<em>$1</em>')
            // Links
            .replace(/\[([^\]]+)\]\(([^)]+)\)/gim, '<a href="$2" target="_blank">$1</a>')
            // Lists
            .replace(/^\s*-\s+(.*$)/gim, '<ul><li>$1</li></ul>')
            // Fix nested lists
            .replace(/<\/ul>\s*<ul>/gim, '')
            // Paragraphs (double newlines)
            .replace(/\n\n/gim, '</p><p>')
            // Line breaks
            .replace(/\n/gim, '<br>');

        return `<p>${html}</p>`;
    }
});

// Global function for property card click
function askAboutProperty(unitId, title) {
    if (window.handlePropertyInquiry) {
        window.handlePropertyInquiry(unitId, title);
    }
}

// Global function for payment plan request
async function requestPaymentPlan(unitId) {
    const userInput = document.getElementById('user-input');
    const sendBtn = document.getElementById('send-btn');

    if (userInput.disabled) return;

    // Use global translations
    const lang = window.currentLanguage || 'en';
    const t = window.translations[lang] || window.translations['en'];

    // 1. Show FRIENDLY message in UI (localized for user)
    window.addMessage(`${t.show_payment}${unitId}`, 'user');

    // 2. Send STANDARDIZED TECHNICAL query to Backend (always English for consistent processing)
    // But append language hint so backend responds in user's language
    const languageMap = { 'en': 'English', 'ar': 'Arabic', 'franco': 'Franco-Arabic' };
    const userLanguage = languageMap[lang] || 'English';
    const technicalMessage = `Show me the detailed payment plan for unit number ${unitId}. [Respond in ${userLanguage}]`;

    await window.processMessage(technicalMessage);
}

// Global functions for image modal
function openImageModal(imageUrl) {
    // Create modal if it doesn't exist
    let modal = document.getElementById('imageModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'imageModal';
        modal.className = 'image-modal';
        modal.innerHTML = `
            <span class="image-modal-close" onclick="closeImageModal()">&times;</span>
            <img class="image-modal-content" id="modalImage">
        `;
        document.body.appendChild(modal);

        // Close modal when clicking outside the image
        modal.onclick = function (event) {
            if (event.target === modal) {
                closeImageModal();
            }
        };
    }

    // Set image and show modal
    document.getElementById('modalImage').src = imageUrl;
    modal.classList.add('active');
    document.body.style.overflow = 'hidden'; // Prevent background scrolling
}

function closeImageModal() {
    const modal = document.getElementById('imageModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = ''; // Restore scrolling
    }
}

// Close modal with Escape key
document.addEventListener('keydown', function (event) {
    if (event.key === 'Escape') {
        closeImageModal();
    }
});


// ═══════════════════════════════════════════════════════════════
// CONTENT MODAL LOGIC (Payment Plans, etc)
// ═══════════════════════════════════════════════════════════════

function openContentModalFromId(contentId) {
    const contentElement = document.getElementById(contentId);
    if (!contentElement) {
        console.error("Content not found for modal:", contentId);
        return;
    }

    // Create modal if it doesn't exist
    let modal = document.getElementById('contentModal');
    if (!modal) {
        modal = document.createElement('div');
        modal.id = 'contentModal';
        modal.className = 'content-modal';
        modal.innerHTML = `
            <div class="content-modal-body">
                <span class="content-modal-close" onclick="closeContentModal()">&times;</span>
                <div id="contentModalContainer"></div>
            </div>
        `;
        document.body.appendChild(modal);

        // Close modal when clicking outside the content
        modal.onclick = function (event) {
            if (event.target === modal) {
                closeContentModal();
            }
        };

        // Close with Escape key
        document.addEventListener('keydown', function (event) {
            if (event.key === 'Escape' && modal.classList.contains('active')) {
                closeContentModal();
            }
        });
    }

    const container = document.getElementById('contentModalContainer');
    container.innerHTML = contentElement.innerHTML;

    modal.classList.add('active');
    document.body.style.overflow = 'hidden';
}

function closeContentModal() {
    const modal = document.getElementById('contentModal');
    if (modal) {
        modal.classList.remove('active');
        document.body.style.overflow = '';
    }
}
