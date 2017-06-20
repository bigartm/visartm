var Slideshow = function () {

    var slideshowContainer;
    var slideshowItems;
    var slideshowNavPrev;
    var slideshowNavNext;
    var slideshowCounter;

    var currentSlideIndex = 0;
    var slideshowShouldLoop = false;
    var currentSlidePosition;
    var startTouch = null;
	var autoMode = true;

    var slideshow = {
        container: ".js-slideshow-container",
        slide: ".js-slideshow-slide",
        previous: ".js-slideshow-previous",
        next: ".js-slideshow-next",
        counter: ".js-slideshow-counter"
    };

    var init = function (pageElement, shouldLoop) {
        var slideshowPageElement = document.querySelector(pageElement);
        slideshowShouldLoop = shouldLoop;

        if (slideshowPageElement === undefined)
            return;

        slideshowContainer = slideshowPageElement.querySelector(slideshow.container);
        slideshowItems = Array.prototype.slice.call(slideshowContainer.querySelectorAll(slideshow.slide));
        slideshowNavPrev = slideshowPageElement.querySelector(slideshow.previous);
        slideshowNavNext = slideshowPageElement.querySelector(slideshow.next);
        slideshowCounter = slideshowPageElement.querySelector(slideshow.counter);

        if (slideshowItems.length === 0)
            return;



        if (slideshowShouldLoop) {
            setupSlideshowLoop();
        }

        setCurrentSlide(false);

        //setup touch handlers
        slideshowContainer.addEventListener("touchstart", handleTouchStart, false);
        slideshowContainer.addEventListener("touchmove", handleTouchMove, false);
        slideshowContainer.addEventListener("touchend", handleTouchEnd, false);
        slideshowContainer.addEventListener("touchcancel", handleTouchCancel, false);

        //setup nav click handlers
        slideshowNavPrev.addEventListener("click", goToPrevious);
        slideshowNavNext.addEventListener("click", goToNext);
        log("initialized");
    };

    var setupCounter = function () {
        if (slideshowShouldLoop) {
            slideshowCounter.textContent = "Slide " + currentSlideIndex + " of " + (slideshowItems.length - 2);
        }
        else {
            slideshowCounter.textContent = "Slide " + (currentSlideIndex + 1) + " of " + slideshowItems.length;
        }
		
		if (slideshowItems[currentSlideIndex].hasAttribute("label")) {
			slideshowCounter.textContent = slideshowItems[currentSlideIndex].attributes["label"].value; 
		}
    };

    var setupSlideshowLoop = function () {

        var firstSlide = slideshowItems[0];
        var lastSlide = slideshowItems[slideshowItems.length - 1];
        var firstSlideCopy = firstSlide.cloneNode(true);
        var lastSlideCopy = lastSlide.cloneNode(true);

        //insert first and last in DOM
        slideshowContainer.insertBefore(lastSlideCopy, firstSlide);
        slideshowContainer.appendChild(firstSlideCopy);


        //insert first and last in slide array
        slideshowItems.unshift(lastSlideCopy);
        slideshowItems.push(firstSlideCopy);
        currentSlideIndex = 1;
    };

    var getTouch = function (touchObj) {
        var touch = {};
        touch.pageX = touchObj.pageX;
        touch.pageY = touchObj.pageY;
        touch.timestamp = new Date();
        return touch;
    };

    var handleTouchStart = function (e) {
        startTouch = getTouch(e.changedTouches[0]);
        log("touchstart at " + startTouch.pageX);
    };

    var handleTouchMove = function (e) {
        if (startTouch === null) {
            return;
        }

        var currentTouch = getTouch(e.changedTouches[0]);
        var pixelsMovedX = currentTouch.pageX - startTouch.pageX;
        var pixelsMovedY = currentTouch.pageY - startTouch.pageY;

        if (Math.abs(pixelsMovedY) > Math.abs(pixelsMovedX)) {
            slideshowContainer.dispatchEvent(new Event("touchcancel"));
            return;
        }

        if (!slideshowShouldLoop && isFirstSlide() && pixelsMovedX < -100) {
            pixelsMovedX = -100;
        }
        if (!slideshowShouldLoop && isFirstSlide() && pixelsMovedX > 100) {
            pixelsMovedX = 100;
        }

        var currentPageX = pixelsMovedX + currentSlidePosition;
        slideshowContainer.style.transition = "";
        slideshowContainer.style.transform = "translate3d(" + currentPageX + "px, 0px, 0px)";
    };

    var handleTouchEnd = function (e) {
        if (startTouch === null) {
            return;
        }
        var endTouch = getTouch(e.changedTouches[0]);
        var pixelsMovedX = Math.abs(endTouch.pageX - startTouch.pageX);
        var touchSpeed = endTouch.timestamp - startTouch.timestamp;

        log("touchend at " + endTouch.pageX + ", moved " + pixelsMovedX + " pixels in " + touchSpeed + " ms");

        if ((touchSpeed < 300 && pixelsMovedX > 6) || (pixelsMovedX / slideshowContainer.offsetWidth > 0.5)) {
            if (endTouch.pageX < startTouch.pageX) {
                goToNext();
            }
            else {
                goToPrevious();
            }
        }
        else {
            setCurrentSlide(true);
        }
        startTouch = null;
    };

    var handleTouchCancel = function (e) {
        startTouch = null;
        log("touchcancel");
    };

    var setCurrentSlide = function (animate) {

        moveToSlide(animate);

        if (slideshowShouldLoop) {
            if (isLastSlide()) {
                currentSlideIndex = 1;
                setTimeout(function () {
                    moveToSlide(false);
                }, 300);
            }
            else if (isFirstSlide()) {
                currentSlideIndex = slideshowItems.length - 2;
                setTimeout(function () {
                    moveToSlide(false);
                }, 300);
            }
        }
        else {
            setNavState();
        }
        setupCounter();
    };

    var moveToSlide = function (animate) {
        slideshowContainer.style.transition = animate ? "all 0.2s ease" : "";
        currentSlidePosition = slideshowContainer.offsetLeft - slideshowItems[currentSlideIndex].offsetLeft;
        slideshowContainer.style.transform = "translate3d(" + currentSlidePosition + "px, 0px, 0px)";
    };

    var setNavState = function () {
        removeClass(slideshowNavPrev, "inactive");
        removeClass(slideshowNavNext, "inactive");
        if (isFirstSlide()) {
            addClass(slideshowNavPrev, "inactive");
        }
        if (isLastSlide()) {
            addClass(slideshowNavNext, "inactive");
        }
    };

    var goToPrevious = function () {
		autoMode = false;
        if (!isFirstSlide()) {
            currentSlideIndex--;
        }
        setCurrentSlide(true);
    };

    var goToNext = function (automatically) {
		//alert(automatically);
        if (automatically != "m") {
			autoMode = false; 
		}
		if (automatically == "m" && !autoMode){
			return;
		}
		
		if (!isLastSlide()) {
            currentSlideIndex++;
        }
        setCurrentSlide(true);
    };

    var isFirstSlide = function () {
        return currentSlideIndex === 0;
    };

    var isLastSlide = function () {
        return currentSlideIndex === slideshowItems.length - 1;
    };

    var log = function (text) {
        console.log(text);
    };

    var addClass = function (element, classToAdd) {
        if (element === null)
            return;

        removeClass(element, classToAdd);

        var classes = element.getAttribute("class");

        element.setAttribute("class", classes + " " + classToAdd);
    };

    var removeClass = function (element, classToRemove) {
        if (element === null)
            return;

        var classes = element.getAttribute("class");
        if (classes === null)
            return;

        var classArray = classes.trim().split(/[ ]+/g);
        for (var i = 0; i < classArray.length; i++) {
            if (classArray[i] === classToRemove) {
                classArray.splice(i, 1);
                break;
            }
        }
        element.setAttribute("class", classArray.join(" "));
    };

    return {
        init: init,
		goToNext: goToNext
    }

}