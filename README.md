# The Terrigal Residence

A single-page architectural brochure for a renovated three-level coastal home in Terrigal, NSW.
It's a plain static site (HTML, CSS and a little JavaScript, with no build step) built for GitHub Pages.

**Intended address:** https://steinbok07.github.io/the-terrigal-residence/

## What's where

| File | What it controls |
|---|---|
| `assets/js/site-config.js` | **Start here.** Specifications, contact details, brochure PDF, floor plans |
| `index.html` | All wording, section order, photo captions and image descriptions |
| `assets/css/style.css` | Colours, fonts and layout (colour tokens are at the top) |
| `assets/js/main.js` | Photo viewer, menu, scroll effects. Rarely needs changing |
| `assets/img/photos/` | Web-optimised photographs (generated, see below) |
| `assets/floorplans/` | Generated view-only floor plans (SVG) |
| `assets/brochure/` | The PDF brochure goes here |
| `tools/build_images.py` | Regenerates the photographs from the original PNGs |
| `tools/build_floorplans.py` | Regenerates the marketing floor plans from the CDC PDFs |

## Common changes

**Add contact details.** In `site-config.js`, fill in `contact.email`, `contact.phone` and/or
`contact.inspectionUrl`. The "Request a Private Inspection" button switches from a placeholder to a
working link on its own. If an inspection URL is set, it's used in place of email.

**Add the brochure.** Copy the PDF to `assets/brochure/`, then set
`brochurePdf: 'assets/brochure/your-file.pdf'`.

**Floor plans.** The plans are generated from the architect's CDC drawings by
`python tools/build_floorplans.py "<folder with the three CDC PDFs>"`. It reads the drawings'
own vector linework, keeps only the marketed residence (the right-hand one on the drawings), removes
demolition, hatch, section and annotation layers, and writes view-only SVGs to
`assets/floorplans/`. Room names come from the drawing's own labels (`LEVELS` in the script).
The site deliberately offers **no downloads**: don't put PDFs or the original drawings in the
website folder, as anything in it becomes publicly reachable once published. For PDF copies to
review privately, add a second argument with a folder outside the website. The floor list and
room summaries on the site are set in `floorPlans` in `site-config.js`.

**Change specifications.** Edit the `specs` list. Remove the `note` from the floor-area line once
the area is confirmed.

**Change wording.** Edit the text in `index.html`. Each section is marked with a comment such as
`<!-- 04 LIVING & ENTERTAINING -->`.

**Replace or add a photo.**
1. Put the new PNG in the originals folder (kept outside this repository), and add or change its line in
   `PHOTOS` in `tools/build_images.py`.
2. Run `python tools/build_images.py "<originals folder>"`. It prints the `srcset` line to use.
3. In `index.html`, copy an existing `<figure class="plate …">` block, update the file names,
   `width`/`height`, `alt` description and caption. Plate numbers follow page order, and the
   index in the Details section (`data-goto="n"`) refers to them.

**Add or remove a section.** Copy or delete a `<section>` block in `index.html`, and add or
remove its link in both the header nav and the `#menu` list.

## Rules this site follows

- All paths are relative (no leading `/`), so the site works under the `/the-terrigal-residence/`
  subpath. Keep it that way.
- Placeholders are deliberately visible. Don't swap them for buttons that don't do anything.
- Only verified facts go in: no invented measurements, brands, certifications or room-by-level
  assignments, and no claims of accessibility compliance for the lift.
- The superseded photo "Minimal Coastal Living Space with Ocean Views" isn't used.

## Previewing locally

From the folder *above* this one: `python -m http.server 4173`, then open
http://localhost:4173/the-terrigal-residence/ (this matches the GitHub Pages subpath).

## Publishing

Live site: **https://steinbok07.github.io/the-terrigal-residence/** (GitHub Pages, deployed from
the `main` branch of this repository). Keep this address unchanged.

- `main` = what's live. Anything pushed to `main` is published within about a minute.
- `dev` = work in progress. Make and check all changes on `dev` in the local preview first.
- To deploy approved changes only: merge `dev` into `main`, push `main`, then check the live site.
- Never push unfinished edits to `main`.
