from shutil import copyfile
from flask import Flask, request, render_template
from harmony import analyze_file, rules, Report

app = Flask(__name__)
app.debug = True

@app.route('/', methods=['GET', 'POST'])
def upload_file():
  if request.method == 'POST':
    f = request.files['file']
    report = analyze_file(f.read())
    return render_template('results.html', errors=report.errors, key=report.key,
        chords=report.chords)
  else:
    return render_template('home.html')

@app.route('/vexflow.js')
def send_vexflow():
  return app.send_static_file('vexflow.js')

@app.route('/css/site.css')
def send_css():
  return app.send_static_file('css/site.css')

if __name__ == '__main__':
  app.run()

