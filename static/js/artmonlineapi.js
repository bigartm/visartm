class ArtmApi {
	constructor(_host) {
		this.host = "http://127.0.0.1:8000";
	}

	getDocument(documentId, callback) {
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				//alert(this.responseText);
				callback(JSON.parse(this.responseText)[0]);
			}
		};
		xhttp.open("GET", this.host + "/api/documents?ids=" + documentId, true);
		xhttp.send();
	}
	
	getDocumentFull(documentId, callback) {
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				//alert(this.responseText);
				callback(JSON.parse(this.responseText)[0]);
			}
		};
		xhttp.open("GET", this.host + "/api/documents?full=1&ids=" + documentId, true);
		xhttp.send();
	}
	
	
	getDocuments(documentsIds, callback) {
		var xhttp = new XMLHttpRequest();
		var docs_count = documentsIds.length;
		var query = documentsIds[0];
		for (var i = 1; i < docs_count; ++i) {
			query += "," + documentsIds[i];

		} 
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				//alert(this.responseText);
				callback(JSON.parse(this.responseText));
			}
		};
		xhttp.open("GET", this.host + "/api/documents?ids=" + query, true);
		xhttp.send();
	}
	
	getPolygonChildren(polygonId, callback) {
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				callback(JSON.parse(this.responseText));
			}
		};
		xhttp.open("GET", this.host + "/api/polygons/children?id=" + polygonId, true);
		xhttp.send();
	}
	
	getTags(documentId, callback) {
		var xhttp = new XMLHttpRequest();
		xhttp.onreadystatechange = function() {
			if (this.readyState == 4 && this.status == 200) {
				callback(this.responseText);
			}
		};
		xhttp.open("GET", this.host + "/api/tags?id=" + documentId, true);
		xhttp.send();
	}
}