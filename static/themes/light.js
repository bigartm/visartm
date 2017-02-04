var theme_category_colors = [
	"#00ff00", "#0000ff", "#ff0000", 
	"#ff00ff", "#ffff00", "#00ffff",
	"#80ff80", "#8080ff", "#ff8080",
	"#ff80ff", "#ffff80", "#80ffff",
	"#ff8000", "#ff0080", "#80ff00",
	"#8000ff", "#00ff80", "#0080ff",
	"#008000", "#000080", "#800000",
	"#800080", "#808000", "#008080",
];
var d3_range = d3.scale.category20();
for (i=0;i<20;i++) {
	theme_category_colors.push(d3_range(i));
}

var theme =	{
	"d3_color_range" : d3.scale.category20(),
	
	"textColor" : "black",
	"backgroundColor" : "white",
	"activeColor" : "red",
	"selectionColor" : "yellow",
	
	"temporalSquares_EmptyColor" : "#ffffff",
	"temporalSquares_ActiveColor" : "#32ff32",
	"temporalSquares_TopColor" : "#ff0000",
	"temporalSquares_BottomColor" : "#00ff00", 
	
	"palette" : function(i) {
		if (i == -1) return "white";
		if (i == 0) return "grey";
		return theme_category_colors[i-1];
	}
}