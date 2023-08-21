//
// Set the time for resetting the completed status of tasks
//
document.getElementById('updateResetTimeBtn').addEventListener('click', function() {
    const resetTimeInput = document.getElementById('resetTime');
    const chosenTime = resetTimeInput.value;

    fetch('/update-reset-time', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            resetTime: chosenTime
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status) {
            alert('Reset time updated!');
        } else {
            alert('Error updating reset time.');
        }
    });
});

// Fetch the reset time value and set it to the input
fetch('/get-settings')
    .then(response => response.json())
    .then(data => {
        const resetTimeInput = document.getElementById('resetTime');
        let hourStr = String(data.resetTime.hour).padStart(2, '0');
        let minuteStr = String(data.resetTime.minute).padStart(2, '0');
        
        resetTimeInput.value = `${hourStr}:${minuteStr}`;
    });