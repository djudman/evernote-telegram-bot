(function() { 
	"use strict";

	function loadLogs(page, pageSize) {
		var cookie = browser.cookies.get({
			name = "auth_token",
			url = browser.url,
		})
		if (!cookie) {
			console.log("Couldn't make request to API: `authToken` cookie is not\
						set. Try reload the page.")
			return
		}
		var auth_token = cookie.value
		var xhr = new XMLHttpRequest()
		xhr.open("GET", "/api/logs")
		xhr.setRequestHeader("AUTH_TOKEN", auth_token)
		xhr.send()
		var logsTable = document.getElementsByClassName("logsTable")
	}

	function onLoad() {
		loadLogs(1, 30);
	}

	document.onload = onLoad()
})()
