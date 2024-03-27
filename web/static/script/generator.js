// Submit form asynchronously
function submitForm(formId, url) {
    var formData = new FormData(document.getElementById(formId)); // Get form data

    // Display loading animation
    var loading = document.getElementById("loading");
    loading.style.display = "flex";

    fetch(url, {
        method: 'POST',
        body: formData
    })
    .then(response => response.text())
    .then(result => {
        // Log the response text
        console.log('Response from server:', result);

        // Update result section with the response
        var resultSection = document.getElementById('resultSection');
        var responseParagraph = document.getElementById('response');
        if (resultSection && responseParagraph) {
            resultSection.style.display = 'block'; // Display the result section
            responseParagraph.textContent = result; // Update the response content
        } else {
            console.error('Result section or response paragraph not found in the DOM');
        }

        // Hide loading animation
        loading.style.display = "none";
    })
    .catch(error => {
        console.error('Error submitting form:', error);
        // Hide loading animation in case of error
        loading.style.display = "none";
    });
}


// Handle form submission for text prompt
document.getElementById('text-prompt-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission behavior
    submitForm('text-prompt-form', '/generate/tprompt'); // Submit form asynchronously
});

// Handle form submission for random text prompt
document.getElementById('random-text-prompt-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission behavior
    submitForm('random-text-prompt-form', '/generate/trandom'); // Submit form asynchronously
});

// Handle form submission for image prompt
document.getElementById('image-prompt-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission behavior
    submitForm('image-prompt-form', '/generate/iprompt'); // Submit form asynchronously
});

// Handle form submission for random image prompt
document.getElementById('random-image-prompt-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission behavior
    submitForm('random-image-prompt-form', '/generate/irandom'); // Submit form asynchronously
});

// Handle form submission for reverse image prompt
document.getElementById('image-upload-form').addEventListener('submit', function(event) {
    event.preventDefault(); // Prevent default form submission behavior
    submitForm('image-upload-form', '/generate/image'); // Submit form asynchronously
});


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