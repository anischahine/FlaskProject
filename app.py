from flask import Flask, render_template, request, jsonify, url_for
import os
from flask_cors import CORS
import pymysql

app = Flask(__name__)
CORS(app)  # Enable CORS

# MySQL Configuration
db = pymysql.connect(
    host           ='sql5.freesqldatabase.com',
    user           ='sql5770533',
    password       ='96lRlhhNBT',
    database       ='sql5770533',
)
cursor = db.cursor()

# index
@app.route('/')
def home():
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    categories_data = []

    for category in categories:
        cursor.execute("SELECT id, name FROM subcategories WHERE category_id = %s", (category[0],))
        subcategories = cursor.fetchall()
        categories_data.append({
            'category_id': category[0],
            'category_name': category[1],
            'subcategories': subcategories
        })

    cursor.execute("""
        SELECT p.id, p.name, p.price, p.image_url
        FROM products p
    """)
    all_products = cursor.fetchall()

    return render_template('index.html', categories=categories_data, products=all_products)

@app.route('/filter-products', methods=['GET'])
def filter_products():
    category_id = request.args.get('category')
    subcategory_id = request.args.get('subcategory')

    try:
        query = """
            SELECT p.id, p.name, p.price, p.image_url
            FROM products p
            JOIN subcategories s ON p.subcategory_id = s.id
        """
        filters = []
        values = []

        if category_id:
            filters.append("s.category_id = %s")
            values.append(category_id)
        if subcategory_id:
            filters.append("p.subcategory_id = %s")
            values.append(subcategory_id)

        if filters:
            query += " WHERE " + " AND ".join(filters)

        cursor.execute(query, values)
        products = cursor.fetchall()

        products_list = []
        for product in products:
            products_list.append({
                'id': product[0],
                'name': product[1],
                'price': float(product[2]),
                'image_url': url_for('static', filename=product[3]) if product[3] else ""
            })

        return jsonify(products_list)

    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    # Fetch product
    cursor.execute("SELECT * FROM products WHERE id = %s", (product_id,))
    product = cursor.fetchone()
    print("API KEY:", os.getenv("OPENAI_API_KEY"))

    if not product:
        return "Product not found", 404

    # Parse specs
    import json
    specs = json.loads(product[7]) if product[7] else {}

    # Fetch categories + subcategories (for sidebar)
    cursor.execute("SELECT id, name FROM categories")
    categories = cursor.fetchall()

    categories_data = []
    for category in categories:
        cursor.execute("SELECT id, name FROM subcategories WHERE category_id = %s", (category[0],))
        subcategories = cursor.fetchall()
        categories_data.append({
            'category_id': category[0],
            'category_name': category[1],
            'subcategories': subcategories
        })

    return render_template(
        'product_detail.html',
        product=product,
        specs=specs,
        categories=categories_data
    )

@app.route('/chat', methods=['POST'])
def chat():
    user_message = request.json.get('message', '')

    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You're a helpful assistant for an e-commerce website."},
                {"role": "user", "content": user_message}
            ],
            max_tokens=200,
            temperature=0.7
        )

        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"⚠️ OpenAI error: {str(e)}"

    return jsonify(reply=reply)

@app.route('/chat', methods=['POST'])
def chat():
    message = request.json.get('message', '').lower()

    reply = "🤖 I'm not sure how to help with that. Could you rephrase?"

    responses = {
        'order': "📦 You can track your order in your account > Orders.",
        'return': "🔄 We accept returns within 14 days of delivery.",
        'refund': "💸 Refunds are processed within 5 business days.",
        'laptop': "💻 Yes! We have a variety of laptops in the 'Laptops' section.",
        'phone': "📱 Check out our smartphones under the 'Smartphones' category.",
        'support': "📩 Reach our support at support@yourshop.com.",
        'email': "📧 Our email is support@yourshop.com."
    }

    for keyword, response in responses.items():
        if keyword in message:
            reply = response
            break

    return jsonify(reply=reply)

if __name__ == '__main__':
    app.run(debug=True)
