function validateForm() {
	var userInputText = document.getElementById("user_input_text").value.trim();
	var userInputImage = document.getElementById("user_input_image").value.trim();
	var loading = document.getElementById("loading");

	if (userInputText !== "" || userInputImage !== "") {
		// Show loading animation
		loading.style.display = "flex";
		return true;
	} else {
		alert("Please fill in at least one of the input sections.");
		return false;
	}
}

function hideLoading() {
	var loading = document.getElementById("loading");
	loading.style.display = "none";
}        

function copyToClipboard() {
	var responseText = document.getElementById("response");
	var textArea = document.createElement("textarea");
	textArea.value = responseText.innerText;
	document.body.appendChild(textArea);
	textArea.select();
	document.execCommand('copy');
	document.body.removeChild(textArea);
	alert("Response copied to clipboard!");
}