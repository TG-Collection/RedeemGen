document.getElementById("generateButton").onclick = function() {
    var accessKey = document.getElementById("accessKeyInput").value;
    fetch(`/?access_key=${accessKey}&action=generate`)
        .then(response => response.json())
        .then(data => {
            if (data.license_code) {
                alert(`Generated License Code: ${data.license_code}`);
            } else {
                alert(`Error: ${data.message}`);
            }
        })
        .catch(error => console.error('Error:', error));
}
