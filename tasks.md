  BACKEND                                                                                                                                                              
                                                                                                                                                                       
  Security — Credentials & Secrets                                                                                                                                     
                                                                                                                                                                       
  1. Rotate the Gmail app password immediately — it is hardcoded in plaintext in app.yaml:20 and setup_env.sh:7 and is permanently in git history even after deletion  
  2. Remove setup_env.sh from the repo entirely (contains the password and a hardcoded personal absolute path /Users/vaishnavanand/...)                                
  3. app.py:84 — SECRET_KEY falls back to 'your-secret-key-here' if the env var is missing; replace with raise RuntimeError(...) so production fails loudly instead of 
  silently being insecure                                                                                                                                              
  4. Move all secrets (GMAIL_APP_PASSWORD, SECRET_KEY) to GCP Secret Manager and reference them at runtime, not in app.yaml                                            
                                                                                                                                                                       
  Security — Authentication & Authorization
                                                                                                                                                                       
  5. cloud_storage.py:113–118 — user lookup iterates and downloads every users/*.json blob on every login attempt (O(N) GCS GETs); a non-existent user email causes a
  full bucket walk — easy DoS
  6. app.py:251–269 — no rate limiting on /login; vulnerable to credential stuffing
  7. app.py:281–303 — no rate limiting on /register; bots can mass-create accounts                                                                                     
  8. app.py:251 — email not normalized to lowercase before lookup; user@X.com and user@x.com are treated as different accounts                                         
  9. app.py:281 — no email verification step; anyone can register any email address                                                                                    
  10. app.py:281 — no password complexity validation; any single character is accepted                                                                                 
  11. app.py:281 — race condition between get_user_by_email check and create_user call allows duplicate email registrations under concurrent load                      
  12. No CSRF protection on any form; add Flask-WTF with CSRFProtect                                                                                                   
  13. No global rate limiter; add Flask-Limiter to at minimum /login, /register, /contact                                                                              
  14. No security headers (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy); add Flask-Talisman                                                          
  15. Hardcoded admin email list duplicated in at least 9 places across app.py, templates/gallery.html:69, templates/gallery_item.html:127, templates/contact.html:68, 
  templates/blog.html:238,259, and more — centralize into a single is_authorized_editor(user) helper and Jinja context processor                                       
  16. app.py:909–914 — check_permissions route has yet another hardcoded admin list and reflects current_user.email as raw HTML (XSS)                                  
  17. app.py:1130–1137 (/test-blog-access) — no auth at all; exposes the ADMIN_EMAILS list to anyone publicly                                                          
  18. Delete these debug routes entirely: /check-permissions, /debug-cloud-storage, /test-blog-access, /debug-blog-storage                                             
                                                                                                                                                                       
  Security — SSRF & Injection                                                                                                                                          
                                                                                                                                                                       
  19. pdf_generator.py:184 — requests.get(image_url, timeout=30) fetches user-supplied URLs with no host validation; an attacker can point it to                       
  http://169.254.169.254/ (GCP metadata server) — validate that the URL host resolves to a public IP
  20. video_thumbnail_extractor.py:79 — same SSRF risk for video URLs                                                                                                  
  21. pdf_generator.py:80,105 — item title and description passed unescaped to ReportLab Paragraph; a title containing <unknown> throws a parse error; escape or strip 
  tags before passing                                                                                                                                                  
  22. app.py:832–901 (PDF download routes) — download_name is set directly from item_data['title']; a title containing \r\n causes HTTP header injection in            
  Content-Disposition; sanitize the filename                                                                                                                           
                  
  Backend — Data Integrity & Storage Bugs                                                                                                                              
                  
  23. blog_storage.py:70–74 — if not blog_posts: return False prevents saving an empty list, so deleting the last blog post silently fails and data is not cleared     
  24. blog_storage.py:12–14 — threading.Lock is per-process; with multiple gunicorn workers, two workers can simultaneously read/write the same GCS blob causing lost
  updates; use GCS if-generation-match preconditions for safe concurrent writes (same issue in cis_news_storage.py)                                                    
  25. blog_storage.py:161–174 — post slug is regenerated from the title on every edit, breaking any existing shared links to that post when the title changes
  26. cloud_storage.py:222–243 (delete_gallery_item) — deletes only the JSON metadata blob; all associated image/video/thumbnail blobs are orphaned in GCS,            
  accumulating storage costs forever                                                                                                                                   
  27. cloud_storage.py:245–256 (update_gallery_item) — the field allow-list is missing creators, project_links, additional_images, additional_image_links,             
  slideshow_images, slideshow_image_links, videos, tags; editing a gallery item silently drops all of these fields                                                     
  28. app.py:623–626 — when arrays for images, links, and titles have mismatched lengths, only a warning is logged and data is silently dropped; return a 400 error
  with a clear message instead                                                                                                                                         
  29. app.py:1241–1251 — works_cited_* form fields are read from the POST body but never actually persisted to storage; either save them or remove the fields
  30. cloud_user.py:11,14 — self.id = user_data["id"] and created_at will throw KeyError if those fields are absent from the stored blob; use .get() with defaults     
  31. cloud_storage.py — mixes datetime.utcnow() and datetime.now() throughout, causing inconsistent timezone handling; standardize to datetime.utcnow() or            
  datetime.now(timezone.utc)                                                                                                                                           
                                                                                                                                                                       
  Backend — File Handling & Resource Leaks                                                                                                                             
                  
  32. app.py:832–901 — uses tempfile.NamedTemporaryFile(delete=False) and never calls os.unlink; temp files accumulate on the instance disk (App Engine F1 has only    
  256MB disk)
  33. video_thumbnail_extractor.py:87–88 — streams arbitrary video bytes to disk with no size cap; a multi-GB video URL will fill the instance disk and crash the      
  process                                                                                                                                                              
  34. image_optimizer.py:17 — self.format is set as instance state and mutated inside optimize_image based on filename extension; concurrent uploads with different
  formats (one JPEG, one PNG) will trample each other's format mid-call; make it a local variable                                                                      
  35. image_optimizer.py:62 — compression_ratio is computed by reading the stream after Image.open() has already advanced the pointer to the end; image_data.read()
  returns b'', so the ratio is always reported as ~100%; compute the original size before opening                                                                      
  36. image_optimizer.py:50–52 — PNG files are saved with optimize=False (no compression applied)
  37. pdf_generator.py:232 — PIL.Image.open() calls inside the PDF loop are never explicitly closed; file descriptor leak on exception                                 
  38. video_thumbnail_extractor.py:166 — import moviepy.editor is used but moviepy is not in requirements.txt; this will throw ImportError at runtime                  
  39. video_thumbnail_extractor.py:339 — fill='rgba(255, 255, 255, 0.9)' is not a valid PIL color (PIL expects a tuple or hex string); this will throw an error on that
   code path                                                                                                                                                           
                                                                                                                                                                       
  Backend — App Configuration                                                                                                                                          
                  
  40. requirements.txt — Pillow==10.0.1 has known CVEs (CVE-2024-28219 buffer overflow); bump to >=10.3.0                                                              
  41. requirements.txt — opencv-python-headless + numpy (~120MB) are used only to read one video frame in video_thumbnail_extractor.py; replace with imageio[ffmpeg] or
   ffmpeg-python to cut deploy size dramatically                                                                                                                       
  42. app.py:107–115 — Cache-Control: no-cache, no-store is set for every response including static-like JSON API responses; this disables all HTTP caching; use
  private, max-age=0, must-revalidate for HTML and longer TTLs for data endpoints                                                                                      
  43. app.py:117–124 — manual serve_static Flask route conflicts with App Engine's static_files handler in app.yaml; remove the Flask route and let app.yaml serve
  static files directly                                                                                                                                                
  44. app.py:1657 — app.run(debug=False, port=5000) — port 5000 conflicts with macOS AirPlay Receiver on development machines; use port 8080 (also matches App Engine
  convention)                                                                                                                                                          
  45. app.py:37 and hundreds of other print() calls throughout app.py, cloud_storage.py, blog_storage.py, image_optimizer.py — replace all with structured
  logging.getLogger(__name__) calls with appropriate severity levels                                                                                                   
  46. app.py:446 — uses request.content_length to validate file size, but for multipart/form-data this is the total body size, not the per-file size; check file size
  on the individual FileStorage stream                                                                                                                                 
  47. app.py:84 — MAX_CONTENT_LENGTH is 100MB server-side but client JS enforces 15MB; set both to the same value
  48. remove_tags_from_course_projects.py — one-off cleanup script left in the repo; delete it before it gets accidentally imported or scheduled                       
  49. No @app.errorhandler(404) or @app.errorhandler(500) registered; all unexpected errors return raw Flask 500 pages                                                 
  50. No automated tests anywhere in the repo (no tests/ directory, no pytest.ini, no CI config)                                                                       
                                                                                                                                                                       
  Backend — YouTube / Video                                                                                                                                            
                                                                                                                                                                       
  51. video_thumbnail_extractor.py:295–308 — YouTube regex doesn't handle youtube.com/shorts/<id> URLs; Shorts links return no thumbnail                               
   
  ---                                                                                                                                                                  
  FRONTEND        
                                                                                                                                                                       
  Security — XSS
                                                                                                                                                                       
  52. templates/edit_blog_post.html:248 — const postContent = \{{ post.content }}`embeds server-rendered post content directly into a JS template literal without      

  escaping; any backtick or${...}` in the content breaks the page, and a post editor can execute arbitrary JS in any admin's browser — Critical stored XSS

  53. templates/blog.html:462–505 (createPostElement) — uses innerHTML with unescaped post.title, post.author_name, post.content — stored XSS                          

  54. templates/gallery.html:901,904,1006,1187+ — multiple innerHTML = assignments interpolating course metadata (courseName, courseCode, courseDescription) without   

  encoding — stored XSS via admin-controlled data                                                                                                                      

  55. templates/gallery_item.html — same innerHTML pattern with unescaped server data throughout                                                                       

  56. templates/cis_news.html:149 — <img src="{{ item.image_url }}"> renders an admin-controlled URL without validation; could be used for tracking pixels or (in older

   browsers) javascript: execution                                                                                                                                     
                                                                                                                                                                       
[//]: # (  Frontend — Functional Bugs                                                                                                                                           )

[//]: # (                  )
[//]: # (  57. templates/blog.html:397–411 — search uses word in postTitle where postTitle is a JavaScript string; the JS in operator on strings tests integer index keys, not  )

[//]: # (  substring containment — the entire content search is a no-op; replace with postTitle.includes&#40;word&#41;)

[//]: # (  58. templates/blog_post.html:132 — post.created_at.split&#40;'T'&#41;[0] throws AttributeError in Jinja if created_at is None or not a string; add a if post.created_at guard)

[//]: # (  59. templates/edit_blog_post.html:280 — {{ post.works_cited|tojson|safe }} — works_cited is never persisted by the backend so this is always null; the field appears )

[//]: # (  in UI but saves nothing                                                                                                                                              )

[//]: # (  60. templates/add_gallery_item.html:330,372,417,460,498 — counters for additional images, slideshow images, creators, and videos only increment; removing an entry   )

[//]: # (  and then adding a new one produces sparse/out-of-order array indices that mismatch what the backend expects                                                          )

[//]: # (  61. templates/admin/add_gallery_item.html — client-side 15MB file size check enforced in JS but server MAX_CONTENT_LENGTH is 100MB; a user bypassing JS can upload)

[//]: # (  much larger files                                                                                                                                                    )

[//]: # (  62. templates/blog_post.html:313–332 — uses deprecated document.execCommand&#40;'copy'&#41; for the copy-link button; replace with navigator.clipboard.writeText&#40;...&#41;)

[//]: # (  63. templates/index.html:1665 — hardcoded substring check "memory" in error.message to detect WebGL context loss — fragile; different browsers phrase this error     )

[//]: # (  differently; use the webglcontextlost event instead                                                                                                                  )

[//]: # (  64. templates/index.html:23–26 — mobile detection by User-Agent regex string; should use window.matchMedia&#40;'&#40;max-width: 768px&#41;'&#41; feature detection instead           )
                                                                                                                                                                       
  Frontend — Performance
                                                                                                                                                                       
  65. templates/index.html — loads five separate Three.js WebGLRenderer instances simultaneously; browsers typically cap WebGL contexts at 8-16; any user with other   
  tabs open can hit this limit and get blank canvases; consolidate into a single renderer with multiple scenes or use CSS 3D transforms for simpler animations
  66. templates/index.html — loads Three.js r128 from cdnjs.cloudflare.com without a Subresource Integrity (SRI) hash; if the CDN is compromised, malicious JS runs on 
  your page with full access                                                                                                                                           
  67. templates/index.html — loads all Three.js GLB models eagerly on page load regardless of whether the user scrolls to those sections; lazy-load with
  IntersectionObserver                                                                                                                                                 
  68. templates/index.html — chained setTimeout calls for A* algorithm restart are never cleared on page navigation; can leak memory on single-page transitions
  69. templates/blog.html:334 — let allBlogPosts = {{ blog_posts | tojson | safe }}; dumps the full HTML content of every blog post into the initial page payload; send
   only metadata (title, author, date, slug) and lazy-load content on demand                                                                                           
  70. Most image tags across the site are missing loading="lazy"; only cis_news.html uses it — add to gallery grids, team photos, blog thumbnails                      
  71. Google Fonts are loaded synchronously on every page; add font-display: swap and consider self-hosting to avoid the extra DNS lookup                              
                                                                                                                                                                       
  CSS & Styling                                                                                                                                                        
                                                                                                                                                                       
  72. static/css/style.css is 5,766 lines — a single monolithic file; split into per-page or per-component files to improve maintainability and reduce per-page payload
  73. ~95 uses of !important in style.css, plus hundreds more in inline <style> blocks inside gallery.html (~250 lines) and gallery_item.html (~200 lines); refactor
  CSS specificity so !important is not needed                                                                                                                          
  74. Cache-busting version query params on <link> tags are inconsistent across templates (v='3.1', '3.3', '6.3', '6.5', '6.6', missing entirely on some); use a
  build-time hash or single version constant                                                                                                                           
  75. templates/gallery_item.html:165 — grid layout applied via inline style attribute on element; should be a CSS class
                                                                                                                                                                       
  Accessibility   
                                                                                                                                                                       
  76. Many icon-only buttons (share, delete, expand) have no aria-label; screen readers announce them as unlabeled                                                     
  77. No skip-to-content link at the top of any page; keyboard-only users must tab through the entire navigation on every page
  78. Heading hierarchy skips levels on multiple pages (e.g., h1 directly to h3 with no h2); this breaks screen reader document outline                                
  79. Team member photos in templates/team.html have no alt text describing the person                                                                                 
  80. templates/gallery.html:297 — data-creator attribute value uses |lower filter but is missing |e (HTML escape); special characters in a creator name will break the
   attribute                                                                                                                                                           
                                                                                                                                                                       
  UX                                                                                                                                                                   
                  
  81. All delete confirmation dialogs use native confirm() blocking dialogs (in cis_news.html, blog.html, gallery.html, gallery_item.html); replace with styled modal  
  dialogs
  82. No loading indicator for slow operations like PDF generation, file uploads, or gallery loads; users have no feedback that something is happening                 
  83. Flash messages have no client-side dismiss button; users must navigate away to clear them                                                                        
  84. templates/admin/manage_admins.html — the UI has no way to remove an existing admin; once added, the only removal path is a manual GCS JSON edit                  
  85. templates/team.html — all team member profiles (names, bios, LinkedIn URLs, photos) are hardcoded directly in the template with no admin UI to update them       
  86. Multiple pages contain hardcoded stale dates: login.html, register.html, gallery.html show 2024-01-15; team.html shows 2025-07-28; contact.html references "March
   2024" events                                                                                                                                                        
  87. templates/contact.html — no honeypot field or basic anti-spam; open to contact form spam                                                                         
  88. templates/blog_post.html:159–200 — custom [IMAGE:url] marker syntax parsed in the template with a fragile regex that breaks if the image URL contains a ]        
  character; use a more robust delimiter or a proper parser                                                                                                            
  89. templates/cis_news.html:162 — delete action uses a confirm() dialog with no undo; a mis-click permanently deletes a news item with no recovery path              
                                                                                                                                                         