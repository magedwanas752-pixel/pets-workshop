---
name: دفتر الذكريات
description: A private Arabic keepsake book made from warm paper, botanical marks, and treasured photos.
colors:
  paper: "#f5f0e5"
  paper-deep: "#ebe2d1"
  paper-light: "#fffaf0"
  photo-paper: "#fffdf6"
  ink: "#403632"
  ink-soft: "#685a51"
  ink-faint: "#84766c"
  sage: "#71826d"
  sage-dark: "#4e624d"
  rose: "#bb7772"
  rose-dark: "#8d4e4b"
  honey: "#c4a569"
  line: "#d7cbb7"
  envelope-light: "#f8e9d1"
  envelope-mid: "#ebd6b8"
  envelope-deep: "#e8d1b1"
  envelope-flap: "#f3e2c7"
  envelope-line: "#d5bea1"
  envelope-fold: "#dfc7a8"
  letter-line: "#e3d6c3"
  envelope-seal-ink: "#fff6ec"
  photo-line: "#e8dfd1"
  drop-line: "#c5b59d"
  empty-line: "#cbbca5"
  rose-hover: "#763d3b"
typography:
  display:
    fontFamily: 'Georgia, "Times New Roman", serif'
    fontSize: "clamp(2rem, 4vw, 3rem)"
    fontWeight: 400
    lineHeight: 1.3
  body:
    fontFamily: '"Avenir Next", Avenir, "Segoe UI", sans-serif'
    fontSize: "16px"
    fontWeight: 400
    lineHeight: 1.75
  handwritten:
    fontFamily: '"Bradley Hand", "Segoe Print", "Comic Sans MS", cursive'
  label:
    fontFamily: '"Avenir Next", Avenir, "Segoe UI", sans-serif'
    fontSize: "0.875rem"
    fontWeight: 400
    letterSpacing: "0.035em"
  wordmark:
    fontSize: "1.2rem"
  privacy-label:
    fontSize: "0.84rem"
  wordmark-mobile:
    fontSize: "1.05rem"
components:
  privacy-label:
    textColor: "{colors.ink-soft}"
  welcome-envelope:
    backgroundColor: "{colors.envelope-light}"
    width: "370px"
    height: "224px"
  access-paper:
    backgroundColor: "{colors.paper-light}"
    textColor: "{colors.ink}"
  memory-card:
    backgroundColor: "{colors.photo-paper}"
    textColor: "{colors.ink}"
    padding: "11px 11px 16px"
  photo-picker:
    backgroundColor: "rgb(255 250 240 / 54%)"
    borderColor: "{colors.drop-line}"
  empty-state:
    backgroundColor: "rgb(255 250 240 / 48%)"
    borderColor: "{colors.empty-line}"
---

# Design System: دفتر الذكريات

## Overview

**Creative North Star: "A Private Botanical Keepsake"**

The notebook feels like a letter folded into a favorite book: a warm paper
canvas, a flower-sealed envelope at the lock screen, and photographs mounted as
slightly tilted scrapbook prints once the owner opens the book. Its Arabic
right-to-left default and English left-to-right option are calm and personal
rather than administrative. A compact composition form sits beside the archive
so the act of remembering remains close to the memories already kept.

The atmosphere continues the user's selected botanical-envelope reference, but
the product truth is now a private memory book. The envelope is an expressive
frame around a real password form, never a substitute for the lock. Real
uploaded photographs lead each memory; decorative flower marks remain
secondary.

**Key Characteristics:**
- Warm, softly textured paper, botanical ink, pressed-flower rose, and sage.
- A sealed envelope frames the first-run password setup and returning-user lock.
- Memories pair a title and personal story with an optional date and real images.
- Arabic/English language switching with matching RTL/LTR flow, visible keyboard
  focus, and reduced motion.

## Colors

Warm paper is the dominant ground. Sage, rose, and honey guide attention;
envelope and tape shades are small, material-specific accents.

### Primary
- **Warm paper** (`colors.paper`): Main canvas with a subtle printed grain.
- **Ink** (`colors.ink`): Headings and primary reading copy.
- **Soft ink** (`colors.ink-soft`): Explanatory copy and quiet controls.

### Botanical accents
- **Sage** (`colors.sage`, `colors.sage-dark`): Plant marks and reassuring
  secondary emphasis.
- **Pressed rose** (`colors.rose`, `colors.rose-dark`): Flower seals, primary
  actions, and destructive-action emphasis.
- **Honey** (`colors.honey`): Tiny warm highlights, such as a flower center.

### Paper materials
- **Deep paper** (`colors.paper-deep`): Recessed image grounds.
- **Letter paper** (`colors.paper-light`): Form and note surfaces.
- **Photo paper** (`colors.photo-paper`): Keepsake borders around uploaded images.
- **Paper line** (`colors.line`): Dividers, outlines, and quiet boundaries.
- **Envelope and fold shades** (`colors.envelope-*`, `colors.envelope-line`,
  `colors.envelope-fold`): The layered invitation at the privacy gate.

**The Keepsake Rule.** Paper remains the main surface; rose, sage, and honey are
small accents, not large competing panels.

## Typography

**Display Font:** Georgia-led serif stack for keepsake-like Arabic headings.
**Body Font:** Avenir Next-led system sans-serif for controls and reading.
**Handwritten Font:** A system cursive stack for brief, decorative notes only.

Arabic glyphs should remain legible at every size. Use natural line wrapping,
right-aligned multi-line body copy, and a clear visual distinction between
labels, descriptions, and personal stories.

### Hierarchy
- **Display:** `clamp(2rem, 4vw, 3rem)`, 400, line-height 1.3.
- **Hero:** 2.75rem on desktop, 2.25rem on narrow screens, 400, line-height 1.3.
- **Book title:** 2.625rem on desktop and 2rem on narrow screens.
- **Section heading:** 2rem or 1.75rem, 400, line-height 1.3.
- **Memory title:** 1.375rem, 400, line-height 1.35.
- **Body:** 16px, 400, line-height 1.75.
- **Supporting copy:** 1.0625rem, 0.9375rem, 0.875rem, and 0.8125rem.
- **Labels and metadata:** 0.75rem, 0.6875rem, and 0.84rem.
- **Decorative wordmark and botanical marks:** 1.05rem, 1.125rem, 1.2rem,
  1.25rem, 1.5rem, 1.6rem, 1.7rem, and 2.2rem.
- **Envelope and large section details:** 1.75rem and 2.625rem.
- **Shared shell fallback headings:** 2.5rem/4.5rem and 2rem/3rem responsive
  scales; the access and book headings use the fixed sizes above.

## Layout

The main shell is capped at 1120px with 24px gutters, tightening to 16px on
mobile. The access screen pairs the envelope and password paper on wide screens
and stacks them at 720px. The authenticated book pairs a 270–340px composition
column with a flexible scrapbook archive; it becomes a single-column flow at
720px. Memory cards use two columns when space permits and one column below
520px.

The composition area precedes the gallery in the document so the most direct
task remains first on narrow screens. The archive uses generous gaps instead
of dense rows, and cards keep enough width for comfortable Arabic reading.

## Elevation and Depth

Material depth comes from paper contrast, thin borders, layered folds, and
modest soft shadows. The envelope and actual photo prints receive the strongest
lift; writing controls remain visually quiet.

## Shapes

Paper surfaces use square corners and thin outlines. The envelope is formed by
folded triangular layers, its flower seal is circular, and actual memory photos
sit inside straight-edged keepsake frames. Avoid generic rounded app cards.

## Components

### Privacy gate
- **Character:** A quiet invitation with an unambiguous functional form.
- **Behavior:** The first visit asks for a password and confirmation; later
  visits ask for the password. The four-character minimum is a local-use
  constraint, not a claim of internet-grade security.
- **Accessibility:** The form labels remain visible, error messages are
  announced, password entry uses native controls, and focus is conspicuous.

### Memory composer
- **Character:** A paper writing surface beside the gallery.
- **Behavior:** Title and story are required; date and images are optional.
  Selected images show a local preview before saving.
- **Validation:** The server accepts verified JPEG, PNG, WEBP, and GIF images,
  at most eight files, 10 MiB each, and 25 megapixels per image.

### Memory keepsakes
- **Character:** A real photo print with a short written caption, not a generic
  dashboard tile.
- **Behavior:** Memories appear in reverse chronological order when dated;
  undated entries follow. Delete requires confirmation and removes associated
  stored image files.
- **Empty state:** A dashed paper boundary invites the first memory without
  placeholder content that could be mistaken for a real entry.

### Password settings and session
- A quiet details disclosure exposes password change without competing with
  the writing workflow.
- The logout control closes the book and returns to the lock screen.
- Private data and photo responses are not cached by the browser.

## Focus and Motion

Keyboard focus uses a visible 3px deep-rose outline with a 4px offset. Hover
transitions are short and subtle. Honor `prefers-reduced-motion` globally;
never make motion necessary to open or use the book.

## Do's and Don'ts

### Do:
- **Do** keep private content behind the authenticated session, including photos.
- **Do** keep Arabic/English copy aligned with its RTL/LTR direction and readable
  at every size.
- **Do** let real photographs and the owner's actual writing lead each keepsake.
- **Do** state that the data lives on this device and must be backed up.
- **Do** keep form errors, upload limits, and destructive actions explicit.

### Don't:
- **Don't** claim cloud backup, cross-device sync, or public hosting safety.
- **Don't** add sample memories that could be mistaken for personal content.
- **Don't** expose images through an unauthenticated static directory.
- **Don't** let decorative paper, flowers, or script type reduce task clarity.
