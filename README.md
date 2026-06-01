<p align="center">
  <br>
  <b>Turn sticker images into <code>.wastickers</code> files for WhatsApp</b>
</p>

<p align="center">
  <a href="https://www.python.org/downloads/"><img alt="Python 3.8+" src="https://img.shields.io/badge/python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white"></a>
  <a href="LICENSE"><img alt="License: MIT" src="https://img.shields.io/badge/license-MIT-green?style=flat-square"></a>
  <img alt="Tests" src="https://img.shields.io/badge/tests-60_passing-brightgreen?style=flat-square">
  <img alt="Platform" src="https://img.shields.io/badge/platform-windows%20%7C%20macOS%20%7C%20linux-lightgrey?style=flat-square">
</p>

---

```bash
pip install .
whatsappsticker path/to/stickers -o ./packs
```

Transfer the `.wastickers` to your phone, open it with **Sticker Maker Studio** (`iOS`) or **WAStickerApps** (Android), and tap **Add to WhatsApp**. Done.

---



## Installation

Requires **Python 3.8+** and **Pillow**.

```bash
pip install .
```



---

## Features

- **📦 Flat mode** — all images in one folder become a pack
- **📁 Subfolder mode** — each subfolder becomes its own named pack
- **🔁 Auto-padding** — fewer than 3 stickers? Duplicated to reach minimum `(WA limtation)`
- **✂️ Auto-split** — more than 30? Split into numbered packs `(WA limtation)`
- **📄 HTML preview** — generate a mobile-friendly gallery page


---

## Why and for Who?

While moving from an `Android` device to an `IOS` one,  I encountered this stupid issue using `MoveToIOS` (as the process is not annoying and error prune as is) - among other things, **`WhatsappStickers` do not transfer** in the move to the new phone for some reason!

now here me out, im a bit of sticker hoarder, and even after filtering them out I was still left with 300, not in packs or organized of course

so I started researching a way to just dump them on my new phone, and I came to the sad conclusion that the there is no real way to batch up the process - and the sadder conclusion - i am the only human with that much stickers that reached this issue

**so I decided to streamline this [as much as i can](#how-it-works)**

basicly just grab the WhatsAppStickers folder from the app's files
and run this tool on them to create packs out of all your stickers, send them to your self and open them with a Third-Party Whatsapp Sticker app to install 

---


### Why a helper app is required (iOS) & Dead End Research

I wanted to streamline this complelty and have no dependency on third-parties - upon my research a way that looked promising and was commonly talked about was leverging the `Pasteboard` + `whatsapp://stickerPack`
- via `file`
- via `url` 
  
there were conflicting views all over and no one place with an answer - ***so TLDR - there is no way to do this***

WhatsApp iOS only accepts sticker packs through a **native Sticker Provider extension** — an App Store app that registers with WhatsApp via Apple's framework. There is no supported web-based, file-based, or URL-scheme installation path.

The old `whatsapp://stickerPack` pasteboard API (2018) required a custom UTI type (`net.whatsapp.third-party.sticker-pack`) and binary `NSJSONSerialization` data — neither of which can be produced from a browser or file.

Even on its last working versions, the URL scheme was fragile and frequently broken by iOS updates, WhatsApp Business conflicts, and Apple's clipboard security model (blocked on `file://` URLs entirely). Modern WhatsApp versions have removed support for it altogether.

hopefully this serves someone


---



## Usage

### 🗂️ Flat folder — all images become one pack

```
whatsappsticker stickers/ -o ./packs
```

Over 30 images? Packs split automatically ("My Pack 1", "My Pack 2", …).  
Under 3? Stickers are duplicated to reach 3.


### 📂 Subfolder mode — one pack per subfolder

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

```
whatsappsticker stickers/ -o ./packs
```

Each subfolder is a named pack. Max 30 per subfolder (error if exceeded).  
Below 3? Padded automatically.


### 📊 HTML preview

```
whatsappsticker path/to/stickers -o ./packs --report
```

---

## Options

| Flag              | Default                    | Description                          |
|-------------------|----------------------------|--------------------------------------|
| `-o, --output`    | `output/`                  | Output directory                     |
| `--name`          | folder name (title-cased)  | Pack name for flat folders           |
| `--publisher`     | `WhatsApp Sticker Tool`    | Publisher name in metadata           |
| `--report`        | `False`                    | Generate HTML preview gallery        |

---

## WhatsApp limitations (and how we handle them)

| Limitation                          | Our approach                                      |
|-------------------------------------|---------------------------------------------------|
| 3–30 stickers per pack              | Below 3 → pad. Above 30 → split (flat mode).     |
| ≤100 KB per static sticker          | Quality-tuned WebP export hits the target.        |
| ≤500 KB per animated sticker        | Same, with the higher animated limit.             |
| No mixing static & animated         | Says not Allowed — iOS app accepts mixed packs.            |
| 512×512 pixels                      | Auto-resized and centre-cropped.                  |
| 96×96 PNG tray icon                 | Generated from the first sticker.                 |

---

## Output structure

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


## License

[MIT](LICENSE)
