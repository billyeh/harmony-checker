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
    return render_template('results.html', errors=report.errors)
  else:
    return '''
      <!doctype html>
      <h1>Upload new File</h1>
      <form action="" method=post enctype=multipart/form-data>
        <p><input type=file name=file>
           <input type=submit value=Upload>
      </form>
      '''

@app.route('/vexflow.js')
def send_vexflow():
  return app.send_static_file('vexflow.js')

if __name__ == '__main__':
  app.run()

