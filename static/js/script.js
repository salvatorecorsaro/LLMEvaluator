document.getElementById('evaluation-form').addEventListener('submit', function(e) {
    e.preventDefault();

    const formData = new FormData(this);

    // Show a loading indicator
    const resultTableDiv = document.getElementById('result-table');
    resultTableDiv.innerHTML = '<p>Processing... <span class="spinner"></span></p>';

    fetch('/evaluate', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        let tableHTML = `
            <table>
                <thead>
                    <tr>
                        <th>Date</th>
                        <th>Temperature</th>
                        <th>Iteration</th>
                        <th>Prediction</th>
                        <th>Score</th>
                        <th>Reason</th>
                    </tr>
                </thead>
                <tbody>
        `;

        data.eval_results.forEach(result => {
            tableHTML += `
                <tr>
                    <td>${new Date().toLocaleDateString()}</td>
                    <td>${data.temperature}</td>
                    <td>${result.iteration}</td>
                    <td>${result.prediction}</td>
                    <td>${result.score}</td>
                    <td>${result.reason}</td>
                </tr>
            `;

            // Update the table with the current iteration's result
            resultTableDiv.innerHTML = tableHTML;
        });

        tableHTML += `
                </tbody>
            </table>
            <p>Average Score: ${data.avg_score}</p>
            <p>Final Verdict: ${data.final_verdict}</p>
        `;

        resultTableDiv.innerHTML = tableHTML;
    })
    .catch(error => {
        console.error('Error:', error);
    });
});

// Export as CSV
document.getElementById('export-csv').addEventListener('click', function() {
    const table = document.querySelector('table');
    const rows = Array.from(table.querySelectorAll('tr'));

    const csvContent = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('th,td'));
        return cells.map(cell => cell.textContent).join(',');
    }).join('\n');

    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', 'evaluation_results.csv');
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
});
