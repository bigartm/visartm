function getRgb(color) {
	if (color[0] == "#") return $c.hex2rgb(color).a;
	else return $c.name2rgb(color).a;
}

function getUrlParameter(parameterName, defaultValue) {
    sURLVariables = decodeURIComponent(window.location.search.substring(1)).split('&');
	var ret = undefined;
	for (i = 0; i < sURLVariables.length; i++) {
        sParameterName = sURLVariables[i].split('=');

        if (sParameterName[0] === parameterName) {
            ret = sParameterName[1];
			break;			
        }
    }
	if (ret) { return ret;}
	else {return defaultValue;}
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