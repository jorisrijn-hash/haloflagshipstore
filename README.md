# Halo — flagship marketing site (v2, multi-page)

Static HTML. No framework, no bundler, no runtime dependencies. Two stylesheets,
one script, one build step that exists only so the nav and footer are not
copy-pasted seven times.

```
python3 build.py          # pages/*.html + shell → *.html at the root
python3 -m http.server 8000
# open http://localhost:8000
```

`build.py` is optional tooling, not a dependency. The output in the repo root is
plain static HTML you can drop on any host, CDN or S3 bucket as-is.

## Layout

```
assets/halo.css     tokens, reset, primitives, nav, footer, transitions, the light
assets/pages.css    page-level components (heroes, deck, bento, composer, pricing)
assets/halo.js      all behaviour; every module no-ops when its markup is absent
brand/              favicons, PWA icons, manifest, OG and Twitter images
pages/*.html        page bodies only — this is what you edit
build.py            wraps each body in the shared shell
*.html              generated output — do not edit by hand
```

Two directives are available at the top of a page body:

```html
<!--close: Headline | Sub text -->   custom closing CTA
<!--noclose-->                       page supplies its own closing section
```

## Built in this pass

| Page | File | Notes |
|---|---|---|
| Home | `index.html` | Now a chapter opener, not the whole story. Hero, the problem, the card, what's inside, departments rail. |
| Product | `product.html` | Workspaces, departments, the role permission table, points, the two user experiences. |
| Appreciation cards | `cards.html` | The showpiece. Deck hero, card anatomy, the live composer, career scroll-stack, privacy model. |
| Templates | `templates.html` | Fan hero, filterable storefront, premium collections. |
| Halo AI | `ai.html` | Tone morph panel, and a full section on what the model deliberately will not do. |
| Pricing | `pricing.html` | Tiers, 16-row comparison table, add-ons, FAQ. |
| Security | `security.html` | Visibility matrix, controls, export and deletion. |

## Not built yet

`features`, `addons`, `customers`, `downloads`, `about`, `resources`, `contact`,
plus the three legal pages. They appear in the nav and footer as `aria-disabled`
with a "soon" marker rather than as broken links, so the full IA is visible
without shipping filler. Add `pages/<slug>.html` and an entry in `PAGE_META` and
they light up automatically.

Two of them need input rather than design work:

- **Customers** needs real logos, quotes and permission. Invented testimonials
  were cut from v1 for the same reason.
- **Downloads** needs real store URLs before the QR codes mean anything.

## Page transitions

Cross-document View Transitions (`@view-transition { navigation: auto }`) plus
named shared elements on the logo (`halo-brand`) and the hero light
(`halo-light`), so the ring does not blink between pages. Chrome 126+ and
Safari 18+ get the real thing. Firefox falls back to a 150 ms fade handled in
`halo.js`. `prefers-reduced-motion` disables both.

## The one visual rule

The neutrals are near-achromatic and cool (hue 262, chroma under 0.012). The
only warm colour in the entire system is the light: `--glow`, `--glow-core`,
`--glow-deep`, `--glow-ink`. It appears as emitted light, hairlines, and the
card face. Nothing else is ever warm. If a new component needs warmth to work,
the component is wrong.

Every dark section is lit by the same source, positioned per section:

```html
<div class="stage" style="--lx:78%; --ly:44%; --rsize:min(46vh,34vw); --lint:.7">
```

`--lx/--ly` place it, `--rsize` scales the ring, `--lint` dims the bloom. That
is why the site reads as one continuous space rather than seven pages.

---

# React Bits review

Source: `github.com/DavidHDev/react-bits`, 165 components across Animations (36),
Backgrounds (53), Components (44) and TextAnimations (32). Reviewed the full
index against Halo's register.

**Architectural note first.** Every component there is React, and the ones worth
having depend on `motion`, `gsap`, `three` or `ogl`. Halo currently ships zero
runtime dependencies and one script. Adopting them literally means adopting React
plus a WebGL runtime, which trades the 95+ Lighthouse target for effects that can
be reimplemented in CSS at a fraction of the cost. So: ideas adopted,
implementations written from scratch. Licence is MIT + Commons Clause, which
restricts reselling the library itself rather than using it in a product — worth
reading properly if you ever package this as a template for sale.

## Adopted, already in the build

| Idea | Where | What changed |
|---|---|---|
| **SpotlightCard** | `.spot` on every panel, tier, department and add-on | The strongest fit in the library. Halo's thesis is that appreciation is light landing on a person, so a warm pool that follows the cursor is literal, not decorative. Warm gold at 13% instead of a white or blue rim, 420 ms fade instead of instant, one delegated listener for the whole page instead of one per card. |
| **Stack / CardSwap** | `.deck` on `cards.html` | The object being browsed is the product. Rebuilt as real `<button>`s in a `role="group"` with arrow-key support and a dot control, because a card stack you cannot reach by keyboard is a demo, not a component. |
| **ScrollStack** | `.stack-scroll` on `cards.html` | Cards accumulating as you scroll *is* what a recognition history is. Pure `position: sticky` with a per-item offset, no scroll listener at all. |
| **MagicBento** | `.bento` on four pages | Kept the layout idea, dropped the equal tiles: 6-column grid with `wide` / `narrow` / `tall` / `full` spans so no two sections look alike. Border glow replaced by the spotlight, since two glow systems is one too many. |
| **Magnet** | `data-magnet` on primary CTAs only | 6px of pull. Anything more and the button feels loose rather than weighted. |
| **LogoLoop** | `.marquee` integration strip | CSS-only: one list duplicated, translated 50%, paused on hover, masked at both edges. Duplicate items are `aria-hidden`. |
| **GradualBlur** | `.fade-top` | Masked `backdrop-filter` under the fixed nav instead of a stack of blurred layers. The Apple "content dissolves into the chrome" cue. |
| **Noise / Grainient** | `.grain` on dark sections | Adopted for a technical reason, not a stylistic one: 40rem radial gradients band visibly on 8-bit displays, and 3.5% noise at `mix-blend-mode: overlay` is the standard fix. |
| **MaskedHeading** | existing `[data-mask]` | One reveal type for headings across the whole site. Using four different text animations is variety for its own sake. |
| **StaggeredMenu** | `.sheet` | Mobile links enter at 28 ms intervals. Confirmed the pattern; the implementation is three lines of CSS with `--i`. |

## Worth doing next

- **LightRays / SideRays / LightPillar** — volumetric shafts. On-brand, but they
  need a shader to look right. Candidates for one hero only (probably `about`),
  as a lazy-loaded canvas that never blocks paint.
- **Masonry / AccordionGallery** — the honest answer for the templates storefront
  once there are 40+ designs instead of 12.
- **VariableProximity** — display weight responding to cursor distance. Newsreader
  and Instrument Sans are already loaded as variable fonts, so this costs nothing.
  Use exactly once, on the mission statement on `about`. Twice and it is a gimmick.
- **ProfileCard** — for the team section on `about`, heavily reduced.
- **ReflectiveCard** — a moving specular sheen on the single hero card. Matches
  "the card is the lit thing". One instance, or it becomes noise.

## Rejected, with reasons

- **All cursor components** (BlobCursor, GhostCursor, SwarmCursor, TargetCursor,
  Crosshair, SplashCursor, ClickSpark, PixelTrail, ImageTrail) — replacing the
  system cursor is a portfolio-site move. Halo is asking people to type something
  sincere; the pointer should disappear.
- **Ballpit, Balatro, Hyperspeed, Galaxy, MetaBalls, Prism, PrismaticBurst,
  LiquidChrome, Plasma, PixelBlast, PixelSnow** — wrong register entirely.
  Playful, gamer or psychedelic. They would destroy the calm the whole design
  depends on.
- **GlitchText, DecryptedText, ScrambledText, FaultyTerminal, LetterGlitch,
  ASCIIText** — corrupting the text of an appreciation card is the exact opposite
  of the product's message.
- **GradientText, ShinyText** — `background-clip: text` on a gradient is banned in
  this system. Emphasis comes from weight, size and the italic.
- **GlassSurface, FluidGlass** — glassmorphism as decoration. The nav's backdrop
  blur is the only justified instance and it already exists.
- **TiltedCard** — 3D tilt on hover is the most saturated card effect of the last
  three years. `ReflectiveCard` gets at the same idea without the tell.
- **Dock, Folder, Lanyard, BubbleMenu, GooeyNav** — off-register. Lanyard is
  thematically perfect for a workplace product and still rejected: it is physics,
  which means bounce, which is banned in the motion language.
- **CountUp and the hero-metric pattern** — no invented statistics on this site.
  That decision was made in v1 and holds.
- **Dither, HalftoneReveal, MetallicPaint** — texture effects looking for a brief.

The rule applied throughout: an effect ships if removing it would make something
harder to understand or less true to the product. Everything above that failed
the test failed it for the same reason — it would have been impressive and meant
nothing.
