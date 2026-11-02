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

const errorCard = document.getElementById('error-card');
const errorMsg = document.getElementById('error-msg');

const shareMobile = document.getElementById('share-mobile');

let currentCertBlob = null;
let currentFormat = 'reel'; // 'reel' eller 'post'
const formatToggle = document.getElementById('format-toggle');

async function switchFormat() {
    const file = getSelectedFile();
    if (!file) return;
    const targetEndpoint = currentFormat === 'reel' ? '/analyze/post' : '/analyze';
    const targetFormat = currentFormat === 'reel' ? 'post' : 'reel';

    formatToggle.textContent = 'Laddar...';
    const formData = new FormData();
    formData.append('file', file);
    try {
        const res = await fetch(targetEndpoint, { method: 'POST', body: formData });
        if (!res.ok) return;
        const data = await res.json();
        if (!data.certificate) return;

        const dataUrl = 'data:image/png;base64,' + data.certificate;
        resultCert.src = dataUrl;

        try {
            const byteStr = atob(data.certificate);
            const ab = new ArrayBuffer(byteStr.length);
            const ia = new Uint8Array(ab);
            for (let i = 0; i < byteStr.length; i++) ia[i] = byteStr.charCodeAt(i);
            currentCertBlob = new Blob([ab], { type: 'image/png' });
        } catch (_) {}

        currentFormat = targetFormat;
        formatToggle.textContent = currentFormat === 'reel' ? 'Byt till 4:3-format' : 'Byt till 16:9-format';
    } catch (_) {
        formatToggle.textContent = currentFormat === 'reel' ? 'Byt till 4:3-format' : 'Byt till 16:9-format';
    }
}

formatToggle.addEventListener('click', (e) => {
    e.preventDefault();
    switchFormat();
});

shareMobile.addEventListener('click', async () => {
    const shareData = { title: 'Min mustaschstyrka', text: 'Kolla min mustaschstyrka!', url: window.location.origin };
    if (currentCertBlob) {
        const file = new File([currentCertBlob], 'mustaschkraft.png', { type: 'image/png' });
        try {
            if (navigator.canShare && navigator.canShare({ files: [file] })) {
                await navigator.share({ files: [file], ...shareData });
                return;
            }
        } catch (_) {}
    }
    try { await navigator.share(shareData); } catch (_) {}
});

function showError(msg = 'Inget ansikte upptäckt') {
    errorMsg.textContent = msg;
    errorCard.hidden = false;
    setTimeout(() => { errorCard.hidden = true; }, 5000);
}

const fileInput = document.getElementById('file-input');
const fileInputCamera = document.getElementById('file-input-camera');
const fileLabelGallery = document.getElementById('file-label-gallery');
const fileLabelCamera = document.getElementById('file-label-camera');
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

const uploadCard = document.getElementById('upload-card');

// På Android: visa både "Ta foto" och "Välj från galleri"
const isAndroid = /Android/i.test(navigator.userAgent);
if (isAndroid) {
    fileLabelGallery.querySelector('input').removeAttribute('capture');
    fileLabelGallery.childNodes[0].textContent = 'Välj från galleri';
    fileLabelCamera.hidden = false;
}

function handleFileSelected(file) {
    if (!file) return;
    fileName.textContent = file.name;
    preview.src = URL.createObjectURL(file);
    preview.style.display = 'block';
    analyzeBtn.hidden = false;
    resultCard.hidden = true;
    uploadCard.classList.add('expanded');
}

fileInput.addEventListener('change', () => handleFileSelected(fileInput.files[0]));
fileInputCamera.addEventListener('change', () => handleFileSelected(fileInputCamera.files[0]));

function getSelectedFile() {
    return fileInput.files[0] || fileInputCamera.files[0] || null;
}

analyzeBtn.addEventListener('click', async () => {
    const file = getSelectedFile();
    if (!file) return;

    analyzeBtn.hidden = true;
    startLoading();

    const formData = new FormData();
    formData.append('file', file);

    try {
        const isMobileDevice = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);
        const endpoint = isMobileDevice ? '/analyze' : '/analyze/post';
        const res = await fetch(endpoint, { method: 'POST', body: formData });

        if (!res.ok) {
            if (res.status === 422) {
                showError('Inget ansikte upptäckt');
            } else if (res.status === 403) {
                showError('Den här bilden kan inte analyseras');
            } else {
                const err = await res.json();
                alert(err.detail || 'Något gick fel.');
            }
            analyzeBtn.hidden = false;
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
        const certError = document.getElementById('cert-error');
        const hashtagHint = document.getElementById('hashtag-hint');
        const isMobile = /Mobi|Android|iPhone|iPad/i.test(navigator.userAgent);

        if (data.certificate) {
            certError.hidden = true;
            const dataUrl = 'data:image/png;base64,' + data.certificate;
            resultCert.src = dataUrl;
            resultCert.style.display = 'block';

            try {
                const byteStr = atob(data.certificate);
                const ab = new ArrayBuffer(byteStr.length);
                const ia = new Uint8Array(ab);
                for (let i = 0; i < byteStr.length; i++) ia[i] = byteStr.charCodeAt(i);
                currentCertBlob = new Blob([ab], { type: 'image/png' });
            } catch (_) {
                currentCertBlob = null;
            }

            shareMobile.hidden = !isMobile;
            hashtagHint.hidden = !isMobile;

            if (isMobile) {
                certMobileHint.hidden = false;
                certDownload.hidden = true;
                currentFormat = 'reel';
                formatToggle.textContent = 'Byt till 4:3-format';
                formatToggle.hidden = false;
            } else {
                certDownload.href = dataUrl;
                certDownload.hidden = false;
                certMobileHint.hidden = true;
                formatToggle.hidden = true;
            }
        } else {
            resultCert.style.display = 'none';
            certDownload.hidden = true;
            certMobileHint.hidden = true;
            certError.hidden = false;
            shareMobile.hidden = true;
            hashtagHint.hidden = true;
            formatToggle.hidden = true;
            currentCertBlob = null;
        }

        preview.style.display = 'none';
        fileName.textContent = 'Ingen fil vald';
        analyzeBtn.hidden = true;
        uploadCard.classList.remove('expanded');

        resultCard.hidden = false;
        resultCard.scrollIntoView({ behavior: 'smooth' });

    } catch (e) {
        alert('Kunde inte nå servern.');
        analyzeBtn.hidden = false;
    } finally {
        stopLoading();
    }
});
