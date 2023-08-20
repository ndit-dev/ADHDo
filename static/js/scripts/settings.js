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