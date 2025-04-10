document.getElementById('submitBtn').addEventListener('click', async () => {
    const userInput = document.getElementById('userInput').value.trim();
    const responseDiv = document.getElementById('response');

    if (userInput === "") {
        alert("Please enter a question.");
        return;
    }

    responseDiv.textContent = "Thinking...";

    try {
        const apiResponse = await getOpenAIResponse(userInput);
        responseDiv.textContent = apiResponse;
    } catch (error) {
        responseDiv.textContent = "Error: Unable to fetch response.";
        console.error(error);
    }
});

async function getOpenAIResponse(prompt) {
    const apiKey = 'your_openai_api_key';  // Replace with your OpenAI API key
    const apiUrl = 'https://api.openai.com/v1/completions';

    const requestBody = {
        model: 'text-davinci-003',  // Specify the model
        prompt: prompt,
        max_tokens: 150,
        temperature: 0.7
    };

    const response = await fetch(apiUrl, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${apiKey}`,
        },
        body: JSON.stringify(requestBody),
    });

    const data = await response.json();
    return data.choices[0].text.trim();
}
