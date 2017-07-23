function getRgb(color) {
	if (color[0] == "#") return $c.hex2rgb(color).a;
	else return $c.name2rgb(color).a;
}

function initColors(colorsCount) {
	background_rgb = getRgb(theme.backgroundColor);
	for (i=-1; i<=colorsCount; ++i) {	
		color = theme.palette(i);
		square = document.getElementById("square"+i);
		if (square) square.style.color = color;
		
		rgb = getRgb(color);  
		color = $c.rgb2hex( 
			~~(0.2*rgb[0]+0.8*background_rgb[0]), 
			~~(0.2*rgb[1]+0.8*background_rgb[1]),
			~~(0.2*rgb[2]+0.8*background_rgb[2])
		);
		$(".tpc" + i).css("background-color", color);
	}
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

function getCookie(name, default_value) {
  var matches = document.cookie.match(new RegExp(
	"(?:^|; )" + name.replace(/([\.$?*|{}\(\)\[\]\\\/\+^])/g, '\\$1') + "=([^;]*)"
  ));
  return matches ? decodeURIComponent(matches[1]) : default_value;
}

function setCookie(name, value) {
  document.cookie = name + "=" + value + "; path=/";
} 

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