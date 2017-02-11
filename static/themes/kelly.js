var kelly_colors = [
	'#F2F3F4', '#222222', '#F3C300',
	'#875692', '#F38400', '#A1CAF1',
	'#BE0032', '#C2B280', '#848482',
	'#008856', '#E68FAC', '#0067A5',
	'#F99379', '#604E97', '#F6A600', 
	'#B3446C', '#DCD300', '#882D17',
	'#8DB600', '#654522', '#E25822', '#2B3D26']


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
		return kelly_colors[(i+1)%kelly_colors.length];
	}
}