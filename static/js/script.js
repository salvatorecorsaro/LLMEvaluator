// Export as CSV
document.getElementById('export-csv').addEventListener('click', function() {
    const table = document.querySelector('table');
    const rows = Array.from(table.querySelectorAll('tr'));

    const csvContent = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('th,td'));
        return cells.map(cell => {
            let cellValue = cell.textContent.trim();
            cellValue = cellValue.replace(/"/g, '""');
            cellValue = `"${cellValue}"`;
            return cellValue;
        }).join(',');
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

document.querySelectorAll('.tab').forEach(tab => {
    tab.addEventListener('click', function() {
        document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(tc => tc.classList.remove('active'));

        tab.classList.add('active');
        document.getElementById(tab.getAttribute('data-tab')).classList.add('active');
    });
});

document.getElementById('evaluation-form').addEventListener('submit', function(e) {
    e.preventDefault();

    document.getElementById('export-csv').classList.add('hidden');

    const formData = new FormData(this);

    // Show a loading indicator
    const resultTableDiv = document.getElementById('result-table');
    resultTableDiv.innerHTML = '<p><span class="spinner"></span> Processing inputs...</p>';

    fetch('/evaluate_stream', {
        method: 'POST',
        body: new URLSearchParams(formData)
    })
    .then(response => {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let result = '';

        reader.read().then(function processText({ done, value }) {
            if (done) {
                try {
                    const data = JSON.parse(result.split("\n").filter(line => line.trim().startsWith("data:")).pop().substring(5));
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
                    });

                    tableHTML += `
                            </tbody>
                        </table>
                        <p>Average Score: ${data.avg_score}</p>
                        <p>Final Verdict: ${data.final_verdict}</p>
                    `;

                    resultTableDiv.innerHTML = tableHTML;
                    document.getElementById('export-csv').classList.remove('hidden');
                } catch (e) {
                    console.error('Error parsing final response:', e);
                    resultTableDiv.innerHTML = '<p>Error processing results. Please try again.</p>';
                }
                return;
            }

            result += decoder.decode(value, { stream: true });
            let progress = result.split("\n").filter(line => line.trim().startsWith("data:")).pop().substring(5);
            resultTableDiv.innerHTML = `<p><span class="spinner"></span> ${progress} iterations completed</p>`;
            reader.read().then(processText);
        });
    })
    .catch(error => {
        console.error('Error:', error);
        resultTableDiv.innerHTML = '<p>Error occurred. Please try again.</p>';
    });
});

document.getElementById('csv-upload-form').onsubmit = function(event) {
    event.preventDefault();
    var formData = new FormData(this);

    document.getElementById('spinner-csv').style.display = 'block';

    fetch('/upload_csv', {
        method: 'POST',
        body: formData
    })
    .then(response => response.blob())
    .then(blob => {
        document.getElementById('spinner-csv').style.display = 'none';
        var url = window.URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = 'evaluation_results.csv';
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
    })
    .catch(error => {
        document.getElementById('spinner').style.display = 'none';
        console.error('Error:', error);
    });
};

document.getElementById('clear-fields').onclick = function() {
    document.getElementById('prompt').value = '';
    document.getElementById('criteria').value = '';
    document.getElementById('expected_result').value = '';
};

document.addEventListener('DOMContentLoaded', function() {
    fetch('static/js/defaults.json')
        .then(response => response.json())
        .then(data => {
            document.getElementById('model').value = data.model;
            document.getElementById('temperature').value = data.temperature;
            document.getElementById('max_new_tokens').value = data.max_new_tokens;
            document.getElementById('prompt').value = data.prompt;
            document.getElementById('criteria').value = data.criteria;
            document.getElementById('expected_result').value = data.expected_result;
            document.getElementById('iterations').value = data.iterations;
        })
        .catch(error => console.error('Error loading defaults:', error));
});