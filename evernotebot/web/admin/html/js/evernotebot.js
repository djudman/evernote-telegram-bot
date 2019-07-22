(function() { 
	"use strict";

	class EvernotebotAdminApi {
		constructor(token) {
			this.apiUrl = "/api";
			this.token = token;
		}

		buildQueryString(params) {
			return Object
				.keys(params)
				.map(k => `${k}=${encodeURI(params[k])}`)
				.join("&");
		}

		login(username, password) {
			let url = this.apiUrl + "/login";
			let data = {
				username: username,
				password: password,
			}
			this.httpRequest("POST", url, data, function(e) {
				let response = JSON.parse(this.response);
				if (!response.status) {
					console.log(response);
					return;
				}
				document.cookie = "token=" + response.data.token;
				window.location = "/";
			});
		}

		getLogs(page, pageSize, callback) {
			let qs = this.buildQueryString({page: page, page_size: pageSize});
			let url = this.apiUrl + "/logs?" + qs;
			return this.httpRequest("GET", url, null, callback);
		}

		httpRequest(method, url, data, onload) {
			var xhr = new XMLHttpRequest();
			xhr.withCredentials = true;
			xhr.open(method, url);
			if (this.token) {
				xhr.setRequestHeader("AUTH_TOKEN", this.token);
			}
			xhr.onload = onload;
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

	function onLoadLogsPage() {
		let getAttr = function(obj, path) {
			let val = obj;
			for (name of path.split(".")) {
				val = val[name];
			}
			return val || "";
		};
		let createCell = function(value, path) {
			let td = document.createElement("td");
			let v = getAttr(value, path);
			if (v instanceof Object) {
				v = JSON.stringify(v, null, 4);
			}
			td.innerHTML = "<pre>" + v + "</pre>";
			return td;
		};
		let createRow = function(data) {
			let row = document.createElement("tr");
			row.appendChild(createCell(data, "data.request.REQUEST_METHOD"));
			row.appendChild(createCell(data, "data.request.RAW_URI"));
			row.appendChild(createCell(data, "data.request.body"));
			row.appendChild(createCell(data, "data.response.status"));
			row.appendChild(createCell(data, "data.exception"));
			return row
		};
		api.getLogs(1, 10, function(e) {
			let response = JSON.parse(this.response);
			let tableLogs = document.getElementsByClassName("logs")[0];
			let tbody = tableLogs.getElementsByTagName("tbody")[0];
			for (let entry of response.data.data) {
				tbody.appendChild(createRow(entry));
			}
		});
	}

	function onLoad() {
		loadCss("/evernotebot.css")
	}

	var token = "";
	window.api = new EvernotebotAdminApi(token);
	window.onLoadLoginPage = onLoadLoginPage;
	window.onLoadLogsPage = onLoadLogsPage;
	window.onload = onLoad();
})()
