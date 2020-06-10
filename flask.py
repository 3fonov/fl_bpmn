from flask import Flask,render_template, request,send_file
import mysql.connector
from bpmn import generate_bpmn
app = Flask(__name__)

@app.route('/bpmn/', methods=['GET', 'POST'])
def bpmn():
    if request.method == 'POST':
        data = request.form['data']
        generate_bpmn(data)
        return send_file('bpmn.xml',
                as_attachment=True)
    return render_template('bpmn.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
