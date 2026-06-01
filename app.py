import sys
import urllib.parse
import werkzeug.urls
werkzeug.urls.url_decode = urllib.parse.parse_qsl
sys.modules['werkzeug.urls'].url_decode = urllib.parse.parse_qsl
werkzeug.urls.url_encode = urllib.parse.urlencode
sys.modules['werkzeug.urls'].url_encode = urllib.parse.urlencode



#Meu codigo começa aqui

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_login import LoginManager, login_user, UserMixin, login_required, logout_user, current_user



app = Flask(__name__)
app.config['SECRET_KEY'] = "minha_chave_123"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'

db = SQLAlchemy(app)
CORS(app)
login_manager = LoginManager(app)
login_manager.init_app(app)
login_manager.login_view = 'login'


#Definindo a Class User (id, username e password), e a relação com o carrinho de compras (cart) usando SQLAlchemy e Flask-Login para autenticação de usuários.

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), nullable=False, unique=True)
    password = db.Column(db.String(80), nullable=False)
    cart = db.relationship('cartItem', backref='user', lazy=True)
                           
#Definindo a rota de login para o User, onde o usuário pode enviar suas credenciais (username e password) para autenticação. Se as credenciais forem válidas, o usuário será autenticado e uma mensagem de sucesso será retornada. Caso contrário, uma mensagem de erro será retornada.

@app.route('/login', methods=['POST'])
def login():
    data = request.json

    if 'username' in data and 'password' in data:
        user = User.query.filter_by(username=data['username'], password=data['password']).first()
        if user and data.get('password') == user.password:
            login_user(user)
            return jsonify({'message': 'Login successful'})
    return jsonify({'error': 'Unauthorized. Invalid credentials'}), 400

#Definindo a rota de logout para o User, onde o usuário pode sair da sua sessão. Se o usuário estiver autenticado, ele será desautenticado e uma mensagem de sucesso será retornada.

@app.route('/logout', methods=['POST'])
@login_required 
def logout():
    logout_user()
    return jsonify({'message': 'Logout successful'})

#Definindo a função de carregamento de usuário para autenticação

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
     
#Definindo a Class Produto (id, name, price e description), que representa os produtos disponíveis para compra na aplicação. Cada produto tem um identificador único (id), um nome (name), um preço (price) e uma descrição (description). A classe Product é mapeada para uma tabela no banco de dados usando SQLAlchemy, permitindo que os produtos sejam armazenados e recuperados facilmente.

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    price = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)

#Definindo a Class Carrinho de compras, que representa os itens que um usuário adiciona ao seu carrinho de compras. Cada item no carrinho é representado por uma instância da classe cartItem, que tem um identificador único (id), uma referência ao usuário que adicionou o item (user_id) e uma referência ao produto adicionado (product_id). A classe cartItem é mapeada para uma tabela no banco de dados usando SQLAlchemy, permitindo que os itens do carrinho sejam armazenados e recuperados facilmente.
class cartItem(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'), nullable=False)



#Definindo a rota para adicionar um novo produto, onde um usuário autenticado pode enviar os detalhes do produto (name, price e description) para criar um novo produto na aplicação. Se os dados do produto forem válidos, o produto será adicionado ao banco de dados e uma mensagem de sucesso será retornada. Caso contrário, uma mensagem de erro será retornada indicando que os dados do produto são inválidos.
@app.route('/api/products/add', methods=['POST'])
@login_required
def add_product():
    data = request.json
    if 'name' in data and 'price' in data:
        product = Product(name=data['name'], price=data['price'], description=data.get('description', ''))
        db.session.add(product)
        db.session.commit()
        return jsonify({'message': 'Product added successfully'})
    return jsonify({'error': 'Invalid product data'}), 400  

#Definindo a rota para deletar um produto, onde um usuário autenticado pode enviar o ID do produto para excluí-lo da aplicação. Se o produto for encontrado, ele será deletado do banco de dados e uma mensagem de sucesso será retornada. Caso contrário, uma mensagem de erro será retornada indicando que o produto não foi encontrado.
@app.route('/api/products/delete/<int:product_id>', methods=['DELETE'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product:
        db.session.delete(product)
        db.session.commit()
        return jsonify({'message': 'Product deleted successfully'})
    return jsonify({'error': 'Product not found'}), 404

#Definindo a rota para obter os detalhes de um produto, onde um usuário pode enviar o ID do produto para recuperar suas informações.
@app.route('/api/products/<product_id>', methods=['GET'])
def get_product_details(product_id):
    product = Product.query.get_or_404(product_id)
    if product:
        return jsonify({
            'id': product.id,
            'name': product.name,
            'price': product.price,
            'description': product.description
        })
    return jsonify({'error': 'Product not found'}), 404

#Definindo a rota para atualizar um produto, onde um usuário autenticado pode enviar o ID do produto e os novos dados para atualizá-lo.
@app.route('/api/products/update/<int:product_id>', methods=['PUT'])
@login_required
def update_product(product_id):
    product = Product.query.get(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
    
    data = request.json
    if 'name' in data:
        product.name = data['name']
    
    if 'price' in data:
        product.price = data['price']
    
    if 'description' in data:
        product.description = data['description']
    
    db.session.commit()

    return jsonify({'message': 'Product updated successfully'})

#Definindo a rota para listar todos os produtos, onde um usuário pode recuperar a lista de todos os produtos disponíveis na aplicação.
@app.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    products_list = []
    for product in products:
        product_data = {
            'id': product.id,
            'name': product.name,
            'price': product.price,
        }
        products_list.append(product_data)
    return jsonify(products_list)

#Definindo a rota para o checkout do carrinho de compras, onde um usuário autenticado pode finalizar a compra dos itens em seu carrinho. Se o checkout for bem-sucedido, os itens do carrinho serão removidos do banco de dados e uma mensagem de sucesso será retornada. Caso contrário, uma mensagem de erro será retornada indicando que o checkout falhou.

@app.route('/api/cart/add/<int:product_id>', methods=['POST'])
@login_required
def add_to_cart(product_id):
    user  = User.query.get(int(current_user.id))
    product = Product.query.get(product_id)

    if user and product:
        cart_item = cartItem(user_id=user.id, product_id=product.id)
        db.session.add(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item added to cart successfully'})
    return jsonify({'error': 'Failed to add item to cart'}), 400

@app.route('/api/cart/remove/<int:product_id>', methods=['DELETE'])
@login_required
def remove_from_cart(product_id):
    cart_item = cartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if cart_item:
        db.session.delete(cart_item)
        db.session.commit()
        return jsonify({'message': 'Item removed from cart successfully'})
    return jsonify({'message': 'Failed to remove item from cart'}), 400

   
@app.route('/api/cart', methods=['GET'])
@login_required
def view_cart():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart
    cart_content = []
    for cart_item in cart_items:
        product = Product.query.get(cart_item.product_id)
        cart_content.append({
    "id": cart_item.id,
    "user_id": cart_item.user.id,
    "product_id": cart_item.product_id,
    "product_name": product.name,
    "product_price": product.price
  })
    return jsonify(cart_content)

@app.route('/api/cart/checkout', methods=['POST'])
@login_required
def checkout():
    user = User.query.get(int(current_user.id))
    cart_items = user.cart 
    for cart_item in cart_items:
        db.session.delete(cart_item)
    db.session.commit()    
    return jsonify({'message': 'Checkout successful'})

#Para fazer o Deploy da aplicação de exemplo, utiliza-se o serviço da AWS para implementar a aplicação Flask. O processo envolve a criação de uma instância EC2, configuração do ambiente, instalação das dependências necessárias, implantação do código da aplicação e configuração do servidor web para servir a aplicação Flask. Após a implantação, a aplicação estará acessível publicamente através do endereço IP ou domínio associado à instância EC2.
#Utilizando o Elastic Beanstalk da AWS, é possível implantar a aplicação Flask de forma simplificada. O Elastic Beanstalk gerencia automaticamente a infraestrutura subjacente, como servidores, balanceadores de carga e escalabilidade, permitindo que os desenvolvedores se concentrem no código da aplicação. Para implantar a aplicação Flask usando o Elastic Beanstalk, basta criar um ambiente, configurar as opções de implantação e enviar o código da aplicação. O Elastic Beanstalk cuidará do restante, garantindo que a aplicação esteja disponível e funcionando corretamente na nuvem da AWS.



if __name__ == "__main__":
    app.run(debug=True)