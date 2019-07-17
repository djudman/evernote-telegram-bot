(function() { 
	"use strict";

	class EvernotebotAdminApi {
		constructor(token) {
			this.apiUrl = "/api";
			this.token = token;
		}

		login(username, password) {
			let url = this.apiUrl + "/login";
			let data = {
				username: username,
				password: password,
			}
			this.httpRequest("POST", url, data);
		}

		httpRequest(method, url, data) {
			var xhr = new XMLHttpRequest();
			xhr.withCredentials = true;
			xhr.open(method, url);
			if (this.token) {
				xhr.setRequestHeader("AUTH_TOKEN", this.token);
			}
			xhr.onload = function(e) {
				let response = JSON.parse(this.response);
				if (!response.status) {
					console.log(response);
					return;
				}
				window.location = "/";
			}
			if (data) {
				let body = JSON.stringify(data);
				xhr.send(body);
			} else {
				xhr.send();
			}
		}
	}

	function loadCss(path) {
		let link = document.createElement("link");
		link.href = path;
		link.type = "text/css";
		link.rel = "stylesheet";
		document.getElementsByTagName("head")[0].appendChild(link);
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
		let button = document.getElementById("loginButton");
		button.onclick = function() {
			let username = document.getElementById("username").value;
			let password = document.getElementById("password").value;
			api.login(username, password);
		};
	}

	function onLoad() {
		loadCss("/evernotebot.css")
	}

	var token = "";
	window.api = new EvernotebotAdminApi(token);
	window.onLoadLoginPage = onLoadLoginPage;
	window.onload = onLoad();
})()
