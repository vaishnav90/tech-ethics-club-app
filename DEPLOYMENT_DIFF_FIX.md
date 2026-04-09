# Why Local and Production Are Different - Common Causes

## 🔍 **Main Causes:**

### 1. **CSS Version Numbers (Cache-Busting)**
- Templates use version numbers like `v='3.1'` in CSS links
- If version doesn't change, browsers use cached CSS
- **Fix**: Update version numbers when CSS changes

### 2. **Static Files Not Deployed**
- App Engine might not upload all static files
- **Fix**: Check `app.yaml` handlers for static files

### 3. **Browser Caching**
- Production browsers cache CSS/JS aggressively
- **Fix**: Hard refresh (Ctrl+Shift+R / Cmd+Shift+R)

### 4. **Deployment Not Complete**
- Old code might still be running
- **Fix**: Check deployment logs, wait for deployment to complete

### 5. **Environment Differences**
- Different Python versions or dependencies
- **Fix**: Check `app.yaml` runtime version

## ✅ **Quick Fixes:**

### **Immediate Fix:**
1. **Update CSS version numbers** in templates (I just did this for gallery pages)
2. **Deploy again**: `gcloud app deploy`
3. **Hard refresh** production site: Ctrl+Shift+R (Windows) or Cmd+Shift+R (Mac)

### **Long-term Fix:**
Use a timestamp or hash-based versioning system instead of manual version numbers.

## 🔧 **What I Just Fixed:**

- Updated `gallery.html` CSS version from `v='3.1'` to `v='3.3'`
- Updated `gallery_item.html` CSS version from `v='3.2'` to `v='3.3'`

This will force browsers to fetch the new CSS file with all your recent changes (smaller tiles, better spacing, etc.).
