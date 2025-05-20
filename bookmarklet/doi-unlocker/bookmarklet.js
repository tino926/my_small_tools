// DOI Helper Bookmarklet - Human-readable version
(function () {
    var sciHubMirrors = [
      "https://sci-hub.se/",
      "https://sci-hub.ru/",
      "https://sci-hub.st/"
    ];
  
    function getDOIsFromText(text) {
      var re = /\b10\.[^\s%"'#?,<>]+\/[^\s%"'#?,<>]+/g;
      return text.match(re) || [];
    }
  
    function getDOIFromMeta() {
      var meta = document.getElementsByTagName("meta");
      for (var i = 0; i < meta.length; i++) {
        var name = meta[i].getAttribute("name");
        if (name && name.toLowerCase() === "citation_doi") {
          return meta[i].getAttribute("content");
        }
      }
      return null;
    }
  
    function getDOIsFromLinks() {
      var links = document.getElementsByTagName("a");
      var found = [];
      for (var i = 0; i < links.length; i++) {
        var href = links[i].href;
        if (href && href.includes("10.")) {
          var match = href.match(/\b10\.[^\s%"'#?,<>]+\/[^\s%"'#?,<>]+/);
          if (match) found.push(match[0]);
        }
      }
      return found;
    }
  
    var metaDOI = getDOIFromMeta();
    var textDOIs = getDOIsFromText(document.body.innerHTML);
    var linkDOIs = getDOIsFromLinks();
  
    var allDOIs = [];
    if (metaDOI) allDOIs.push(metaDOI);
    allDOIs = allDOIs.concat(textDOIs, linkDOIs);
    allDOIs = [...new Set(allDOIs)]; // Remove duplicates
  
    if (allDOIs.length === 0) {
      alert("❌ DOI not found!");
      return;
    }
  
    var doi = (allDOIs.length === 1)
      ? allDOIs[0]
      : prompt("Multiple DOIs found. Please choose one:\n" + allDOIs.join("\n"), allDOIs[0]);
  
    if (!doi) return;
  
    var service = prompt(
      "Select source:\n1 = Sci-Hub\n2 = LibGen SciMag\n3 = DOI Official Link",
      "1"
    );
  
    var url = "";
    switch (service) {
      case "1":
        url = sciHubMirrors[0] + encodeURIComponent(doi);
        break;
      case "2":
        url = "http://libgen.is/scimag/index.php?s=" + encodeURIComponent(doi);
        break;
      case "3":
        url = "https://doi.org/" + encodeURIComponent(doi);
        break;
      default:
        alert("❗ Invalid selection");
        return;
    }
  
    window.location.href = url;
  })();
  