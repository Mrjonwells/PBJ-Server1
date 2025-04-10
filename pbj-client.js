
async function askPBJ() {
  const question = document.getElementById('pbj-question').value;
  const responseDiv = document.getElementById('pbj-response');
  responseDiv.innerHTML = "PBJ is thinking...";

  try {
    const res = await fetch("https://pbj-server1.onrender.com/pbj", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: question })
    });

    const data = await res.json();
    responseDiv.innerHTML = data.response || "No response received.";
  } catch (error) {
    responseDiv.innerHTML = "Error: " + error.message;
  }
}
