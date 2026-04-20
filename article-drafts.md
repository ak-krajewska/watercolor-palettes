# Article Drafts

Three versions of the project writeup. Pick one, mix and match, or use as reference.

---

## Version 4 — Chronological

**How I built a palette planning tool with an LLM**

I have seventy-two watercolor paints catalogued on artistpigments.org. The site handles inventory well — pigment codes, lightfastness, granulation, transparency. What it doesn't do is help me plan which paints to put in a tin for a specific purpose. I wanted a small set of purpose-built palettes: one default for plein air in San Francisco, a garden palette, an urban sketching palette. I decided to build something local.

### Starting with the data

The first step was getting the data out of artistpigments. The site exports an xlsx file with one row per paint — color name, brand, pigment codes, lightfastness, transparency, granulation. I copied it into a new folder and read it with Python. Seventy-two paints across five brands: CfM Handmade Watercolors, Winsor & Newton Professional, Holbein, Roman Szmal Aquarius, and a few stragglers.

I also had an earlier spreadsheet from before I found artistpigments — a manual catalog I'd built myself. It had things the artistpigments export didn't: hue categories, alternative pigment names, and three CfM paints that weren't listed on the site at all. The first real design decision was how to merge these. The answer was a build script that treats the xlsx as the primary source and the manual CSV as supplementary — filling in hue categories and adding the uncatalogued paints. Run the script after any new artistpigments download and the merged inventory stays current.

### The pigment index

The hue category merge revealed a gap: the manual spreadsheet only covered about a third of my paints. Most of the Holbein and Roman Szmal paints had no hue category at all.

It turned out I had a third file — a reference table derived from Bruce MacEvoy's Handprint site, mapping pigment codes to color families (violet blue, earth orange, blue green, and so on). The right solution was to make that a data file the build script could query, rather than hardcoding lookups. Unknown pigments — a newer benzimidazolone yellow, a fluorescent dye, mica — get added to the reference file, not to the script. Four paints ended up needing manual additions to the index. After that, hue category coverage was complete.

### Designing the palette data model

The interesting design problem was palettes themselves. A palette has a physical reality — a specific tin with a specific number of slots — and a conceptual one. The same pan of Dioxazine Violet lives physically in one box, but it belongs conceptually to both my default palette and my garden palette. These needed to be separate things.

The model I settled on: a `palettes.csv` with one row per paint per palette, including which container it lives in and its physical position (row and slot). A separate `containers.csv` defines the boxes — slot count, pan orientation, portability. Slot counts are maximums, not targets. A paint can appear in multiple conceptual palettes; the physical constraint is enforced by the painter, not the data.

### The default palette

I've been using the same default palette for a while. It lives in a CfM Small Palette — fourteen slots, excellent fold-out mixing wells. Top row: white gouache, Cadmium Yellow, Permanent Rose, Cadmium Red, Alizarin Crimson, Ultramarine, Cerulean. Bottom row: Dioxazine Violet, Cobalt Sea Blue, Sap Green, Yellow Ochre, Burnt Sienna, Cyprus Burnt Umber, Indigo.

Recording this palette meant recording what I actually knew about it — which colors I couldn't live without (Permanent Rose, Cadmium Yellow, Yellow Ochre, Indigo), which were underperformers (Alizarin Crimson, Cadmium Red), and why. Cerulean is beautiful but I never mix with it. Indigo is my near-black and general darkener, doing the job Payne's Gray used to do. Sap Green is ugly straight from the pan but a reliable base for mixing foliage greens. This kind of qualitative knowledge doesn't fit in a CSV. It went into a markdown notes file.

The notes files live in a `notes/` folder and get rendered into the HTML output. They're freeform. The structure is: what the palette is for, what works, what doesn't, open questions.

### The garden palette

My garden has a lot going on: California natives, several varieties of sage, geraniums, thyme, dandelions, California poppies, calla lilies, manzanita, and a large and varied collection of succulents. The default palette doesn't handle it well. The main gap is greens — the garden has deep greens, silvery greens, and the complex powdery-to-sun-damaged range of succulent colors.

Working out the garden palette took some time. The CfM greens I had (Olive, Cypress Green, Tide Pool) turned out to be chaparral and coastal colors, not garden colors. The garden needed a different green strategy: Phthalo Green as a dark anchor and deepener, Bamboo Green as a mid-range foliage base, Cobalt Cerulean for silvery greens and powdery succulents. Indigo for darks, but I didn't have a second pan yet, so Burnt Umber went in as a placeholder — warm, which is right for the mood of this palette regardless.

The flower colors came from Roman Szmal: Quinacridone Magenta and Pyrrole Red, both untested but promising. The backbone colors — Cadmium Yellow, Cadmium Red, Dioxazine Violet, white gouache — came from W&N, which I trust.

### The urban sketching palette

The third palette was more of a creative exercise. I do urban sketching with a black fountain pen — the pen handles all the drawing, so the watercolor only needs to provide atmosphere, light, and mood. Eight paints in a CfM Yellow palette, middle row deliberately empty.

The constraint of "eight paints, pen does the work, lightfastness doesn't matter" opened up options that aren't available on other palettes. Holbein Opera — a fluorescent pink with notoriously poor lightfastness — is exactly right here. Holbein Davy's Grey is SF fog in a pan. Holbein Cherry Blossom Pink, which I hadn't decanted yet, is a soft granulating pink that could do useful things over pen lines. Prussian Blue instead of Ultramarine because city skies aren't romantic.

### The HTML output

Once the data was solid, a second script generated a browsable HTML page: one section per palette showing the physical layout as a grid of pan cards, with the notes file rendered below. A filterable inventory table at the bottom shows all seventy-two paints with a useful filter: "not used in any palette." Thirty-five paints currently sit outside all palettes. That's a number worth looking at.

### The label problem

Looking at the pan grid in the HTML output raised a practical question. I swatch my paints on cotton paper cut to half-pan size, and I label them in Sharpie. The labels are fine but fragile. A printed label glued to the back of the cotton swatch would be more durable and include the pigment code, which Sharpie doesn't.

The build script already had all the data. Adding a second output — `labels.html` — was straightforward: pan-sized cards (19mm × 30mm for standard half-pans), grouped by palette, laid out in physical row order. The one complication was that different palette boxes orient their pans differently. The CfM Yellow takes pans lying flat — labels are landscape. The other boxes stand pans upright — labels are portrait. That's a field on the containers table now.

### What this is

The whole project is a few CSV files, two Python scripts, and a notes folder. It's not complex software. It's precisely sized for one person's problem, and that's exactly the kind of thing that used to not be worth building. Working through the design with an LLM made it faster and better than working alone — not because the LLM wrote the code, but because it's useful to have something to think out loud with that can hold the context of the problem and ask the next question.

The repo is at [github.com/ak-krajewska/watercolor-palettes](https://github.com/ak-krajewska/watercolor-palettes). The scripts and reference data are reusable by anyone with an artistpigments collection. The palette notes are mine.

---

## Version 1 — Considered tone (AK's best judgment)

**Seventy-two paints and a spreadsheet**

I have seventy-two watercolor paints. [artistpigments.org](https://artistpigments.org) does a genuinely good job of cataloguing them — pigment codes, lightfastness ratings, granulation, transparency, all of it. What it doesn't do is help me decide which twelve to put in a tin before I hike somewhere.

That's a palette planning problem, and it's mine to solve. The goal is a set of small, purpose-built palettes: one for plein air landscapes, one for painting in my garden, one for urban sketching with a fountain pen. Fewer paints means fewer decisions in the field, and fewer decisions in the field means better paintings.

I built a local tool to help with this. The core is a Python script that merges my artistpigments export with some hand-maintained notes, outputs a master CSV, and validates that my palette definitions don't reference paints that no longer exist. A second script generates a browsable HTML page showing each palette in its physical layout, and a set of printable labels sized to standard half-pans — because I swatch on cotton paper and needed something to glue to the back.

The data model has a few decisions worth noting. Palettes are conceptual and physical separately: the same paint can appear in multiple conceptual palettes, but physically it occupies one slot in one tin. Containers are their own table, because slot count is a hard constraint when you're planning what to carry. The pigment index is a data file, not hardcoded logic, so unknown pigments get added to the reference rather than patched into the script.

None of this is especially complex software. That's the point. It's precisely sized for one person's problem, which is exactly the kind of thing that used to be not worth building. An LLM as a design collaborator changes that calculation — not because it writes the code, but because working through the problem out loud with something that can ask questions and push back makes the design better and faster than working alone.

The [repo is here](https://github.com/ak-krajewska/watercolor-palettes). It's structured as a template: the scripts and reference data are reusable by anyone with an artistpigments collection; the palette definitions and notes are mine.

---

## Version 2 — Extravagant prose

**The tyranny of abundance, or: how I learned to stop worrying and trust the half-pan**

There is a particular species of paralysis that afflicts the watercolorist standing before a full palette on a foggy Tuesday morning in San Francisco. It is not the paralysis of scarcity — the painter who has only ochre and indigo and makes do magnificently — but its more insidious cousin: the paralysis of seventy-two options, each one winking at you from its little pan like a jewel in a very disorganised treasury.

I own seventy-two watercolor paints. I am not apologising for this. [Artistpigments.org](https://artistpigments.org), a website of surpassing usefulness, helps me catalogue them: their pigment codes, their lightfastness ratings, their granulating tendencies, their staining sins. What it cannot do — what no website can do, because this is not a website problem — is look me in the eye and say: *for the succulents in your garden on a warm morning, these eight paints and no others.*

That is a palette planning problem. It is also, I discovered, a software problem, which is to say a problem susceptible to the application of a little structured thinking and a Python script or two.

The tool I built is modest in ambition and precise in execution. A script merges my paint inventory with hand-maintained notes and a Handprint-derived pigment reference — because the lightfastness of a newer benzimidazolone yellow is, frankly, anyone's guess, and that fact belongs in a data file rather than a comment in the code. A second script renders everything as a browsable HTML page, each palette displayed in its physical row-and-column layout, plus a sheet of printable labels sized to the exact dimensions of a standard half-pan. This last feature emerged unexpectedly from looking at the HTML output and remembering, with sudden clarity, that I had been writing colour names in Sharpie on little scraps of paper like some kind of feral art student.

The design has a small elegance I'm fond of: containers are their own data, because a twelve-slot tin is a constraint as real as any lightfastness rating. Palettes are conceptual and physical at once — the same Dioxazine Violet can belong to both the garden palette and the default palette in the abstract, while physically it occupies exactly one slot in exactly one box. The pigment index is a CSV, not a dictionary embedded in a function, because data and operations should be separated, and I did not learn this from a computer science textbook but from the experience of wanting to add a pigment code without touching a script.

The LLM in this collaboration was less a code generator than a design interlocutor: something to think out loud with, to push back against, to correct when it optimised for the wrong thing. The result is a tool of almost aggressive specificity — built for one collection, one set of subjects, one person's conviction that the garden always reads warm even on foggy days. Which is, perhaps, the most honest definition of personal software: something that knows what you mean.

[The repo](https://github.com/ak-krajewska/watercolor-palettes) is structured as a template. The scripts are yours. The opinions about Dioxazine Violet are mine.

---

## Version 3 — Dry technical (Google Developer Documentation style)

**Watercolor Palettes: a personal inventory and palette planning tool**

This document describes a local palette planning tool for watercolor painters who maintain a paint inventory on [artistpigments.org](https://artistpigments.org).

**Overview**

The tool extends an artistpigments.org collection export with palette planning functionality not available on the platform. It consists of two Python scripts, a set of CSV data files, and two HTML outputs.

**Problem statement**

artistpigments.org provides comprehensive paint inventory management including pigment codes, lightfastness ratings, and paint properties. It does not support the definition of named palettes, physical palette layouts, or the generation of printable pan labels. This tool provides those features as a local supplement to the existing platform.

**Components**

*Data files*
- `paints-inventory.xlsx` — export from artistpigments.org; replace when new paints are added
- `paints-manual-notes.csv` — manually maintained supplementary data including hue categories and paints not catalogued on artistpigments.org
- `pigment-index.csv` — maps pigment codes to color families; extend this file to add coverage for new pigments
- `data/containers.csv` — defines physical palette containers, slot counts, and pan orientation
- `data/palettes.csv` — defines named palettes as ordered lists of paint IDs with container and position data
- `data/inventory.csv` — generated output; do not edit directly

*Scripts*
- `build_inventory.py` — merges source files into `data/inventory.csv`; validates palette references against inventory IDs and container IDs
- `build_html.py` — generates `index.html` and `labels.html` from the data files

*Outputs*
- `index.html` — browsable palette viewer with filterable full inventory
- `labels.html` — printable pan labels sized to standard half-pan dimensions (19mm × 30mm), oriented per container

**Key design decisions**

*Palettes are conceptual, not physical.* A paint may appear in multiple palettes in `palettes.csv`. Physical slot constraints are enforced by the user, not the data model. Slot counts on containers represent maximums, not targets.

*Reference data lives in files, not code.* The pigment-to-color-family mapping is maintained in `pigment-index.csv`. To add an unknown pigment, add a row to that file and re-run the build scripts.

*The inventory is a generated artifact.* `data/inventory.csv` is produced by `build_inventory.py` and should not be edited manually. Source data lives in the xlsx export and the manual notes CSV.

**Usage**

To update after adding new paints:
```
# Replace paints-inventory.xlsx with a fresh export from artistpigments.org
python3 build_inventory.py
python3 build_html.py
```

**Requirements**

```
pip3 install openpyxl markdown
```

**Repository**

[github.com/ak-krajewska/watercolor-palettes](https://github.com/ak-krajewska/watercolor-palettes)

The repository is structured as a template. Data files specific to the author's collection are excluded via `.gitignore`. To use with your own collection, replace the source data files and update `data/palettes.csv` and `data/containers.csv` as needed.
