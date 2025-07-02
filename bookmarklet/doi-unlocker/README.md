# DOI Helper - Your Speedy Paper Access Pal

Hey research warriors! DOI Helper is a super handy bookmarklet that sniffs out
those Digital Object Identifiers (DOIs) on whatever page you're on. Then, it
zaps you straight to one of these awesome services to (hopefully!) unlock that
paper:

- Sci-Hub
- LibGen SciMag
- Official DOI resolver (doi.org)

---

## Getting Started

It's a piece of cake to get this bookmarklet up and running:

1. **Copy the Code:** Grab the entire line of code from `bookmarklet.min.js`.
2. **Make a Bookmark:** Create a new bookmark in your favorite browser.
3. **Paste the Code:** In the bookmark's URL (or Address) field, paste the code 
   you copied.
4. **Find a DOI:** Head over to a webpage that has a DOI on it (like an academic 
   publisher's site).
5. **Click It!** Click your new bookmarklet.

You'll then get a couple of quick questions:

- Which DOI d'you want (if it spots more than one).
- Which service should open it?

---

## So, How Does It Do That

This little script is pretty smart about finding DOIs. It looks in a few places:

- Checks out `<meta>` tags (you know, the `citation_doi` kind).
- Scans the main text of the page for DOI patterns.
- Looks at the URLs in links (`<a>` tags) just in case a DOI is hiding there.

Once it finds them, it gets rid of any duplicates, shows you the list, and then
whisks you away to your chosen service with the DOI you picked.

---

## Want to Tinker

The full, more readable source code is right there in `bookmarklet.js` if
you're curious or want to play around.

Here are a few ideas for making it your own:

- Add more Sci-Hub mirrors if you know some good ones.
- Skip the pop-up questions and make it automatically pick your go-to service.
- Swap out the standard `prompt()` boxes for a fancier custom UI.

---

## A Quick Heads-Up (The Important Bit)

This tool is meant for your personal educational use and research kicks.

Just a friendly reminder: accessing paywalled content without the green light
from the owners might go against local laws or your institution's policies.
You're the captain of your ship, so please make sure your actions are all above
board.

---

## License

This baby is open source under the MIT License. So go ahead – use it, tweak it,
share it. Go wild (responsibly, of course)!
