<p align="center">
  <br>
  <b>pack sticker images into <code>.wastickers</code> nun for WhatsApp</b>
  <br>
  <i>easily recover stickers when moving phones into installable packs </i>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.8+" src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green?style=flat-square"></a>
  <a href="https://pypi.org/project/wastickers-packer/"><img alt="PyPI" src="https://img.shields.io/pypi/v/wastickers-packer?style=flat-square"></a>
  <a href="https://pypi.org/project/wastickers-packer/"><img alt="PyPI Downloads" src="https://img.shields.io/pypi/dm/wastickers-packer?style=flat-square"></a>
  <a href="https://github.com/Yuxni/wastickers-packer"><img alt="GitHub Stars" src="https://img.shields.io/github/stars/Yuxni/wastickers-packer?style=flat-square&logo=github"></a>
  <img alt="Tests" src="https://img.shields.io/badge/tests-60_passing-brightgreen?style=flat-square">
  <img alt="Platform" src="https://img.shields.io/badge/platform-windows%20%7C%20macOS%20%7C%20linux-lightgrey?style=flat-square">
</p>

---

```bash
pip install wastickers-packer

wastickers-packer path/to/stickers -o ./packs
```

Transfer the `.wastickers` to your phone, open it with **Sticker Maker Studio** (iOS) or **WAStickerApps** (Android), and tap **Add to WhatsApp**.

---

## Features

- One command converts a folder of images into WhatsApp-ready sticker packs
- Handles WhatsApp's **3–30 sticker limit** — pads small packs, splits large ones
- Auto-resizes to **512×512**, converts to **WebP**, enforces **≤100 KB** (static) / **≤500 KB** (animated)
- Generates **96×96 tray icon** from the first sticker
- **HTML preview gallery** — `--report` flag generates a mobile-friendly index page
- Works on **Windows, macOS, Linux**

---

## Table of Contents

- [Installation](#installation)
- [Usage](#usage)
- [Why and for Who?](#why-and-for-who)
- [Why a helper app is required (iOS) & Dead End Research](#why-a-helper-app-is-required-ios--dead-end-research)
- [Options](#options)
- [WhatsApp Limitations](#whatsapp-limitations-and-how-we-handle-them)
- [Output Structure](#output-structure)
- [License](#license)

---

## Installation

```bash
pip install wastickers-packer
```

Requires **Python 3.8+**. The `Pillow` dependency is installed automatically.

---

## Usage

### Flat folder — all images become one pack

```bash
wastickers-packer stickers/ -o ./packs
```

Over 30 images? Packs split automatically ("My Pack 1", "My Pack 2", …).  
Under 3? Stickers are duplicated to reach 3.

### Subfolder mode — one pack per subfolder

```
stickers/
├── animals/       → "Animals" pack
│   ├── cat.webp
│   └── dog.webp
├── food/          → "Food" pack
│   ├── pizza.png
│   └── taco.jpg
└── reactions/     → "Reactions" pack
    ├── hug.gif
    └── wave.gif
```

```bash
wastickers-packer stickers/ -o ./packs
```

Each subfolder is a named pack. Max 30 per subfolder (error if exceeded).  
Below 3? Padded automatically.

### HTML preview

```bash
wastickers-packer path/to/stickers -o ./packs --report
```

---

## Why and for Who?

While moving from an **Android** device to an **iOS** one, I encountered this stupid issue using `MoveToIOS` (as the process is not annoying and error prone as is) — among other things, **WhatsApp Stickers do not transfer** in the move to the new phone for some reason!

On Android at least it is possible to access them via:
```
Internal Storage/Android/media/com.whatsapp/WhatsApp/Media/WhatsApp Stickers/
```

Now hear me out, I'm a bit of sticker hoarder, and even after filtering and copying them out I was still left with **300+ stickers**, not in packs nor organized of course.

So I started researching a way to just dump and install them on my new phone, and I came to the sad conclusion that there is no real way to batch up the process — and the sadder conclusion — I am the only human with that much stickers that reached this issue.

**So I decided to streamline this as much as I can.**

Basically just grab the `WhatsApp Stickers` folder from the app's files and run this tool on them to create packs out of all your stickers, send them to yourself and open them with a third-party WhatsApp Sticker app to install.

---

### Why a helper app is required (iOS) & Dead End Research

I wanted to streamline this completely and have no dependency on third-parties — upon my research a way that looked promising and was commonly talked about was leveraging the `Pasteboard` + `whatsapp://stickerPack`
- via `file`
- via `url`

There were conflicting views all over and no one place with an answer — ***so TLDR — there is no way to do this***.

WhatsApp iOS only accepts sticker packs through a **native Sticker Provider extension** — an App Store app that registers with WhatsApp via Apple's framework. There is no supported web-based, file-based, or URL-scheme installation path.

The old `whatsapp://stickerPack` pasteboard API (2018) required a custom UTI type (`net.whatsapp.third-party.sticker-pack`) and binary `NSJSONSerialization` data — neither of which can be produced from a browser or file.

Even on its last working versions, the URL scheme was fragile and frequently broken by iOS updates, WhatsApp Business conflicts, and Apple's clipboard security model (blocked on `file://` URLs entirely). Modern WhatsApp versions have removed support for it altogether.

Hopefully this serves someone.

---

## Options

| Flag              | Default                    | Description                          |
|-------------------|----------------------------|--------------------------------------|
| `-o, --output`    | `output/`                  | Output directory                     |
| `--name`          | folder name (title-cased)  | Pack name for flat folders           |
| `--publisher`     | `WhatsApp Sticker Tool`    | Publisher name in metadata           |
| `--report`        | `False`                    | Generate HTML preview gallery        |

---

## WhatsApp Limitations (and how we handle them)

| Limitation                          | Our approach                                      |
|-------------------------------------|---------------------------------------------------|
| 3–30 stickers per pack              | Below 3 → pad. Above 30 → split (flat mode).     |
| ≤100 KB per static sticker          | Quality-tuned WebP export hits the target.        |
| ≤500 KB per animated sticker        | Same, with the higher animated limit.             |
| Frame duration 10–500 ms (>8ms)     | Clamped automatically; 0ms → 100ms.               |
| Total animation ≤10 s               | Scaled proportionally if exceeded.                |
| No mixing static & animated         | Says not allowed — iOS app accepts mixed packs.   |
| 512×512 pixels                      | Auto-resized and centre-cropped.                  |
| 96×96 PNG tray icon                 | Generated from the first sticker.                 |

---

## Output Structure

```
packs/
├── animals.wastickers          ← open on phone to install
├── food.wastickers
├── reactions.wastickers
├── index.html                  ← preview page (with --report)
├── animals/
│   ├── tray.png
│   ├── sticker_01.webp
│   └── ...
├── food/
│   ├── tray.png
│   └── ...
└── reactions/
    └── ...
```

---

## License

[MIT](LICENSE)
