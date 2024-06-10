from flask import Flask, render_template, request, jsonify
from langchain.evaluation import load_evaluator
from langchain_openai import ChatOpenAI, OpenAI

from langchain_aws import BedrockLLM
from langchain_community.chat_models import BedrockChat

from langchain.schema import HumanMessage
import dotenv
import re
import logging

dotenv.load_dotenv()
app = Flask(__name__)

logging.basicConfig(level=logging.DEBUG)


def get_llm(model_name, temperature):
    if model_name == 'gpt_3.5':
        return ChatOpenAI(model_name="gpt-3.5-turbo-0125", temperature=temperature, max_tokens=1024)
    elif model_name == 'gpt_4':
        return ChatOpenAI(model_name="gpt-4-turbo", temperature=temperature, max_tokens=1024)
    elif model_name == 'gpt_4o':
        return ChatOpenAI(model_name="gpt-4o", temperature=temperature, max_tokens=1024)
    elif model_name == 'llama_3_8b':
        return BedrockLLM(model_id="meta.llama2-13b-chat-v1")
    elif model_name == 'llama_3_70b':
        return BedrockChat(model_id="meta.llama3-70b-instruct-v1")
    elif model_name == 'claude_3_sonnet':
        return BedrockChat(model_id="anthropic.claude-3-sonnet-20240229-v1:0")
    elif model_name == 'claude_3_haiku':
        return BedrockChat(model_id="anthropic.claude-3-haiku-20240307-v1:0")
    elif model_name == 'claude_3_opus':
        return BedrockChat(model_id="anthropic.claude-3-opus-20240229-v1:0")
    elif model_name == 'claude_v2.1_200k':
        return BedrockChat(model_id="anthropic.claude-v2")
    elif model_name == 'amazon_titan_text_g1':
        return BedrockLLM(model_id="amazon.titan-text-express-v1")
    else:
        return OpenAI(temperature=temperature, max_tokens=1024)  # default model


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluate', methods=['POST'])
def evaluate():
    model = request.form['model']
    temperature = float(request.form['temperature'])
    prompt = request.form['prompt']
    criteria = request.form['criteria']
    iterations = int(request.form['iterations'])
    expected_result = request.form['expected_result']

    accuracy_criteria = {
        "accuracy": criteria
    }

    evaluator = load_evaluator(
        "labeled_score_string",
        criteria=accuracy_criteria,
    )

    llm = get_llm(model, temperature)
    eval_results = []

    for i in range(iterations):
        try:
            if isinstance(llm, (ChatOpenAI, BedrockChat)):
                messages = [HumanMessage(content=prompt)]
                logging.debug(f"Sending messages to model: {messages}")
                response = llm(messages)
                prediction = response[0].content if isinstance(response, list) else response.content
            elif isinstance(llm, BedrockLLM):
                logging.debug(f"Sending prompt to model: {prompt}")
                prediction = llm(prompt)
            else:
                logging.debug(f"Sending prompt to model: {prompt}")
                prediction = llm(prompt)

            logging.debug(f"Received prediction: {prediction}")

            eval_result = evaluator.evaluate_strings(prediction=prediction, input=prompt, reference=expected_result)
            score_match = re.search(r'\[\[(\d+)]]', eval_result['reasoning'])
            score = int(score_match.group(1)) if score_match else None
            eval_results.append({
                'iteration': i + 1,
                'prediction': prediction,
                'score': score,
                'reason': eval_result['reasoning']
            })
        except ValueError as e:
            logging.error(f"Error during evaluation: {e}")
            eval_results.append({
                'iteration': i + 1,
                'prediction': None,
                'score': None,
                'reason': str(e)
            })

    scores = [result["score"] for result in eval_results if result["score"] is not None]
    avg_score = sum(scores) / len(scores) if scores else None

    final_verdict_prompt = f"Final verdict for the evaluation of {model} based on the given criteria and {iterations} iterations:"
    try:
        if isinstance(llm, (ChatOpenAI, BedrockChat)):
            final_verdict_messages = [HumanMessage(content=final_verdict_prompt)]
            logging.debug(f"Sending final verdict prompt to model: {final_verdict_messages}")
            final_verdict_response = llm(final_verdict_messages)
            final_verdict = final_verdict_response.content if not isinstance(final_verdict_response, list) else \
                final_verdict_response[0].content
        elif isinstance(llm, BedrockLLM):
            logging.debug(f"Sending final verdict prompt to model: {final_verdict_prompt}")
            final_verdict = llm(final_verdict_prompt)
        else:
            logging.debug(f"Sending final verdict prompt to model: {final_verdict_prompt}")
            final_verdict = llm(final_verdict_prompt)
    except ValueError as e:
        logging.error(f"Error during final verdict generation: {e}")
        final_verdict = str(e)

    return jsonify({
        'eval_results': eval_results,
        'avg_score': avg_score,
        'final_verdict': final_verdict,
        'temperature': temperature
    })


if __name__ == '__main__':
    app.run(debug=True)
