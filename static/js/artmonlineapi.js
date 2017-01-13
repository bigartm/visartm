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
	
	getDocuments(documentsIds, callback) {
		var xhttp = new XMLHttpRequest();
		var docs_count = documentsIds.length;
		var query = "";
		for (var i = 0; i < docs_count; ++i) {
			query += documentsIds[i] + ",";
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
}