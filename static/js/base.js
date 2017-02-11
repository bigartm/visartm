function getRgb(color) {
	if (color[0] == "#") return $c.hex2rgb(color).a;
	else return $c.name2rgb(color).a;
}

var getUrlParameter = function getUrlParameter(sParam) {
    var sPageURL = decodeURIComponent(window.location.search.substring(1)),
        sURLVariables = sPageURL.split('&'),
        sParameterName,
        i;

    for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === sParam) {
            return sParameterName[1] === undefined ? true : sParameterName[1];
        }
    }
};


//D3 Tooltip
var D3Tooltip = function() {
	var tooltipDiv = d3.select("body").append("div")	
		.attr("class", "d3tooltip")				
		.style("opacity", 0);
	
	
	var show = function (message, mouse) {
		tooltipDiv
			.transition(200)		
			.style("opacity", .9);	
		tooltipDiv
			.html(message)
			.style("left", (d3.event.pageX) + "px")		
			.style("top", (d3.event.pageY - 28) + "px")
			.attr("visibility", "visible")
			;
	};

	var hide = function() {
		tooltipDiv
			.transition(200)		
			.style("opacity", 0);
	};
	
	return {
		show: show,
		hide: hide
	}
};