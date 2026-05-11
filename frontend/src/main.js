const BACKEND_URL = "http://localhost:5000";
const form = document.querySelector("#upload-form");
const fileInput = document.querySelector("#bom-file");
const result = document.querySelector("#result");
const backendStatus = document.querySelector("#backend-status");

async function fetchHealth() {
  try {
    const response = await fetch(`${BACKEND_URL}/api/health`);
    const body = await response.json();
    backendStatus.textContent = body.status === "ok" ? "online" : "offline";
  } catch (error) {
    backendStatus.textContent = "offline";
  }
}

async function uploadFile(event) {
  event.preventDefault();

  if (!fileInput.files.length) {
    result.textContent = "Please choose an Excel file first.";
    return;
  }

  const formData = new FormData();
  formData.append("file", fileInput.files[0]);

  result.textContent = "Uploading and parsing...";

  try {
    const response = await fetch(`${BACKEND_URL}/api/parse`, {
      method: "POST",
      body: formData,
    });

    const body = await response.json();
    if (!response.ok) {
      result.textContent = `Error: ${body.error || response.statusText}`;
      return;
    }

    result.textContent = JSON.stringify(body, null, 2);
  } catch (error) {
    result.textContent = `Request failed: ${error.message}`;
  }
}

form.addEventListener("submit", uploadFile);
fetchHealth();
