"""Genera secuencia PNG RGBA (y WebM VP9 con alfa) a partir de un vídeo usando RobustVideoMatting ONNX."""
import sys, os, time, subprocess
import numpy as np, cv2, onnxruntime as ort
src_video, out_dir, model = sys.argv[1], sys.argv[2], sys.argv[3]
ratio = float(sys.argv[4]) if len(sys.argv) > 4 else 0.4
os.makedirs(out_dir, exist_ok=True)
sess = ort.InferenceSession(model, providers=['CPUExecutionProvider'])
rec = [np.zeros([1, 1, 1, 1], dtype=np.float32)] * 4
ds = np.array([ratio], dtype=np.float32)
cap = cv2.VideoCapture(src_video); n = 0; t0 = time.time()
while True:
    ok, bgr = cap.read()
    if not ok: break
    rgb = cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
    x = np.transpose(rgb, (2, 0, 1))[None]
    fgr, pha, *rec = sess.run([], {'src': x, 'r1i': rec[0], 'r2i': rec[1], 'r3i': rec[2], 'r4i': rec[3], 'downsample_ratio': ds})
    fg = (np.transpose(fgr[0], (1, 2, 0)) * 255).clip(0, 255).astype(np.uint8)
    a = (pha[0, 0] * 255).clip(0, 255).astype(np.uint8)
    rgba = np.dstack([cv2.cvtColor(fg, cv2.COLOR_RGB2BGR), a])
    cv2.imwrite(os.path.join(out_dir, f"f_{n:04d}.png"), rgba); n += 1
dt = time.time() - t0
print(f"frames={n} tiempo={dt:.1f}s fps={n/dt:.1f} ratio={ratio}")
