function isTouchDevice() {
	return "ontouchstart" in window || navigator.maxTouchPoints;
}

(function CheckJavascriptAndTouch() {
	var htmlTag = document.querySelector("html");
	var htmlClasses = htmlTag.getAttribute("class");
	if (htmlClasses !== null) {
		htmlTag.setAttribute("class", htmlClasses.replace("no-js", ""));
	}

	var touchClass = isTouchDevice() ? " touch" : " no-touch";
	document.querySelector('html').className += touchClass;
})();