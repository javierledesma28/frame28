---
title: Installing and running Frame28 in your team
summary: For Team. What a workstation needs, how to install in ten minutes, how to edit the first video and what to do when something fails.
order: 8
minutes: 6
tier: team
---

With Team, Frame28 runs on your own computers: the video never leaves the company and the team produces without
depending on anyone. We install the first two workstations, configure your brand and train you; this article is
the cheat sheet for afterwards.

## What a workstation needs

- Windows 11 or a recent macOS. Linux works too.
- 16 GB of memory; without a dedicated graphics card everything works, just slower.
- A Claude Code account (from Anthropic) for the person who directs the edits. They decide what goes on screen;
  the engine does the rest locally.
- An internet connection to install and for the render to download its scripts. The video isn't uploaded.

## Install in ten minutes

The simplest way: open a terminal and paste the installer. It asks before every step and checks at the end.

- Windows (PowerShell): `irm https://frame28.t28.io/install.ps1 | iex`
- macOS (Terminal): `curl -fsSL https://frame28.t28.io/install.sh | bash`

It installs three supporting programs if missing (ffmpeg for video, Node.js for the render and uv for Python), the
`frame28` engine, and the plugin inside Claude Code. On Mac, the first step may ask for your computer password.

Another way, if you already use Claude Code: paste this into a session and let it do it: *"Install Frame28
following https://frame28.t28.io/instalar.md"*.

When done, in a new terminal: `frame28 doctor`. Every line with a green mark is a requirement that's present. The
two crosses on "gpu" and "RVM model" are normal: the first says there's no graphics card (slower, not worse) and
the model downloads itself the first time it's needed.

## Your brand

We leave it configured at installation. To see or change it: `frame28 brand list` and `frame28 brand show <name>`.
If you change your identity, `frame28 brand from-site https://your-website` proposes colors, font and logo from the
website and you review it together.

## Editing the first video

1. A new folder with the clip inside.
2. Open Claude Code in that folder and type: *"Here's my clip. Edit it with the {name} brand."*
3. Claude asks what it needs (destination, duration, language), transcribes, cuts silences and fillers, decides the
   text and writes the edit script. It shows it to you before rendering.
4. Review the contact sheet (`out/<name>_sheet.png`). Ask for changes in plain language: *"the title at 1:10
   shorter"*, *"remove the counter"*. Each change regenerates only what's needed.
5. For shorts: *"Give me three vertical shorts with two hooks each."* For another language: *"Spanish version."*

Timings on a laptop without a graphics card: transcribing one minute of video, about a minute; rendering one minute
of video, two or three. It can run in the background.

## When something fails

| Symptom | What to do |
|---|---|
| "frame28 is not recognized" | open a new terminal; if it persists, `uv tool update-shell` and another new terminal |
| The render has no network | the render loads some scripts from the internet the first time; connect and retry |
| A text covers the face | tell Claude: *"move the title to the other side"*; it uses the free side that `frame28 speaker` detects |
| Names transcribed wrong | pass the list of names and brands in the request; they're fixed and reused |
| Frozen video in the result | don't edit the generated HTML; ask to regenerate from the script |
| Something's off with the installation | `frame28 doctor` says what's missing and how to install it |

Email support with a two-business-day response while the fee is active. Engine updates come with `uv tool upgrade
frame28`; plugin updates, by uninstalling and reinstalling from the marketplace.

## What the team learns in the two sessions

First: shooting, the brief, the first edit end to end and how to read the contact sheet. Second: shorts with hooks,
versions in other languages, covers, and how to ask Claude for changes so they land first time.
