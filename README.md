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
| `privacy.html` | Privacy statement, with the measurement opt-out (linked from the form and footer) |
| `thank-you/index.html` | Shown after a confirmed enquiry; records the enquiry conversion |
| `assets/js/tracking.js` | Google Ads / Analytics loading, consent defaults, conversion events |
| `robots.txt`, `sitemap.xml` | Tell search engines what to crawl. Update `<lastmod>` in the sitemap after content changes |
| `CNAME` | The custom domain. Don't delete it, or the domain stops working |

## Common changes

**Contact details.** Gavin's name, mobile and email appear in three places. Change all three
together: the Private Inspections section in `index.html`, `thank-you/index.html` and `privacy.html`,
plus `contact` in `site-config.js` (used by the phone call bar and form messages).

**Enquiry form.** Delivered by Formspree (formspree.io). In the Formspree account for
gavin@steinbok.com.au, create a form, then put its ID (the part after `formspree.io/f/`) in
`enquiryForm.id`. The ID is a public identifier, not a password. Never put account logins or
private API keys in this repository. Until `id` is set, the form shows "not yet connected" and can't
be sent. Web3Forms also works (`provider: 'web3forms'`, `id` = access key); if you switch, update
the "How enquiries are delivered" paragraph in `privacy.html`.

After a confirmed delivery, visitors go to `thank-you/` (noindex, and deliberately not in the
sitemap). A failed submission never redirects and never counts as a conversion.

**Google Ads and Analytics.** Fill in `googleAds.conversionId` (`AW-…`), the three labels
(`enquiry` primary; `phone` and `email` secondary) and, optionally, `googleAnalytics.measurementId`
(`G-…`). Nothing from Google loads until an ID is set (`assets/js/tracking.js`).
- The enquiry conversion fires on the thank-you page only when the form left a one-time token
  after confirmed delivery. Reloads and direct visits count nothing, and the token is sent as
  `transaction_id`. In Google Ads, set the enquiry action up as a **website event using code**,
  not a "page load of URL contains thank-you" rule, which would count reloads.
- Phone and email conversions count clicks on `tel:` and `mailto:` links. A click isn't proof
  that a call or email happened.
- Events are also pushed to `dataLayer`: `generate_lead`, `phone_click`, `email_click`.
- Visitors in the EEA, UK and Switzerland default to denied (Consent Mode). Anyone can switch
  measurement off on the privacy page.

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
