# 📚 DOI Helper Bookmarklet

This is a browser bookmarklet that extracts DOI (Digital Object Identifier) values
from the current webpage and opens them using one of the following services:

- 🧪 Sci-Hub
- 📘 LibGen SciMag
- 🔗 Official DOI resolver (doi.org)

---

## 🚀 How to Use

1. Copy the entire line from `bookmarklet.min.js`.
2. Create a new browser bookmark.
3. Paste the copied code into the URL field of the bookmark.
4. Navigate to a page containing a DOI (e.g. academic publisher sites).
5. Click the bookmarklet.

You'll be prompted to:

- Select a DOI (if multiple are detected).
- Choose a source to open the paper.

---

## 🔍 What It Does

The script scans the current page for DOI values by:

- Reading `<meta>` tags (e.g. `citation_doi`)
- Searching the page body text
- Checking anchor (`<a>`) tag URLs

It removes duplicates and prompts you to select from the found DOIs, then opens
the selected DOI with your chosen source.

---

## 🛠 Development

The full readable source is available in `bookmarklet.js`.

You can customize it by:

- Adding more Sci-Hub mirrors
- Skipping prompts and automating the source selection
- Replacing `prompt()` with custom UI elements

---

## ⚠ Legal & Ethical Notice

This tool is intended for educational and personal use only.

Accessing paywalled content without proper authorization may violate local laws
or institutional policies. Users are responsible for ensuring their actions
comply with applicable regulations.

---

## 📄 License

MIT License — you are free to use, modify, and share this code.
