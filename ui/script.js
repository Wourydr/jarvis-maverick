// ========================================================
// MAVERICK // J.A.R.V.I.S. INTERFACE CONTROLLER
// THEME : MULTI-HUD (CYAN VECTOR // IRON MAN MARK VII)
// ========================================================

let wakeActive = true;
let voiceActive = true;
let chatVisible = true;
let currentLang = 'FR';
let currentTheme = 'cyan'; // 'cyan' (HUD Matrix Vector) ou 'ironman' (Stark Mark VII)
let currentStreamingBubble = null;

// 1. HORLOGE TEMPS RÉEL HUD
function updateClock() {
    const now = new Date();
    const timeStr = now.toLocaleTimeString('fr-FR', { hour12: false });
    const clockEl = document.getElementById('clockDisplay');
    if (clockEl) clockEl.textContent = timeStr;
}
setInterval(updateClock, 1000);
updateClock();

// 2. GESTION DU THÈME HOLOGRAPHIQUE (CYAN VS IRON MAN)
let currentViewMode = 'hud'; // 'hud' ou 'webui'

function basculerModeVue(mode) {
    currentViewMode = mode;
    const btnHud = document.getElementById('btnModeHud');
    const btnWebUI = document.getElementById('btnModeWebUI');
    const studio = document.getElementById('openWebUiStudio');
    const iframe = document.getElementById('webUiIframe');
    const loader = document.getElementById('webUiLoader');

    if (mode === 'webui') {
        if (btnHud) btnHud.classList.remove('active');
        if (btnWebUI) btnWebUI.classList.add('active');
        if (studio) studio.classList.remove('hidden');
        if (loader) loader.classList.remove('fade-out');

        // Demander à Python de vérifier et démarrer Open WebUI si nécessaire
        if (window.pywebview && window.pywebview.api) {
            window.pywebview.api.demarrer_et_obtenir_webui().then(res => {
                const targetUrl = (res && res.url) ? res.url : "http://localhost:8080";
                if (iframe && (!iframe.src || iframe.src === 'about:blank' || iframe.src.indexOf('8080') === -1)) {
                    iframe.src = targetUrl;
                    iframe.onload = () => {
                        if (loader) loader.classList.add('fade-out');
                    };
                } else if (loader) {
                    loader.classList.add('fade-out');
                }
            }).catch(e => {
                if (iframe) iframe.src = "http://localhost:8080";
                setTimeout(() => { if (loader) loader.classList.add('fade-out'); }, 2500);
            });
        } else {
            if (iframe && (!iframe.src || iframe.src === 'about:blank')) {
                iframe.src = "http://localhost:8080";
                iframe.onload = () => {
                    if (loader) loader.classList.add('fade-out');
                };
            }
        }
    } else {
        if (btnHud) btnHud.classList.add('active');
        if (btnWebUI) btnWebUI.classList.remove('active');
        if (studio) studio.classList.add('hidden');
    }
}

function toggleTheme() {
    currentTheme = (currentTheme === 'cyan') ? 'ironman' : 'cyan';
    appliquerTheme(currentTheme);
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.changer_theme(currentTheme);
    }
}

window.appliquerTheme = function(theme) {
    currentTheme = (theme === 'ironman') ? 'ironman' : 'cyan';
    const statusText = document.getElementById('themeStatus');
    if (statusText) statusText.textContent = currentTheme.toUpperCase();

    const wallpaper = document.getElementById('hudWallpaper');
    const eyeGlow = document.getElementById('ironmanEyeGlow');
    const radarWeather = document.getElementById('radarWeatherAnchor');

    if (wallpaper) {
        if (currentTheme === 'cyan') {
            wallpaper.src = 'assets/hud_theme_blue_hd.jpg';
            if (eyeGlow) eyeGlow.style.display = 'none';
            if (radarWeather) radarWeather.style.display = 'none';
        } else {
            wallpaper.src = 'assets/ironman_theme_hd.jpg';
            if (eyeGlow) eyeGlow.style.display = 'block';
            if (radarWeather) radarWeather.style.display = 'block';
        }
    }
    alignCoreToHud();
};

// 3. ALIGNEMENT PIXEL-PERFECT DES ÉLÉMENTS ANIMÉS SELON LE THÈME
function alignCoreToHud() {
    const stage = document.getElementById('hudStage');
    const reactorWrap = document.getElementById('reactorCoreWrap');
    const eyeGlow = document.getElementById('ironmanEyeGlow');
    const radarWeather = document.getElementById('radarWeatherAnchor');
    const badge = document.getElementById('coreStatusBadge');
    const spectrum = document.getElementById('audioSpectrum');

    if (!stage || !reactorWrap) return;

    const w = stage.clientWidth;
    const h = stage.clientHeight;

    let origW, origH, cxRatio, cyRatio, diameterRatio;

    if (currentTheme === 'cyan') {
        // Fond Cyan Holographique HD : 1920 x 1183, Cœur centré (cx: 49.84%, cy: 49.22%)
        origW = 1920;
        origH = 1183;
        cxRatio = 0.4984;
        cyRatio = 0.4922;
        diameterRatio = 380 / 1183;
    } else {
        // Fond Iron Man HD : 1920 x 1023, Réacteur (cx: 45.57%, cy: 28.15%)
        origW = 1920;
        origH = 1023;
        cxRatio = 875 / 1920;
        cyRatio = 288 / 1023;
        diameterRatio = 365 / 1023;
    }

    const imgRatio = origW / origH;
    const screenRatio = w / h;

    let renderedW, renderedH, offsetX, offsetY;

    if (screenRatio > imgRatio) {
        renderedW = w;
        renderedH = w / imgRatio;
        offsetX = 0;
        offsetY = (h - renderedH) / 2;
    } else {
        renderedH = h;
        renderedW = h * imgRatio;
        offsetX = (w - renderedW) / 2;
        offsetY = 0;
    }

    // Positionnement du réacteur à arc central animé
    const reactorCx = offsetX + cxRatio * renderedW;
    const reactorCy = offsetY + cyRatio * renderedH;
    const reactorDiameter = diameterRatio * renderedH;

    reactorWrap.style.left = `${Math.round(reactorCx - reactorDiameter / 2)}px`;
    reactorWrap.style.top = `${Math.round(reactorCy - reactorDiameter / 2)}px`;
    reactorWrap.style.width = `${Math.round(reactorDiameter)}px`;
    reactorWrap.style.height = `${Math.round(reactorDiameter)}px`;

    // Éléments Iron Man spécifiques
    if (currentTheme === 'ironman') {
        if (eyeGlow) {
            const eyeCx = offsetX + (1490 / origW) * renderedW;
            const eyeCy = offsetY + (300 / origH) * renderedH;
            eyeGlow.style.left = `${Math.round(eyeCx)}px`;
            eyeGlow.style.top = `${Math.round(eyeCy)}px`;
            eyeGlow.style.display = 'block';
        }
        if (radarWeather) {
            const radarCx = offsetX + (1808 / origW) * renderedW;
            const radarCy = offsetY + (158 / origH) * renderedH;
            const radarDiameter = (120 / origH) * renderedH;
            radarWeather.style.left = `${Math.round(radarCx - radarDiameter / 2)}px`;
            radarWeather.style.top = `${Math.round(radarCy - radarDiameter / 2)}px`;
            radarWeather.style.width = `${Math.round(radarDiameter)}px`;
            radarWeather.style.height = `${Math.round(radarDiameter)}px`;
            radarWeather.style.display = 'block';
        }
    } else {
        if (eyeGlow) eyeGlow.style.display = 'none';
        if (radarWeather) radarWeather.style.display = 'none';
    }

    // Badge et spectre sous le réacteur
    if (badge) {
        badge.style.left = `${Math.round(reactorCx)}px`;
        badge.style.top = `${Math.round(reactorCy + reactorDiameter / 2 + 14)}px`;
        badge.style.transform = 'translateX(-50%)';
    }
    if (spectrum) {
        spectrum.style.left = `${Math.round(reactorCx)}px`;
        spectrum.style.top = `${Math.round(reactorCy + reactorDiameter / 2 + 50)}px`;
        spectrum.style.transform = 'translateX(-50%)';
    }
}

window.addEventListener('resize', alignCoreToHud);
window.addEventListener('load', () => {
    alignCoreToHud();
    const video = document.getElementById('coreVideo');
    if (video) {
        video.play().catch(e => console.log("Lecture vidéo auto démarrée:", e));
    }
});

// 3. INITIALISATION AVEC PYWEBVIEW
window.addEventListener('pywebviewready', function() {
    console.log("PyWebView Ready!");
    alignCoreToHud();
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.initialiser_ui();
    }
});

document.addEventListener('DOMContentLoaded', () => {
    const input = document.getElementById('userInput');
    if (input) {
        input.addEventListener('keypress', function(e) {
            if (e.key === 'Enter') {
                envoyerMessage();
            }
        });
    }
    alignCoreToHud();
});

// 4. ACTIONS UTILISATEUR
function envoyerMessage() {
    const input = document.getElementById('userInput');
    const texte = input.value.trim();
    if (!texte) return;

    input.value = '';
    definirEtat('reflexion', (currentLang === 'EN' ? 'MAVERICK IS PROCESSING...' : 'MAVERICK ANALYSE...'));

    if (!chatVisible) {
        toggleChatPanel();
    }

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.recevoir_message_texte(texte);
    }
}

function poserQuestionRapide(texte) {
    const input = document.getElementById('userInput');
    if (input) {
        input.value = texte;
        envoyerMessage();
    }
}

function declencherMicro() {
    definirEtat('ecoute', (currentLang === 'EN' ? 'LISTENING TO MICROPHONE...' : 'ÉCOUTE AU MICROPHONE...'));
    const micBtn = document.getElementById('micBtn');
    if (micBtn) micBtn.classList.add('listening');

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.activer_micro_manuel();
    }
}

function toggleLangue() {
    currentLang = (currentLang === 'FR') ? 'EN' : 'FR';
    window.mettreAJourLangueUI(currentLang);
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.changer_langue(currentLang.toLowerCase());
    }
}

window.mettreAJourLangueUI = function(lang) {
    currentLang = lang.toUpperCase();
    const statusText = document.getElementById('langStatus');
    if (statusText) statusText.textContent = currentLang;

    const input = document.getElementById('userInput');
    if (input) {
        if (currentLang === 'EN') {
            input.placeholder = "Give an order or say 'Hey Mav'...";
        } else {
            input.placeholder = "Donnez un ordre ou dites « Hey Mav »...";
        }
    }
};

function toggleWakeWord() {
    wakeActive = !wakeActive;
    const btn = document.getElementById('btnWake');
    const statusText = document.getElementById('wakeStatus');

    if (wakeActive) {
        btn.classList.add('active');
        statusText.textContent = 'ON';
    } else {
        btn.classList.remove('active');
        statusText.textContent = 'OFF';
    }

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.changer_wake_word(wakeActive);
    }
}

function toggleVoice() {
    voiceActive = !voiceActive;
    const btn = document.getElementById('btnVoice');
    const statusText = document.getElementById('voiceStatus');

    if (voiceActive) {
        btn.classList.add('active');
        statusText.textContent = 'ON';
    } else {
        btn.classList.remove('active');
        statusText.textContent = 'OFF';
    }

    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.changer_voix(voiceActive);
    }
}

let currentVoiceProfile = 'JARVIS'; // 'JARVIS' (IA armure Iron Man) ou 'STARK' (Tony Stark)

function toggleVoiceProfile() {
    currentVoiceProfile = (currentVoiceProfile === 'JARVIS') ? 'STARK' : 'JARVIS';
    window.mettreAJourProfilVoixUI(currentVoiceProfile);
    if (window.pywebview && window.pywebview.api) {
        window.pywebview.api.changer_profil_voix(currentVoiceProfile.toLowerCase());
    }
}

window.mettreAJourProfilVoixUI = function(profil) {
    currentVoiceProfile = profil.toUpperCase();
    const statusText = document.getElementById('voiceProfileStatus');
    if (statusText) statusText.textContent = (currentVoiceProfile === 'STARK') ? 'STARK' : 'J.A.R.V.I.S.';
};

function toggleChatPanel() {
    const panel = document.getElementById('terminalPanel');
    const btn = document.getElementById('btnChatToggle');
    if (!panel) return;

    chatVisible = !chatVisible;
    if (chatVisible) {
        panel.classList.remove('hidden');
        if (btn) btn.classList.add('active');
    } else {
        panel.classList.add('hidden');
        if (btn) btn.classList.remove('active');
    }
}

function clearChat() {
    const container = document.getElementById('chatMessages');
    if (container) {
        container.innerHTML = `
            <div class="history-separator">── VUE RÉINITIALISÉE // MÉMOIRE CONSERVÉE ──</div>
        `;
    }
}

// 5. FONCTIONS STREAMING & CONSOLE (APPELÉES DEPUIS PYTHON)

window.ajouterMessage = function(role, texte, badge = null) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    const isUser = (role.toLowerCase() === 'user' || role.toLowerCase() === 'toi');
    const bubble = document.createElement('div');
    bubble.className = `message-bubble ${isUser ? 'user' : 'assistant'}`;

    const authorName = isUser ? 'VOUS' : 'MAVERICK';
    const badgeHtml = badge ? `<span class="message-badge">${badge}</span>` : '';

    bubble.innerHTML = `
        <div class="message-header">
            <span>${authorName}</span>
            ${badgeHtml}
        </div>
        <div class="message-text">${formaterTexte(texte)}</div>
    `;

    container.appendChild(bubble);
    container.scrollTop = container.scrollHeight;
};

// Début d'un message streaming assistant
window.commencerMessageAssistant = function(badge = null) {
    const container = document.getElementById('chatMessages');
    if (!container) return;

    currentStreamingBubble = document.createElement('div');
    currentStreamingBubble.className = 'message-bubble assistant';

    const badgeHtml = badge ? `<span class="message-badge">${badge}</span>` : '';
    currentStreamingBubble.innerHTML = `
        <div class="message-header">
            <span>MAVERICK</span>
            ${badgeHtml}
        </div>
        <div class="message-text"><span class="typing-cursor">▌</span></div>
    `;

    container.appendChild(currentStreamingBubble);
    container.scrollTop = container.scrollHeight;
};

// Mise à jour continue mot par mot
window.mettreAJourMessageAssistant = function(texteComplet) {
    if (!currentStreamingBubble) {
        window.commencerMessageAssistant();
    }
    const textEl = currentStreamingBubble.querySelector('.message-text');
    if (textEl) {
        textEl.innerHTML = formaterTexte(texteComplet) + ' <span class="typing-cursor">▌</span>';
    }
    const container = document.getElementById('chatMessages');
    if (container) {
        container.scrollTop = container.scrollHeight;
    }
};

// Fin du streaming : suppression du curseur
window.terminerMessageAssistant = function() {
    if (currentStreamingBubble) {
        const cursor = currentStreamingBubble.querySelector('.typing-cursor');
        if (cursor) cursor.remove();
    }
    currentStreamingBubble = null;
};

window.definirEtat = function(etat, message) {
    const stage = document.getElementById('hudStage');
    const label = document.getElementById('coreStatusText');
    const spectrum = document.getElementById('audioSpectrum');
    const micBtn = document.getElementById('micBtn');

    if (stage) {
        stage.classList.remove('state-listening', 'state-thinking', 'state-speaking');
    }
    if (spectrum) spectrum.classList.remove('active');
    if (micBtn && etat !== 'ecoute') micBtn.classList.remove('listening');

    if (label && message) {
        label.textContent = message.toUpperCase();
    }

    if (etat === 'ecoute') {
        if (stage) stage.classList.add('state-listening');
        if (spectrum) spectrum.classList.add('active');
        if (label) label.textContent = (message || (currentLang === 'EN' ? '« HEY MAV » DETECTED // LISTENING...' : '« HEY MAV » DÉTECTÉ // JE VOUS ÉCOUTE...')).toUpperCase();
    } else if (etat === 'reflexion') {
        if (stage) stage.classList.add('state-thinking');
        if (label) label.textContent = (message || (currentLang === 'EN' ? 'NEURAL ANALYSIS...' : 'ANALYSE NEURONALE...')).toUpperCase();
    } else if (etat === 'parole') {
        if (stage) stage.classList.add('state-speaking');
        if (spectrum) spectrum.classList.add('active');
        if (label) label.textContent = (message || (currentLang === 'EN' ? 'VOCAL TRANSMISSION ACTIVE...' : 'TRANSMISSION VOCALE EN COURS...')).toUpperCase();
    } else {
        // Standby
        if (label) label.textContent = (currentLang === 'EN' ? 'MAVERICK // STANDBY // SAY "HEY MAV"' : 'MAVERICK // STANDBY // DITES « HEY MAV »');
    }
};

window.chargerHistoriqueUI = function(messages) {
    const container = document.getElementById('chatMessages');
    if (!container || !messages || messages.length === 0) {
        window.ajouterMessage('assistant', currentLang === 'EN' 
            ? "Hello Boss! I am MAVERICK, your personal holographic JARVIS interface. Say 'Hey Mav' or give me any command!" 
            : "Bonjour Patron ! Je suis MAVERICK, votre assistant personnel holographique Jarvis. Dites simplement « Hey Mav » ou posez votre question !"
        );
        return;
    }

    container.innerHTML = `<div class="history-separator">── SESSION HISTORIQUE RECHARGÉE ──</div>`;

    messages.forEach(m => {
        window.ajouterMessage(m.role, m.content, m.date || null);
    });

    window.ajouterMessage('assistant', currentLang === 'EN'
        ? "Systems online, Boss! All previous conversations are synchronized in memory. How can I assist you?"
        : "Système prêt, Patron ! Tous nos échanges passés sont mémorisés dans mon noyau. Que souhaitez-vous faire ?"
    );
};

function formaterTexte(txt) {
    if (!txt) return '';
    let f = txt.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    f = f.replace(/\*(.*?)\*/g, '<em>$1</em>');
    f = f.replace(/\n/g, '<br>');
    return f;
}
