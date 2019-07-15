(function() { 
	"use strict";

	function loadCss(path) {
		let link = document.createElement("link");
		link.href = path;
		link.type = "text/css";
		link.rel = "stylesheet";
		document.getElementsByTagName("head")[0].appendChild(link);
	}

	function loadLogs(page, pageSize) {
		var cookie = browser.cookies.get({
			name: "auth_token",
			url: browser.url,
		})
		if (!cookie) {
			console.log("Couldn't make request to API: `authToken` cookie is \
						not set. Try reload the page.")
			return
		}
		var auth_token = cookie.value
		var xhr = new XMLHttpRequest()
		xhr.open("GET", "/api/logs")
		xhr.setRequestHeader("AUTH_TOKEN", auth_token)
		xhr.send()
		var logsTable = document.getElementsByClassName("logsTable")
	}

	function onLoadLoginPage() {
		let username = document.getElementById("username");
		username.focus();
		let password = document.getElementById("password");
		password.onkeydown = function(e) {
			if (e && e.keyCode == 13) {
				document.getElementById("loginButton").click();
			}
		}
	}

	function onLoad() {
		loadCss("/evernotebot.css")
		var cookie = document.cookie
		console.log(cookie)
	}

	document.onload = onLoad()
})()
