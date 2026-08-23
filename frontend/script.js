const loadingCard = document.getElementById('loading-card');
const loadingLabel = document.getElementById('loading-label');
const bar1 = document.getElementById('bar1');
const bar2 = document.getElementById('bar2');

const LABELS = [
    'Skannar överläppsregionen...',
    'Analyserar hårdensitetsmatris...',
    'Korsreferens mot mustaschdatabasen...',
    'Beräknar mustaschkraft...',
];

let loadingInterval = null;

function startLoading() {
    loadingCard.hidden = false;
    let labelIndex = 0;
    let tick = 0;
    loadingLabel.textContent = LABELS[0];

    loadingInterval = setInterval(() => {
        tick++;
        const frac = (tick % 60) / 60;
        const v1 = frac < 0.5 ? frac * 2 : 2 - frac * 2;
        const v2 = 1 - v1;
        bar1.style.width = (v1 * 100) + '%';
        bar2.style.width = (v2 * 100) + '%';

        if (tick % 60 === 0) {
            labelIndex = (labelIndex + 1) % LABELS.length;
            loadingLabel.textContent = LABELS[labelIndex];
        }
    }, 50);
}

function stopLoading() {
    clearInterval(loadingInterval);
    loadingCard.hidden = true;
    bar1.style.width = '0%';
    bar2.style.width = '0%';
}

const videoWrapEl = document.getElementById('video-wrap');
const videoOverlayEl = document.getElementById('video-overlay');
const resultVideoEl = document.getElementById('result-video');

videoOverlayEl.addEventListener('click', () => {
    resultVideoEl.play();
    videoOverlayEl.style.display = 'none';
});

resultVideoEl.addEventListener('ended', () => {
    videoOverlayEl.textContent = '↺';
    videoOverlayEl.style.display = 'flex';
});

const fileInput = document.getElementById('file-input');
const analyzeBtn = document.getElementById('analyze-btn');
const resultCard = document.getElementById('result-card');
const resultVideo = document.getElementById('result-video');
const resultTitle = document.getElementById('result-title');
const resultStyrka = document.getElementById('result-styrka');
const resultDesc = document.getElementById('result-desc');
const resultCert = document.getElementById('result-cert');
const preview = document.getElementById('preview');
const fileName = document.getElementById('file-name');
const infoBtn = document.getElementById('info-btn');
const infoPopup = document.getElementById('info-popup');

infoBtn.addEventListener('click', () => {
    infoPopup.hidden = !infoPopup.hidden;
});

fileInput.addEventListener('change', () => {
    const file = fileInput.files[0];
    if (file) {
        fileName.textContent = file.name;
        preview.src = URL.createObjectURL(file);
        preview.style.display = 'block';
        analyzeBtn.hidden = false;
        resultCard.hidden = true;
    }
});

analyzeBtn.addEventListener('click', async () => {
    const file = fileInput.files[0];
    if (!file) return;

    analyzeBtn.hidden = true;
    startLoading();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const res = await fetch('/analyze', { method: 'POST', body: formData });

        if (!res.ok) {
            const err = await res.json();
            alert(err.detail || 'Något gick fel.');
            return;
        }

        const data = await res.json();

        resultTitle.textContent = data.title;
        resultStyrka.textContent = data.mustache ? `Mustaschstyrka: ${data.score} / 100` : '';
        resultDesc.textContent = data.description || '';

        const VIDEO_MAP = {
            'legendarisk': '/assets/abbe/video/legendarisk.mp4',
            'episk':       '/assets/abbe/video/episk.mp4',
            'respektabel': '/assets/abbe/video/respektabel.mp4',
            'lovande':     '/assets/abbe/video/lovande.mp4',
            'fjunig':      '/assets/abbe/video/fjunig.mp4',
            'ingen':       '/assets/abbe/video/ingen.mp4',
        };
        const titleLower = data.title.toLowerCase();
        const videoSrc = Object.entries(VIDEO_MAP).find(([key]) => titleLower.includes(key))?.[1];
        const videoWrap = document.getElementById('video-wrap');
        const videoOverlay = document.getElementById('video-overlay');
        if (videoSrc) {
            resultVideo.src = videoSrc;
            resultVideo.load();
            videoWrap.style.display = 'block';
            videoOverlay.style.display = 'flex';
            videoOverlay.textContent = '▶';
        } else {
            videoWrap.style.display = 'none';
        }

        const certDownload = document.getElementById('cert-download');
        const certMobileHint = document.getElementById('cert-mobile-hint');
        const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

        if (data.certificate) {
            const dataUrl = 'data:image/png;base64,' + data.certificate;
            resultCert.src = dataUrl;
            resultCert.style.display = 'block';
            if (isMobile) {
                certMobileHint.hidden = false;
                certDownload.hidden = true;
            } else {
                certDownload.href = dataUrl;
                certDownload.hidden = false;
                certMobileHint.hidden = true;
            }
        } else {
            resultCert.style.display = 'none';
            certDownload.hidden = true;
            certMobileHint.hidden = true;
        }

        preview.style.display = 'none';
        fileName.textContent = 'Ingen fil vald';

        resultCard.hidden = false;
        resultCard.scrollIntoView({ behavior: 'smooth' });

    } catch (e) {
        alert('Kunde inte nå servern.');
    } finally {
        stopLoading();
        analyzeBtn.hidden = false;
    }
});
