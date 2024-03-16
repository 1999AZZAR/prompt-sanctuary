// validate form
function validateForm() {
	var far1 = document.getElementById("user_input_text").value.trim();
	var far2 = document.getElementById("parameter0").value.trim();
	var far3 = document.getElementById("user_input_image").value.trim();
	var loading = document.getElementById("loading");

	// validate form
	if (far1 !== "" || far2 !== "" || far3 !== "") {
		loading.style.display = "flex";
		return true;
	} else {
		alert("Please fill in at least one of the input sections.");
		return false;
	}
}

// copy the response to the clipboard
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

// image input preview
function previewImage() {
	var input = document.querySelector('input[name="image"]');
	var preview = document.getElementById('preview-image');

	input.addEventListener('change', function () {
		var file = input.files[0];

		// preview image 
		if (file) {
			var reader = new FileReader();

			reader.onload = function (e) {
				preview.src = e.target.result;
				document.body.setAttribute('data-image-selected', 'true');
			};

			reader.readAsDataURL(file);
			// 
		} else {
			preview.src = "{{ url_for('static', filename='icon/favicon.ico') }}";
			document.body.setAttribute('data-image-selected', 'false');
		}
	});
}

// 
document.addEventListener("DOMContentLoaded", function () {
	previewImage();
})

// 
function loadingAnimation() {
	var loading = document.getElementById("loading");
	loading.style.display = "flex";

	return true;
}