var color_range = d3.scale.category10();

var theme =	{
	"textColor" : "black",
	"backgroundColor" : "white",
	"activeColor" : "red",
	"selectionColor" : "yellow",
	
	"temporalSquares_EmptyColor" : "#ffffff",
	"temporalSquares_ActiveColor" : "#32ff32",
	"temporalSquares_TopColor" : "#ff0000",
	"temporalSquares_BottomColor" : "#00ff00", 
	
	"palette" : function(i) {
		if (i == 0) {
			return "grey";
		} else { 
			return color_range(i-1);
		}
	}
}