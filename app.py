from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Author, Book, Review
from scrape_books import scrape_and_store_books

app = Flask(name)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///books.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db.init_app(app)
migrate = Migrate(app, db)

@app.route('/books', methods=['GET'])
def get_all_books():
    books = Book.query.join(Author).all()
    return jsonify([{
        'id': book.id,
        'title': book.title,
        'publication_year': book.publication_year,
        'author': book.author.name,
        'reviews': [{'id': review.id, 'rating': review.rating, 'comment': review.comment} for review in book.reviews]
    } for book in books])

@app.route('/books/<int:id>', methods=['GET'])
def get_book(id):
    book = Book.query.get_or_404(id)
    return jsonify({
        'id': book.id,
        'title': book.title,
        'publication_year': book.publication_year,
        'author': book.author.name,
        'reviews': [{'id': review.id, 'rating': review.rating, 'comment': review.comment} for review in book.reviews]
    })

@app.route('/books', methods=['POST'])
def create_book():
    data = request.get_json()
    if not data or not all(key in data for key in ['title', 'publication_year', 'author_id']):
        return jsonify({'error': 'Missing required fields'}), 400
    author = Author.query.get(data['author_id'])
    if not author:
        return jsonify({'error': 'Author not found'}), 404
    book = Book(title=data['title'], publication_year=data['publication_year'], author_id=data['author_id'])
    db.session.add(book)
    db.session.commit()
    return jsonify({'id': book.id, 'title': book.title, 'publication_year': book.publication_year, 'author_id': book.author_id}), 201

@app.route('/books/<int:id>', methods=['PATCH'])
def update_book(id):
    book = Book.query.get_or_404(id)
    data = request.get_json()
    if not data:
        return jsonify({'error': 'No data provided'}), 400
    if 'title' in data:
        book.title = data['title']
    if 'publication_year' in data:
        book.publication_year = data['publication_year']
    db.session.commit()
    return jsonify({'id': book.id, 'title': book.title, 'publication_year': book.publication_year})

@app.route('/books/<int:id>', methods=['DELETE'])
def delete_book(id):
    book = Book.query.get_or_404(id)
    db.session.delete(book)
    db.session.commit()
    return jsonify({'message': 'Book deleted'})

@app.route('/scrape', methods=['GET'])
def scrape_books():
    try:
        added_books, added_authors = scrape_and_store_books()
        return jsonify({
            'message': 'Scraping completed',
            'books_added': added_books,
            'authors_added': added_authors
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if name == 'main':
    app.run(debug=True)