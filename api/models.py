import glob
import os
import torch
import tensorflow as tf
from facenet_pytorch import MTCNN, InceptionResnetV1
import numpy as np
from PIL import Image

mtcnn = MTCNN(image_size=178, margin=40, post_process=False)
mtcnn_face = MTCNN(image_size=160, margin=0, post_process=True)
facenet = InceptionResnetV1(pretrained="vggface2").eval()

BLOCKLIST_THRESHOLD = 0.65
BLOCKLIST_ROOT = "assets/blocklist_reference"


def _load_blocklist_embeddings():
    if not os.path.isdir(BLOCKLIST_ROOT):
        return []
    paths = []
    for person_dir in glob.glob(os.path.join(BLOCKLIST_ROOT, "*")):
        if not os.path.isdir(person_dir):
            continue
        for ext in ("*.jpg", "*.jpeg", "*.png"):
            paths += glob.glob(os.path.join(person_dir, ext))
    embeddings = []
    for path in paths:
        try:
            face = mtcnn_face(Image.open(path).convert("RGB"))
        except Exception:
            continue
        if face is None:
            continue
        with torch.no_grad():
            emb = facenet(face.unsqueeze(0)).squeeze(0).numpy()
        embeddings.append(emb)
    return embeddings


blocklist_embeddings = _load_blocklist_embeddings()


def is_blocked(image: Image.Image):
    image = image.convert("RGB")
    if max(image.size) > 1200:
        image.thumbnail((1200, 1200), Image.LANCZOS)
    face = mtcnn_face(image)
    if face is None or not blocklist_embeddings:
        return False
    with torch.no_grad():
        emb = facenet(face.unsqueeze(0)).squeeze(0).numpy()
    similarities = [
        float(np.dot(emb, ref) / (np.linalg.norm(emb) * np.linalg.norm(ref)))
        for ref in blocklist_embeddings
    ]
    return max(similarities) >= BLOCKLIST_THRESHOLD

mustache_model = tf.keras.models.load_model("models/mustache_detector_3.keras")
epic_model = tf.keras.models.load_model("models/epic_detector_4class_1.keras")


def prepare_image(image: Image.Image):
    image = image.convert("RGB")
    max_dim = 1200
    if max(image.size) > max_dim:
        image.thumbnail((max_dim, max_dim), Image.LANCZOS)
    face = mtcnn(image)
    if face is None:
        return None
    arr = face.permute(1, 2, 0).numpy().astype(np.uint8)
    return np.expand_dims(arr, axis=0)


def predict(image: Image.Image):
    img_array = prepare_image(image)
    if img_array is None:
        return None

    mustache_prob = float(mustache_model.predict(img_array, verbose=0)[0][0])
    if mustache_prob < 0.4:
        return {"mustache": False, "mustache_prob": mustache_prob}

    preds = epic_model.predict(img_array, verbose=0)[0]
    p_epic, p_medium, p_medium_thin, p_thin = float(preds[0]), float(preds[1]), float(preds[2]), float(preds[3])

    return {
        "mustache": True,
        "mustache_prob": mustache_prob,
        "p_epic": p_epic,
        "p_medium": p_medium,
        "p_medium_thin": p_medium_thin,
        "p_thin": p_thin,
    }
