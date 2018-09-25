var currentAttendance;
var currentBellSchedule;
var currentStudents;

var database = firebase.database();
var attendanceRef = database.ref().child("Attendance");
attendanceRef.on('value', function(snapshot) {
	currentAttendance = snapshot.val();
	assembleAttendanceTable();
});

var bellScheduleRef = database.ref().child("Bell Schedule");
bellScheduleRef.on('value', function(snapshot) {
	currentBellSchedule = snapshot.val();
	assembleAttendanceTable();
});

var studentsRef = database.ref().child("Students");
studentsRef.on('value', function(snapshot) {
	currentStudents = snapshot.val();
	assembleAttendanceTable();
});

function setImgSrcForStudent(student) {
	if (currentStudents == undefined) { return; }
	firebase.storage().ref().child(currentStudents[student]["photo"]).getDownloadURL().then(function(url) {
		$("." + student.toLowerCase().replace(" ", "-")).each(function(i, obj) {
			obj.src = url;
		});
	});
}

function ymdToDate(ymd) {
	var d =  new Date();
	d.setFullYear(ymd.split("-")[0]);
	d.setMonth(ymd.split("-")[1] - 1);
	d.setDate(ymd.split("-")[2]);
	d.setHours(0);
	d.setMinutes(0);
	d.setSeconds(0);
	d.setMilliseconds(0);
	return d;
}

function calcAttendance(ymd, period, name) {
	if (currentBellSchedule == undefined) { return; }
	
	
	if (!(name in currentAttendance[ymd][period])) {
		return {
			"str" : "N/A",
			"c" : "gray"
			   };
	}
	timestamp = currentAttendance[ymd][period][name]["time"];
	
	var day_string = "";
	var date = ymdToDate(ymd);
	if (date.getDate() % 2 == 0) {
		day_string = "A Day";
	} else {
		day_string = "B Day";
	}
	// Get periods for day in one dict
	var periodTimes = {};
	for (var key in currentBellSchedule) {
		if (key == period) {
			periodTimes[key] = $.extend({}, currentBellSchedule[key]);
		} else if (key == day_string) {
			for (var day_period in currentBellSchedule[key]) {
				if (day_period == period) {
					periodTimes[period] = $.extend({}, currentBellSchedule[key][period]);
				}
			}
		}
	}
	periodTimes = periodTimes[period];
	// Convert timestring to epoch time
	for (var key in periodTimes) {
		var timeString = periodTimes[key];
		var idDate = new Date(date.getTime());
		var timeHours = parseInt(timeString.split(":")[0]);
		var timeMinutes = parseInt(timeString.split(":")[1].split(" ")[0]);
		var timeMeridianDesignation = timeString.split(" ")[1].toLowerCase();
		if (timeHours == 12 && timeMeridianDesignation == "am") {
			timeHours = 0;
		} else if (timeHours != 12 && timeMeridianDesignation == "pm") {
			timeHours += 12;
		}
		idDate.setHours(timeHours);
		idDate.setMinutes(timeMinutes);
		periodTimes[key] = idDate.getTime();
	}
	
	var classStart = periodTimes["Class Start"];
	var classEnd = periodTimes["Class End"];
	timestamp *= 1000;
	
	if (timestamp < classStart) {
		return {
			"str" : "On Time",
			"c" : "green",
			"timestamp" : timestamp
			   };
	} else if (timestamp >= classStart && timestamp <= classEnd) {
		return {
			"str" : "Tardy",
			"c" : "yellow",
			"timestamp" : timestamp
			   };
	} else {
		return {
			"str" : "Absent",
			"c" : "gray",
			"timestamp" : timestamp
			   };
	}
}

function hmsForTimestamp(timestamp) {
	var d = new Date();
	d.setTime(timestamp);
	var h = d.getHours();
	var m = d.getMinutes();
	var s = d.getSeconds();
	var ampm = "";
	if (h >= 12) {
		h = h - 12;
		ampm = "PM";
	} else {
		ampm = "AM";
	}
	if (h == 0) {
		h = 12;
	}
	
	m = m < 10 ? "0" + m : m;
	s = s < 10 ? "0" + s : s;
	
	return h + ":" + m + ":" + s + " " + ampm;
}

function noData() {
	$(".info").remove();
	$("#attendanceRoot").empty();
	$("body").append("<p class='info gray'>No data</p>");
}

function assembleAttendanceTable() {
	if (currentAttendance == undefined || currentBellSchedule == undefined || currentStudents == undefined) { 
		noData();
		return; 
	}
	var attRoot = $("#attendanceRoot");
	attRoot.empty();
	$(".info").remove();
	var attString = "";
	for (var ymd in currentAttendance) {
		attString += "<li>";
		attString += "<h4>" + ymd.split("-")[1] + "/" + ymd.split("-")[2] + "/" + ymd.split("-")[0] + "</h4>";
		attString += "<ul class='period-list'>";
		for (var period in currentAttendance[ymd]) {
			attString += "<li>"
			attString += "<h5>" + period + "</h5>";
			attString += "<table class='attendance-table'>";
			attString += "<tr><th>Name</th><th>Attendance</th></tr>";
			for (var name in currentStudents) {
				attString += "<tr>";
				attString += "<td>";
				attString += "<img class='" + name.toLowerCase().replace(" ", "-") + "'>";
				setImgSrcForStudent(name);
				attString += "<p>" + name + "</p>";
				attString += "</td>";
				var attendance = calcAttendance(ymd, period, name);
				var timeStr = attendance.timestamp ? " - " + hmsForTimestamp(attendance.timestamp) : "";
				attString += "<td class='" + attendance.c + "'>" + attendance.str + timeStr + "</td>";
				attString += "</tr>";
			}
			attString += "</table>";
			attString += "</li>";
		}
		attString += "</ul>";
		attString += "</li>";
	}
	attRoot.append(attString);
	var attRootNumLi = document.getElementById("attendanceRoot").getElementsByTagName("li").length;
	if (attRootNumLi < 2) {
		noData();
	}
}
