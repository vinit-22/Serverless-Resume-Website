// Replace this with your actual API Gateway Invoke URL from Step 5
// Example: https://abc123xyz.execute-api.us-east-1.amazonaws.com/count
const API_URL = "https://eznxvkojk5.execute-api.us-east-1.amazonaws.com/count";

async function updateVisitorCount() {
  const counterEl = document.getElementById("counter");

  try {
    const response = await fetch(API_URL);

    if (!response.ok) {
      throw new Error(`Request failed with status ${response.status}`);
    }

    const data = await response.json();
    counterEl.textContent = data.count;
  } catch (error) {
    console.error("Error fetching visitor count:", error);
    counterEl.textContent = "unavailable";
  }
}

document.addEventListener("DOMContentLoaded", updateVisitorCount);
