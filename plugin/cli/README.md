# frame28 (CLI)

Pasos deterministas de Frame28. Las skills de Claude Code lo invocan; también sirve a mano.

```bash
uv tool install --editable .        # desde este directorio
frame28 doctor                      # qué falta (ffmpeg, Node, modelos)
frame28 prep clip.mp4 -o work       # copia 30 fps + voz normalizada
frame28 transcribe work/audio16k.wav -o work --lang es
frame28 cut plan work/words.json --audio work/voice.wav -o work/cuts.json   # silencios, muletillas, falsos arranques
frame28 cut apply work/clip.mp4 work/cuts.json --audio work/voice.wav --words work/words.json --captions work/captions.json -o work/cut
frame28 speaker work/clip.mp4       # dónde está el hablante
frame28 gestures work/clip.mp4 --words work/words.json -o work/gestures.json   # dónde señala
frame28 matte work/clip.mp4 --start 4.3 --end 6.8 -o work/alpha.webm
frame28 storyboard schema           # formato del storyboard
frame28 build storyboard.json -o project
frame28 check project && frame28 render project -o out/video.mp4
```

Requisitos: Python 3.11+, ffmpeg en PATH (o `FRAME28_FFMPEG`), Node.js 22+ (HyperFrames se descarga solo con `npx`).
