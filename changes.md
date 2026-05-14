# Session Changes

_Changes made during this work session. Updated as each fix is applied._

---

## Changes

### Frontend Functional Bugs

**`templates/blog.html`**
- Fixed broken search: `word in postTitle` (JS `in` operator tests index keys, not substrings) replaced with `postTitle.includes(word)` for all search fields (title, content, author, tags), in both exact-match and word-based search modes.

**`templates/blog_post.html`**
- Fixed `AttributeError` crash when `post.created_at` is `None`: added Jinja guard so date displays "Unknown" instead of throwing.
- Replaced deprecated `document.execCommand('copy')` in the copy-link button with the modern `navigator.clipboard.writeText()` API.

**`templates/edit_blog_post.html`**
- Added comment in `loadExistingWorksCited()` noting that `works_cited` is not yet persisted by the backend (always loads as `[]`). No functional change; the null guard was already present.

**`templates/admin/add_gallery_item.html`**
- Fixed counter bug for Additional Images, Slideshow Images, Creators, Videos, and Project Links: replaced ever-incrementing global index variables with live DOM counts so labels always show the correct number after removals. Re-numbering logic runs on every removal to keep labels sequential.

**`templates/index.html`**
- Replaced fragile User-Agent regex mobile detection with `window.matchMedia('(max-width: 768px)')` for reliable viewport-based detection.
- Replaced brittle `error.message.includes('memory')` string check for WebGL failures with a proper `webglcontextlost` DOM event listener.

**`app.py`**
- Changed `MAX_CONTENT_LENGTH` from 100MB to 15MB to match the client-side file size validation already enforced in JS. Previously a user bypassing JS could upload files up to 100MB.

---

### Bug Fix — /gallery 500 Internal Server Error

**Root cause:** The local service account lacks `storage.objects.list` permission on the GCS bucket. `_list_files()` in `cloud_storage.py` had no error handling, so the `403 Forbidden` from GCS propagated all the way up as an unhandled exception, causing a 500 on every GET `/gallery` request.

**`cloud_storage.py`**
- Added `self._storage_available = False` as a default field before the try block so it is always defined.
- Set `self._storage_available = True` only after the startup bucket connectivity test passes; keeps it `False` on auth/permission failures.
- Added availability guard and try/except to `_list_files()` — returns `[]` instead of crashing when storage is down.
- Added availability guard to `_save_json()` — skips the write with a log message instead of throwing.

**`app.py`**
- Added `import logging`.
- Wrapped `get_all_gallery_items()` and `get_all_courses()` calls in the `gallery()` route with try/except; on failure, flashes a user-friendly error and renders the page with empty lists rather than serving a 500.
- Added an upfront `_storage_available` check that flashes a clear "Storage unavailable" message when GCS credentials are missing or lack permission.

---

### Hide Blog Nav Button

The BLOG nav button was inconsistently present on some pages (cis_news, blog, blog_post, add_blog_post, edit_blog_post) but absent on others (index, gallery, team, contact). Removed it from all 5 templates and replaced each with a comment so it can be easily restored when the blog is ready to go public.

**Templates changed:** `cis_news.html`, `blog.html`, `blog_post.html`, `add_blog_post.html`, `edit_blog_post.html`
- Removed `<a href="/blog" class="nav-button">` nav link from each navbar.
- Left a `<!-- BLOG nav link hidden from public until blog is ready to launch -->` comment in its place.

---

### Fix Inconsistent Navbar on Login/Register Pages

`login.html` and `register.html` had a stale, out-of-date navbar that differed from every other page: wrong item labels ("GALLERY" / "OUR TEAM"), wrong order (Team was last instead of second), and no auth block (LOGIN/LOGOUT buttons were missing entirely).

**`templates/login.html`** and **`templates/register.html`**
- Replaced old navbar with the standard navbar used across the rest of the site.
- Corrected item order: HOME → TEAM → PROJECTS → CIS NEWS → CONTACT US.
- Renamed "GALLERY" → "PROJECTS" and "OUR TEAM" → "TEAM" to match other pages.
- Added the standard auth block (shows LOGIN when logged out, LOGOUT + admin links when logged in).

---

### Consistent Navbar Active-Button Highlight

The CIS News page already marked its nav button with `nav-button-active` (blue tint background + inset border shadow), making it visually distinct and giving a different hover appearance. No other page did this, causing inconsistent navbar behaviour. Added `nav-button-active` to the current page's nav button on every template.

| Template | Button marked active |
|----------|----------------------|
| `index.html` | HOME |
| `team.html` | TEAM |
| `gallery.html` | PROJECTS |
| `gallery_item.html` | PROJECTS |
| `contact.html` | CONTACT US |
| `cis_news.html` | CIS NEWS (already had it) |
| `login.html` | LOGIN |
| `register.html` | LOGIN |

---

### Frontend — Performance Bugs

**Task 65 — Consolidated WebGL renderers (`templates/index.html`)**

Five separate `THREE.WebGLRenderer` instances (one per robot model) were replaced with a single shared renderer. Only one WebGL context is now created, eliminating the risk of hitting the 8–16 context limit browsers enforce.

Implementation: a `sharedThree` IIFE holds the single renderer (kept off-DOM). Each viewer gets a 2D `<canvas>` appended to its container; after each Three.js render call, the frame is blitted to that canvas via `ctx2d.drawImage(renderer.domElement, …)`. `OrbitControls` binds to the 2D canvas so pointer events continue to work normally. The per-viewer render loop checks `getBoundingClientRect()` and skips any viewer outside the viewport, which also handles task 67.

The five separate init functions (`initRobotViewer`, `initSweeperViewer`, `initMiniRobotViewer`, `initCuteRobotViewer`, `initSmallRobotViewer`), five animate functions, and five resize handlers were deleted and replaced with a single `loadModelIntoViewer(containerId, modelPath, camPos)` factory (~80 lines vs ~700 lines before). Dead code for `#sweeper-viewer` and `#cute-robot-viewer` (HTML containers that never existed) was also removed.

**Task 66 — SRI hashes on Three.js CDN scripts (`templates/index.html`)**

Added `integrity="sha384-…"` and `crossorigin="anonymous"` to all three CDN `<script>` tags (three.min.js from cdnjs, GLTFLoader.js and OrbitControls.js from jsDelivr). Hashes were computed with `openssl dgst -sha384 -binary | base64`. A compromised CDN can no longer silently inject code.

**Task 67 — Lazy-loading of GLB models (`templates/index.html`)**

Already implemented by the existing `IntersectionObserver` in `initAnimations()`. The refactored code preserves and clarifies this: `loadModelIntoViewer()` is only called when the model section enters the viewport, and `observer.unobserve()` is called immediately after to prevent re-initialization. The shared render loop additionally skips off-screen viewers each frame.

**Task 68 — A* timeout leak fix (`templates/index.html`)**

All `setTimeout` calls inside the A* visualization (`initAStarVisualization`, `startAStar`, `astarStep`, `resetAStar`) are now stored in an `astarTimeouts[]` array. `clearAStarTimeouts()` cancels all pending handles and is called at the start of `startAStar()` and `resetAStar()`, and also on the `pagehide` event so stale callbacks don't fire during browser history navigation.

**Task 69 — Blog page-payload size reduction (`templates/blog.html`, `app.py`)**

`{{ blog_posts | tojson | safe }}` was serialising full post content (potentially KB of HTML per post) into the initial JS payload. Fixed by:
- `app.py` now computes `blog_posts_meta` — a list containing only `id`, `title`, `slug`, `author_name`, `author_city`, `author_state`, `author_country`, `author_school`, `tags`, `created_at` — and passes it alongside `blog_posts`.
- `blog.html` uses `{{ blog_posts_meta | tojson | safe }}` so content is never sent to the client JS.
- `showAllPosts()` now restores the original server-rendered HTML (saved as `originalPostsHTML`) instead of rebuilding from JS, so server-side previews are always correct.
- `filterPosts()` no longer references `post.content`. Content search (the "Include content" checkbox) auto-submits the form for a server-side result rather than silently skipping it.
- `createPostElement()` (used for dynamic search results) renders title/author/tags/date without a content snippet; the READ MORE link is still present.

**Task 70 — `loading="lazy"` on images (`templates/gallery.html`, `templates/team.html`)**

Added `loading="lazy"` to:
- All `<img class="gallery-img">` tags in the three gallery item loops in `gallery.html` (image_url, additional_images[0], and video thumbnail variants — 9 tags total).
- All three team member photos in `team.html`.

`cis_news.html` already had `loading="lazy"` on its images.

**Task 71 — Self-hosted Orbitron font (all templates, `static/css/style.css`, `static/fonts/Orbitron.woff2`)**

Google Fonts loaded Orbitron via two external DNS connections (`fonts.googleapis.com` + `fonts.gstatic.com`) on every page, adding latency and sending page-visit data to Google.

- Downloaded `Orbitron.woff2` (v35, 12 KB) from `fonts.gstatic.com` and saved to `static/fonts/`.
- Added a `@font-face` rule to `style.css` with `font-display: swap` and a `font-weight: 400 900` range (covers all three weights from the same variable-font file).
- Replaced the three-line Google Fonts `<link>` block in every template with a single `<link rel="preload">` pointing to the local font file. Templates changed: `index.html`, `blog.html`, `gallery.html`, `gallery_item.html`, `team.html`, `contact.html`, `cis_news.html`, `login.html`, `register.html`, `add_blog_post.html`, `edit_blog_post.html`, `blog_post.html`, `admin/add_gallery_item.html`.
