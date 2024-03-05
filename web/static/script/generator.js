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

function previewImage() {
	var input = document.querySelector('input[name="image"]');
	var preview = document.getElementById('preview-image');
	
	input.addEventListener('change', function () {
		var file = input.files[0];

		if (file) {
			var reader = new FileReader();

			reader.onload = function (e) {
				preview.src = e.target.result;
				document.body.setAttribute('data-image-selected', 'true');
			};

			reader.readAsDataURL(file);
		} else {
			preview.src = "{{ url_for('static', filename='icon/favicon.ico') }}";
			document.body.setAttribute('data-image-selected', 'false');
		}
	});
}

document.addEventListener("DOMContentLoaded", function () {
	previewImage();
});