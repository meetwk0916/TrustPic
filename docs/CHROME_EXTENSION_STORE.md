# TrustPic Chrome Web Store Notes

Last aligned: 2026-05-29

## Package

Create the upload ZIP from the repository root:

```bash
sh extension/package.sh
```

Upload the generated `trustpic-chrome-0.1.0.zip` in the Chrome Web Store Developer Dashboard.

## Listing Draft

Short description:

```text
Right-click an image to generate a TrustPic evidence report.
```

Detailed description:

```text
TrustPic has one purpose: generate an evidence report for an image selected from the browser context menu.

Right-click an image and choose "Analyze image with TrustPic". The report opens in Chrome Side Panel and summarizes readable evidence found in that selected image.

TrustPic is evidence-first. It does not claim that an image is real, fake, authentic, or AI-generated when readable evidence is absent. The report shows confidence and explains what each signal can and cannot show.
```

## Single Purpose Statement

```text
TrustPic lets the user right-click one image in Chrome and generate a single evidence report for that selected image.
```

## Permission Justification

- `contextMenus`: required to show the "Analyze image with TrustPic" action when the user right-clicks an image. This is the extension's main entry point.
- `sidePanel`: required to show the TrustPic evidence report in Chrome Side Panel after the user right-clicks an image.
- `storage`: required to store the current report state and language preference locally in Chrome. TrustPic does not use storage for tracking, advertising, or cross-site profiling.
- `host_permissions: <all_urls>`: required to fetch the image URL that the user explicitly selects through the right-click image menu. The extension does not scan webpages automatically, does not read page content, and does not access images unless the user starts the analysis from the context menu.

## Remote Code Declaration

```text
TrustPic does not use remote code. All extension JavaScript, HTML, CSS, and assets are packaged inside the extension. The extension only sends the user-selected image to the TrustPic API and receives JSON/image report data. The API response is data, not executable code.
```

## Privacy Disclosure Draft

TrustPic processes only the image selected by the user through the right-click menu. The extension fetches that image and sends it to the TrustPic API for analysis. Uploaded image bytes are not stored by the extension. The extension stores only the latest image URL, latest analysis status, and latest returned report in Chrome local storage.

TrustPic does not sell user data, does not run advertising tracking, and does not use the extension for cross-site behavioral profiling.

Privacy policy URL:

```text
https://<cloudflare-pages-production-domain>/privacy.html
```

## Reviewer Notes

- Manifest V3 extension.
- Single purpose: right-click one image and generate a TrustPic evidence report for that selected image.
- No remotely hosted executable code.
- No analytics SDK.
- No user account requirement.
- The backend API is `https://trustpic-production.up.railway.app`.
- The extension requires broad host access because the user can right-click images from arbitrary webpages.
