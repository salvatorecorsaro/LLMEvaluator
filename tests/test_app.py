import json

def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert b'LLM Evaluator' in response.data

def test_evaluate_missing_fields(client):
    response = client.post('/evaluate', data={})
    assert response.status_code == 400
    assert b'Missing required field' in response.data

def test_evaluate_with_data(client):
    data = {
        'model': 'llama_3_8b',
        'temperature': '0.5',
        'max_new_tokens': '100',
        'prompt': 'Write a poem about the sea.',
        'criteria': 'Score 10: Perfect. Score 1: Bad.',
        'iterations': '1',
        'expected_result': 'A beautiful poem about the sea.'
    }
    response = client.post('/evaluate', data=data)
    assert response.status_code == 200
    response_data = response.get_json()
    assert 'eval_results' in response_data
    assert 'avg_score' in response_data
    assert 'final_verdict' in response_data

def test_upload_csv_no_file(client):
    response = client.post('/upload_csv')
    assert response.status_code == 400
    assert b'No file part in the request' in response.data

def test_upload_csv_with_file(client, tmp_path):
    csv_content = """model,temperature,max_new_tokens,prompt,criteria,iterations,expected_result
    llama_3_8b,0.5,100,Write a poem about the sea.,Score 10: Perfect. Score 1: Bad.,1,A beautiful poem about the sea.
    """
    csv_file = tmp_path / "test.csv"
    csv_file.write_text(csv_content)

    with open(csv_file, 'rb') as f:
        response = client.post('/upload_csv', data={'file': f})
        assert response.status_code == 200
        response_data = response.get_json()
        assert isinstance(response_data, list)
        assert 'model' in response_data[0]
        assert 'eval_results' in response_data[0]

def test_evaluate_stream(client):
    data = {
        'model': 'llama_3_8b',
        'temperature': '0.5',
        'max_new_tokens': '100',
        'prompt': 'Write a poem about the sea.',
        'criteria': 'Score 10: Perfect. Score 1: Bad.',
        'iterations': '1',
        'expected_result': 'A beautiful poem about the sea.'
    }
    response = client.post('/evaluate_stream', data=data)
    assert response.status_code == 200
    assert response.headers['Content-Type'] == 'text/event-stream'

    stream_data = b""
    for line in response.response:
        stream_data += line

    assert b'iterations completed' in stream_data or b'Error occurred' in stream_data
