document.addEventListener("DOMContentLoaded", function () {
    var button = document.getElementById("openAnalyzer");
    if (button) {
        button.addEventListener("click", function () {
            chrome.tabs.create({
                url: "http://localhost:57720/"
            });
        });
    }
});
