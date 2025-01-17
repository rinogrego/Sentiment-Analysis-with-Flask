from flask import Flask, request, render_template, jsonify

from utils import clean_text, create_input, plot_sentiment
from model import model

from keras import backend as K
import datetime

app = Flask(__name__)

@app.route('/', methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return render_template('index.html')
    elif request.method == "POST":
        s = datetime.datetime.now()
        raw_text = request.form['input_text']
        text = clean_text(raw_text)
        token, mask = create_input([text])
        
        sentiment_result = model([token, mask], training=False)
        happy = float(sentiment_result[0][0][0])
        neutral = float(sentiment_result[0][0][1])
        disappointment = float(sentiment_result[0][0][2])
        advice = float(sentiment_result[1][0][0])
        curiosity = float(sentiment_result[1][0][1])
        complaint = float(sentiment_result[1][0][2])
        
        sentiment_viz = plot_sentiment([happy, neutral, disappointment, advice, curiosity, complaint])
        
        K.clear_session()
        print("  Text       :", raw_text)
        print("  Time spent :", datetime.datetime.now() - s)
        
        return render_template(
            'index.html',
            raw_text=raw_text,
            sentiment_viz=sentiment_viz,
            skor_happy=happy,
            skor_neutral=neutral,
            skor_disappointment=disappointment,
            skor_advice=advice,
            skor_curiosity=curiosity,
            skor_complaint=complaint           
        )


@app.route('/api/sentiment', methods=["POST"])
def api_sentiment():
    
    r = request.get_json(force=True)
    try:
        raw_texts = r['text']
    except KeyError:
        return jsonify({"error_message": "Text not found. Please provided a proper json structure."})
    # raw texts limitation. could be modified
    if len(raw_texts) > 5:
        return jsonify({"error_message: Please provide no more than 5 texts"})
    texts = [clean_text(raw_text) for raw_text in raw_texts]
    token_mask_inputs = create_input(texts)
    
    happy = []
    neutral = []
    disappointment = []
    advice = []
    curiosity = []
    complaint = []
    
    sentiment_results = model.predict(token_mask_inputs)
    for idx in range(len(sentiment_results[0])):
        # multi-class result
        happy.append(float(sentiment_results[0][idx][0]))
        neutral.append(float(sentiment_results[0][idx][1]))
        disappointment.append(float(sentiment_results[0][idx][2]))
        # multi-label result
        advice.append(float(sentiment_results[1][idx][0]))
        curiosity.append(float(sentiment_results[1][idx][1]))
        complaint.append(float(sentiment_results[1][idx][2]))
    
    result = []
    for i, raw_text in enumerate(raw_texts):
        result.append({
            'id': i,
            'text': raw_text,
            'sentiment': {
                'multi-class': {
                    'happy': happy[i],
                    'neutral': neutral[i],
                    'disappointment': disappointment[i],
                },
                'multi-label': {   
                    'advice': advice[i],
                    'curiosity': curiosity[i],
                    'complaint': complaint[i],
                }
            }
        })
        
    K.clear_session()
    
    return jsonify(results=result)


if __name__ == '__main__':
    # app.run(debug=True, use_reloader=False)
    app.run(debug=True, port=5000, host='0.0.0.0')