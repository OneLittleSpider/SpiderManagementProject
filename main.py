from flask import Flask, render_template, request, jsonify
from google.cloud import datastore

app = Flask(__name__)
datastore_client = datastore.Client()

@app.route("/tool")
def ToToolPage():
    return render_template('tool.html')

@app.route("/")
@app.route("/home")
def ToHomePage():
    return render_template('home.html')

@app.route('/', methods=['GET'])
def home():
    """Display homepage with form and list of items"""
    # Query all items
    query = datastore_client.query(kind='task')
    items = []
    for entity in query.fetch():
        item = dict(entity)
        item['id'] = entity.key.id
        items.append(item)
    return render_template('home.html', items=items)

@app.route('/create', methods=['POST'])
def create():
     """Handle form submission to create new item"""
     try:
         # task = request.form.get('task')
         # details = request.form.get('details')

         # Create new entity
         key = datastore_client.key('Item')
         entity = datastore.Entity(key=key)
         entity.update({
             'task': "Enter Task",
             'details': "Enter Details"
         })
         datastore_client.put(entity)
         return jsonify({"message": "Success"}, 400)
     except Exception as e:
         return f"Error: {str(e)}", 500


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8080, debug=True)
