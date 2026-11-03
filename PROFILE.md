# Profile artwork

The root `README.md` embeds `profile/profile.svg`: a reference-style profile
strip with a four-cell loading indicator above the Moonwash ocean animation.
The introduction reads "Ujjwal Rana Magar.", "Hello git!!", and "Curious by
default" in Commit Mono. The indicator and ocean both have reduced-motion
stills. The large name has an eight-second white shimmer with a soft glow;
reduced-motion preferences keep the name still. The build also writes
`profile/name-preview.gif` to preview the name animation on its own.

Below the introduction, three adjoining contact sections share thin dividers
with no gaps between them. LinkedIn and Instagram show handles with angled
arrows and link directly to the supplied profiles; Discord displays `@uzuw`.

The typeface is the exact `fonts/CommitMono-Regular.woff2` supplied in the
[reference repository](https://github.com/ripgrim/ripgrim/tree/main/fonts).
Its MIT license is preserved in `fonts/CommitMono-LICENSE`. The font and ocean
animation are embedded directly in the SVG, so it needs no external services.

To change the copy, edit the `text(...)` calls in `build_profile.py`, then run:

```sh
python3 build_profile.py
```

Pillow is the only dependency for this step. The build checks text bounds,
embedded assets, the loading indicator, animation decoding, and logo-free
contact sections. It writes the README, SVG panels, and matching PNG/GIF
previews. Open `index.html` to see the animated layout.

After changing the ocean art, run `python3 mocks/build_ocean.py` before
`python3 build_profile.py` to include the updated scene.

The SVG has a still fallback for reduced-motion preferences and descriptive
text for screen readers. As with the reference, its typography scales with
the image on small screens. The README displays the generated SVGs directly;
no separate hosting service is needed.
