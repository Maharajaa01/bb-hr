"""Face detection, embedding and matching for face-verified check-in.

Detector: YuNet (OpenCV Zoo, 2023mar). Recogniser: SFace (OpenCV Zoo, 2021dec), an
ArcFace-style 128-d embedding trained with sigmoid-constrained hypersphere loss
(99.4% on LFW). Both are Apache-2.0, CPU-only and run through `cv2.dnn`, so the only
dependency is opencv-python-headless. The models are downloaded once into
`bb_academy_hrms/face_models/` and checked against pinned SHA-256 digests.

This module is pure computation: it knows nothing about employees or settings.
"""

import hashlib
import os
import threading
import urllib.request

import frappe
from frappe import _

MODEL_VERSION = "yunet-2023mar+sface-2021dec"
MODELS = {
	"detector": (
		"face_detection_yunet_2023mar.onnx",
		"https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
		"8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4",
	),
	"recognizer": (
		"face_recognition_sface_2021dec.onnx",
		"https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
		"0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79",
	),
}
MODEL_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "face_models")

MAX_SIDE = 640  # frames are analysed at most this big
DETECT_SCORE = 0.8  # YuNet confidence for "this is a face"
MIN_FACE_RATIO = 0.18  # face width / frame short side: closer than arm's length
MIN_SHARPNESS = 25.0  # variance of Laplacian on the face crop
MIN_BRIGHTNESS, MAX_BRIGHTNESS = 45, 225
FRONTAL_YAW = 0.22  # |yaw| above this is not "looking straight"

_lock = threading.Lock()
_models = None


class FaceError(frappe.ValidationError):
	pass


# ---------------------------------------------------------------------- models
def _sha256(path):
	h = hashlib.sha256()
	with open(path, "rb") as f:
		for chunk in iter(lambda: f.read(1 << 20), b""):
			h.update(chunk)
	return h.hexdigest()


def download_models(force=False):
	"""Fetch any missing model. Safe to rerun:

	bench execute bb_academy_hrms.utils.face.download_models
	"""
	os.makedirs(MODEL_DIR, exist_ok=True)
	for filename, url, digest in MODELS.values():
		path = os.path.join(MODEL_DIR, filename)
		if not force and os.path.exists(path) and _sha256(path) == digest:
			continue
		tmp = path + ".part"
		with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
			while chunk := r.read(1 << 20):
				f.write(chunk)
		if _sha256(tmp) != digest:
			os.remove(tmp)
			raise RuntimeError(f"Checksum mismatch for {filename}; refusing to use it.")
		os.replace(tmp, path)
	return MODEL_DIR


def models_available():
	return all(os.path.exists(os.path.join(MODEL_DIR, f)) for f, _u, _d in MODELS.values())


def _load():
	global _models
	if _models is None:
		import cv2

		if not models_available():
			download_models()
		det = cv2.FaceDetectorYN.create(
			os.path.join(MODEL_DIR, MODELS["detector"][0]), "", (320, 320), DETECT_SCORE, 0.3, 20
		)
		rec = cv2.FaceRecognizerSF.create(os.path.join(MODEL_DIR, MODELS["recognizer"][0]), "")
		_models = (det, rec)
	return _models


# -------------------------------------------------------------------- analysis
def _decode(content):
	import cv2
	import numpy as np

	img = cv2.imdecode(np.frombuffer(content, np.uint8), cv2.IMREAD_COLOR)
	if img is None:
		raise FaceError(_("The photo could not be read. Please retake it."))
	h, w = img.shape[:2]
	scale = MAX_SIDE / max(h, w)
	if scale < 1:
		img = cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)
	return img


def yaw_of(face):
	"""Signed head turn from YuNet landmarks: nose offset from the eye midpoint, in eye-widths.

	About 0 looking straight, roughly ±0.3-0.6 for a clear turn. On the mirrored selfie
	the client sends, turning to your own left gives a negative value.
	"""
	rx, lx, nx = face[4], face[6], face[8]
	eye_dist = max(abs(lx - rx), 1.0)
	return float((nx - (rx + lx) / 2) / eye_dist)


def analyse(content, require_frontal=True):
	"""Find exactly one usable face in an image and embed it.

	Returns dict(embedding: list[float] (L2-normalised, 128-d), yaw, score, box).
	Raises FaceError with a message the employee can act on.
	"""
	import cv2
	import numpy as np

	img = _decode(content)
	h, w = img.shape[:2]
	with _lock:  # cv2.dnn nets are not safe to share across threads
		det, rec = _load()
		det.setInputSize((w, h))
		_ok, faces = det.detect(img)
		faces = [] if faces is None else [f for f in faces if f[14] >= DETECT_SCORE]
		if not faces:
			raise FaceError(_("No face was found. Hold the phone at eye level in good light and try again."))
		faces.sort(key=lambda f: f[2] * f[3], reverse=True)
		# a second face of similar size means someone else is in the frame
		if len(faces) > 1 and faces[1][2] * faces[1][3] > 0.35 * faces[0][2] * faces[0][3]:
			raise FaceError(_("More than one face is in the picture. Make sure only you are in the frame."))
		face = faces[0]
		if face[2] < MIN_FACE_RATIO * min(w, h):
			raise FaceError(_("Your face is too far away. Bring the phone a little closer."))

		x, y, fw, fh = (int(max(0, v)) for v in face[:4])
		crop = cv2.cvtColor(img[y : y + fh, x : x + fw], cv2.COLOR_BGR2GRAY)
		if crop.size:
			brightness = float(crop.mean())
			if brightness < MIN_BRIGHTNESS:
				raise FaceError(_("It's too dark to see your face. Move to a brighter spot."))
			if brightness > MAX_BRIGHTNESS:
				raise FaceError(
					_("There's too much glare on your face. Avoid direct light behind or on you.")
				)
			if cv2.Laplacian(crop, cv2.CV_64F).var() < MIN_SHARPNESS:
				raise FaceError(_("The photo is blurry. Hold the phone still and try again."))

		yaw = yaw_of(face)
		if require_frontal and abs(yaw) > FRONTAL_YAW:
			raise FaceError(_("Look straight at the camera."))

		aligned = rec.alignCrop(img, face)
		feat = rec.feature(aligned).flatten().astype(np.float32)
	norm = float(np.linalg.norm(feat)) or 1.0
	return {
		"embedding": (feat / norm).tolist(),
		"yaw": yaw,
		"score": float(face[14]),
		"box": [float(v) for v in face[:4]],
	}


# -------------------------------------------------------------------- matching
def cosine(a, b):
	import numpy as np

	a, b = np.asarray(a, np.float32), np.asarray(b, np.float32)
	return float(a @ b / ((np.linalg.norm(a) * np.linalg.norm(b)) or 1.0))


def centroid(embeddings):
	"""Normalised mean of several embeddings: the stored template."""
	import numpy as np

	m = np.mean(np.asarray(embeddings, np.float32), axis=0)
	return (m / (np.linalg.norm(m) or 1.0)).tolist()
