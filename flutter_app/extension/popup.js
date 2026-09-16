document.getElementById("openAnalyzer").addEventListener("click", function () {

    chrome.tabs.create({
        url: "http://localhost:57720/"
    });

});