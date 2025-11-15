"""
Production vision system with caching and rate limiting
"""
import os
import cv2
import numpy as np
import time
from typing import Dict, Optional, Tuple

from vision.regions import REGION_MAP
from vision.region_assignments import REGION_ASSIGNMENTS

# Template directory
TEMPLATE_DIR = os.path.expanduser(
    "/media/karthikeyan/705BA2D832DDA159/neo3/templates"
)

# Rate limiting
_last_screenshot_time = 0
_screenshot_cooldown = 0.3  # Seconds between screenshots

# Caching
_detection_cache = {}
_cache_ttl = 2.0  # Cache results for 2 seconds


def resolve_template_region(template_key: str) -> Optional[Tuple[int, int, int, int]]:
    """Get region coordinates for template"""
    for app, groups in REGION_ASSIGNMENTS.items():
        for group, keys in groups.items():
            if template_key in keys:
                region_name = f"{app}_{group}"
                if region_name in REGION_MAP:
                    return REGION_MAP[region_name]
    return None


def normalize_key(fname: str) -> str:
    """Normalize template filename to key"""
    key = os.path.splitext(fname)[0].lower()
    
    # Remove size/variant suffixes
    for suffix in ["_32", "_48", "_64", "_orig", "_var", "_alt"]:
        if key.endswith(suffix):
            key = key.rsplit("_", 1)[0]
    
    key = key.replace("__", "_")
    return key


def load_templates() -> Dict[str, list]:
    """Load all template images"""
    templates = {}
    
    if not os.path.isdir(TEMPLATE_DIR):
        print(f"⚠️ Template directory not found: {TEMPLATE_DIR}")
        return templates
    
    loaded = 0
    for fname in os.listdir(TEMPLATE_DIR):
        if not fname.lower().endswith(".png"):
            continue
        
        key = normalize_key(fname)
        path = os.path.join(TEMPLATE_DIR, fname)
        
        img = cv2.imread(path, cv2.IMREAD_UNCHANGED)
        if img is None:
            continue
        
        # Convert RGBA to BGR
        if img.ndim == 3 and img.shape[2] == 4:
            alpha = img[:, :, 3] / 255.0
            bg = np.zeros_like(img[:, :, :3])
            img = (img[:, :, :3] * alpha[..., None] +
                   bg * (1 - alpha[..., None])).astype(np.uint8)
        
        templates.setdefault(key, []).append(img)
        loaded += 1
    
    print(f"✅ Loaded {loaded} templates ({len(templates)} unique)")
    return templates


TEMPLATES = load_templates()

# Multi-scale matching
SCALES = (0.55, 0.75, 1.0, 1.25, 1.5)


def match_template_scaled(roi: np.ndarray, tmpl: np.ndarray) -> Tuple[Optional[Tuple[int, int]], float]:
    """Match template at multiple scales"""
    th, tw = tmpl.shape[:2]
    best_score = 0
    best_pt = None
    
    for scale in SCALES:
        nh, nw = int(th * scale), int(tw * scale)
        
        if nh < 10 or nw < 10:
            continue
        if nh > roi.shape[0] or nw > roi.shape[1]:
            continue
        
        resized = cv2.resize(tmpl, (nw, nh), interpolation=cv2.INTER_AREA)
        res = cv2.matchTemplate(roi, resized, cv2.TM_CCOEFF_NORMED)
        
        _, score, _, loc = cv2.minMaxLoc(res)
        
        if score > best_score:
            best_score = score
            best_pt = (loc[0] + nw // 2, loc[1] + nh // 2)
    
    return best_pt, best_score


def detect_all_templates(screen_bgr: np.ndarray, threshold: float = 0.75) -> Dict[str, Dict]:
    """
    Detect all templates with caching
    """
    if screen_bgr is None:
        return {}
    
    # Check cache
    cache_key = "detections"
    now = time.time()
    
    if cache_key in _detection_cache:
        cached_time, cached_result = _detection_cache[cache_key]
        if now - cached_time < _cache_ttl:
            return cached_result
    
    hits = {}
    
    # Ensure BGR
    screen = (cv2.cvtColor(screen_bgr, cv2.COLOR_GRAY2BGR)
              if screen_bgr.ndim == 2 else screen_bgr)
    
    for tkey, variants in TEMPLATES.items():
        region = resolve_template_region(tkey)
        
        if region:
            # Strict region detection
            x1, y1, x2, y2 = region
            roi = screen[y1:y2, x1:x2]
            
            if roi.size == 0:
                continue
        else:
            # Fallback: small center crop
            h, w = screen.shape[:2]
            cx, cy = w // 2, h // 2
            
            crop_factor = 0.25
            rw, rh = int(w * crop_factor), int(h * crop_factor)
            
            x1 = cx - rw // 2
            y1 = cy - rh // 2
            x2 = x1 + rw
            y2 = y1 + rh
            
            roi = screen[y1:y2, x1:x2]
        
        # Match all variants
        best_pt = None
        best_score = 0
        
        for tmpl in variants:
            pt, score = match_template_scaled(roi, tmpl)
            if score > best_score:
                best_score = score
                best_pt = pt
        
        if best_pt and best_score >= threshold:
            hits[tkey] = {
                "x": best_pt[0] + x1,
                "y": best_pt[1] + y1,
                "score": round(best_score, 3),
            }
    
    # Cache result
    _detection_cache[cache_key] = (now, hits)
    
    return hits


def capture_fullscreen(region: Optional[Tuple[int, int, int, int]] = None) -> Optional[np.ndarray]:
    """
    Capture screenshot with rate limiting
    """
    global _last_screenshot_time
    
    # Rate limit
    now = time.time()
    time_since_last = now - _last_screenshot_time
    
    if time_since_last < _screenshot_cooldown:
        sleep_time = _screenshot_cooldown - time_since_last
        time.sleep(sleep_time)
    
    try:
        import mss
        from PIL import Image
        
        with mss.mss() as sct:
            if region is None:
                mon = sct.monitors[1]
            else:
                mon = {
                    "top": region[1],
                    "left": region[0],
                    "width": region[2],
                    "height": region[3]
                }
            
            raw = sct.grab(mon)
            arr = np.array(Image.frombytes("RGB", raw.size, raw.rgb))
            
            _last_screenshot_time = time.time()
            
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
    
    except Exception as e:
        print(f"❌ Screenshot failed: {e}")
        return None


def ocr_text_from_image(img: np.ndarray, lang: str = "eng") -> str:
    """OCR helper"""
    import pytesseract
    
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    return pytesseract.image_to_string(thresh, lang=lang)