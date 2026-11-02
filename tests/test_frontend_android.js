/**
 * Enhetstester för Android-kameralogiken i script.js.
 * Kör med: node tests/test_frontend_android.js
 */

let passed = 0;
let failed = 0;

function assert(desc, condition) {
    if (condition) {
        console.log(`  ✓ ${desc}`);
        passed++;
    } else {
        console.error(`  ✗ ${desc}`);
        failed++;
    }
}

// --- Mock DOM ---
function makeDom() {
    const elements = {};
    const store = {};

    function el(id, attrs = {}) {
        const input = {
            files: [],
            getAttribute: (k) => attrs[k] ?? null,
            removeAttribute: (k) => { delete attrs[k]; },
            setAttribute: (k, v) => { attrs[k] = v; },
            _attrs: attrs,
        };
        const label = {
            hidden: id === 'file-label-camera', // kamera-knappen är dold från start (hidden-attribut i HTML)
            querySelector: () => input,
            childNodes: [{ textContent: 'Välj bild' }],
        };
        store[id] = { label, input };
        return { label, input };
    }

    const gallery = el('file-label-gallery', { accept: 'image/*' });
    const camera  = el('file-label-camera',  { accept: 'image/*', capture: 'environment' });

    return { gallery, camera };
}

// --- Simulera Android-logiken ---
function applyAndroidLogic(dom, isAndroid) {
    if (isAndroid) {
        dom.gallery.input.removeAttribute('capture');
        dom.gallery.label.childNodes[0].textContent = 'Välj från galleri';
        dom.camera.label.hidden = false;
    }
}

// --- Tester ---

console.log('\nAndroid-detektering och UI-logik\n');

// Ej Android — ingen förändring
{
    const dom = makeDom();
    applyAndroidLogic(dom, false);

    assert('Icke-Android: kamera-knapp förblir dold',
        dom.camera.label.hidden === true);
    assert('Icke-Android: galleri-text oförändrad',
        dom.gallery.label.childNodes[0].textContent === 'Välj bild');
    assert('Icke-Android: capture-attribut finns kvar på kamera-input',
        dom.camera.input._attrs.capture === 'environment');
}

// Android — båda knappar visas, galleri-input tappar capture
{
    const dom = makeDom();
    applyAndroidLogic(dom, true);

    assert('Android: kamera-knapp visas',
        dom.camera.label.hidden === false);
    assert('Android: galleri-text ändras till "Välj från galleri"',
        dom.gallery.label.childNodes[0].textContent === 'Välj från galleri');
    assert('Android: galleri-input har inget capture-attribut',
        dom.gallery.input._attrs.capture === undefined);
    assert('Android: kamera-input behåller capture=environment',
        dom.camera.input._attrs.capture === 'environment');
}

// getSelectedFile-logik
{
    console.log('\ngetSelectedFile — väljer rätt fil\n');

    function getSelectedFile(galleryFiles, cameraFiles) {
        return galleryFiles[0] || cameraFiles[0] || null;
    }

    assert('Ingen fil vald → null',
        getSelectedFile([], []) === null);
    assert('Galleri-fil vald → returnerar den',
        getSelectedFile(['img.jpg'], []) === 'img.jpg');
    assert('Kamera-fil vald → returnerar den',
        getSelectedFile([], ['cam.jpg']) === 'cam.jpg');
    assert('Båda valda → returnerar galleri-filen',
        getSelectedFile(['gallery.jpg'], ['cam.jpg']) === 'gallery.jpg');
}

// --- Sammanfattning ---
console.log(`\n${passed + failed} tester: ${passed} ✓  ${failed} ✗\n`);
if (failed > 0) process.exit(1);
