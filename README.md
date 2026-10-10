# The Terrigal Residence

A single-page architectural brochure for a renovated three-level coastal home in Terrigal, NSW.
It's a plain static site (HTML, CSS and a little JavaScript, with no build step) built for GitHub Pages.

**Address:** https://terrigalhousesforsale.com.au/ (custom domain, set by the `CNAME` file). The old
https://steinbok07.github.io/the-terrigal-residence/ address redirects to it automatically.

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
| `tools/build_icons.py` | Regenerates `favicon.ico` and the PNG icons |
| `privacy.html` | Privacy statement for enquiry details (linked from the form and footer) |
| `robots.txt`, `sitemap.xml` | Tell search engines what to crawl. Update `<lastmod>` in the sitemap after content changes |
| `CNAME` | The custom domain. Don't delete it, or the domain stops working |

## Common changes

**Add contact details.** In `site-config.js`, fill in `contact.name`, `contact.phone` (mobile) and
`contact.email`. They appear in the Private Inspections section, in the call bar on phones and on
the privacy page. Empty values are simply left out.

**Connect the enquiry form.** The "Request a Private Inspection" form is delivered by Web3Forms
(web3forms.com). Create a free access key there for the email address enquiries should go to, then
paste it into `enquiryForm.accessKey`. Until then the form shows "not yet connected" and can't be
sent. Send a test enquiry after connecting it, and check that it arrives (including the spam folder).

**Google Ads tracking.** Fill in `googleAds.conversionId` (`AW-…`) and the conversion labels for
`enquiry`, `phone` and `email`. Nothing from Google loads until `conversionId` is set. An enquiry
only counts as a conversion once Web3Forms confirms it was delivered. Phone and email count on
click. The same actions are also pushed to `dataLayer` as `inspection_enquiry`, `phone_click` and
`email_click`.

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

**Change specifications.** Edit the `specs` list, and the matching written-out list inside
`<dl id="specs">` in `index.html` (it's there so search engines can read the facts without running
scripts). Remove the `note` from the floor-area line once
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

- Page paths are relative (no leading `/`), so the site works both at the domain root and in the local
  preview subpath. Absolute `https://terrigalhousesforsale.com.au/` addresses are used only where
  they must be (canonical link, social previews, structured data, sitemap). `404.html` uses
  root paths because GitHub serves it at any address.
- Search copy stays truthful and readable: no hidden keywords, no invented prices, agents,
  ratings, coordinates or floor-area certification in the page or in the structured data.
- Placeholders are deliberately visible. Don't swap them for buttons that don't do anything.
- Only verified facts go in: no invented measurements, brands, certifications or room-by-level
  assignments, and no claims of accessibility compliance for the lift.
- The superseded photo "Minimal Coastal Living Space with Ocean Views" isn't used.

## Previewing locally

From the folder *above* this one: `python -m http.server 4173`, then open
http://localhost:4173/the-terrigal-residence/.

## Publishing

Live site: **https://terrigalhousesforsale.com.au/** (GitHub Pages, deployed from the `main` branch
of this repository).

- `main` = what's live. Anything pushed to `main` is published within about a minute.
- `dev` = work in progress. Make and check all changes on `dev` in the local preview first.
- To deploy approved changes only: merge `dev` into `main`, push `main`, then check the live site.
- Never push unfinished edits to `main`.
