const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');

fetch('/share_prompt', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrfToken
    },
    body: JSON.stringify(data)
})
