function getRgb(color) {
	if (color[0] == "#") return $c.hex2rgb(color).a;
	else return $c.name2rgb(color).a;
}