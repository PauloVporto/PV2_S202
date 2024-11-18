'''
Nessa atividade você deve usar seus conhecimentos sobre banco de dados baseados em colunos e chave-valor, mais especificamente sobre Cassandra e Redis para atender os requisitos pedidos.
Todos as questões tem um exemplo de caso de teste (com dados de entrada e saída esperada) para que você valide a sua solução.

Contexto: Imagine que você está desenvolvendo um banco de dados para uma loja online. Essa loja tem um volume muito grande de vendas e por isso foram escolhidos sistemas de gerenciamento de bancos de dados NoSQL. Os principais objetivos do sistema são: 
i) exibir uma lista de produtos mais recomendados para um determinado usuário; 
ii) armazenar tenoirariamente as informações de produtos no carrinho; e 
iii) registrar as informações de uma venda efetivada.

Para manter as informações das vendas realizadas de forma persistente e distribuída, a tabela de vendas, produtos e usuários foram registrados no Cassandra. 
Apesar de ter um esquema flexível, considere as seguintes informações:
    . Usuário (id: int, estado: text, cidade: text, endereço: text, nome: text, email: text, interesses: list<text>)
    . Produto (id: int, categoria: text, nome: text, custo: int, preco: int, quantidade: int)
    . Venda (id: int, dia: int, mês: int, ano: int, hora: text, valor: int, produtos: list<map<int, int>>, usuario: map<text, text>)
Os dados de usuários devem ser particionados pelo estado e cidade, usando o id para complementar a idenficação.
Produtos devem ser agrupadors por categoria, também usando id para ordenar os produtos em uma mesma partição.
Por fim, os dados das vendas devem ser particionados por dia, mês e ano, usando a hora e o id para complementar a idenficação de uma venda.

A fim de manter consultas rápidas, algumas informações do usuário, suas preferências e seus produtos em carrinho são mantidas no Redis.

---------------------------------------------------------------------------------------------------------------

(20 pontos) Questão 1)
Crie as tabelas e registe as informações dos seguintes usuários e produtos no Cassandra e realize a consutla no Cassandra para apresentar:
a) a quantidade de usuários registrados e 
b) a custo total dos produtos em estoque (obs.: o custo registrado é apenas o custo unitário de cada produto).

    ### Dica: Use valores inteiros ao armazenar os valores monetários no Cassandra (basta multiplicar por 100 na hora de inserir e dividir por 100 quando for apresentar)

(20 pontos) Questão 2)
Carregue do Cassandra as informações de cada um dos usuários do estado de Minas Gerais, incluindo a lista de interesses, registre no Redis e realize a consutla no Redis para apresentar os dados registrados.

(30 pontos) Questão 3) 
Imagine que o usuário 3 acessa o feed dele. Use a lista de interesses desse usuário registrada no Redis para buscar as informações sobre produtos mais interessantes no Cassandra (considere que a lista de interesses contém os nomes das categorias de produtos interessantes).

(10 pontos extras) Questão 4) 
O usuário 3 seleciona alguns produtos para o seu carrinho. Registre essas informações no Redis e realize uma consulta para mostrar os dados cadastrados.

(10 pontos extras) Questão 5)
O usuário 3 efetiva a compra dos produtos em seu carrinho. Realize uma consulta no Redis dos dados do carrinho desse usuário e registre as informações sobre essa venda no Cassandra (considere que a data e a hora vão ser passadas como parâmetro). Por fim recupere e retorne o nome do usuário, a hora e o valor das vendas  realizadas no dia atual registradas no Cassadra.
    ## Dica: Use alias para formatar o retorno. Não esqueça de converter o valor monetário.


'''
import json

from datetime import datetime

from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from cassandra.query import dict_factory

import redis


# This secure connect bundle is autogenerated when you download your SCB, 
# if yours is different update the file name below
cloud_config= {
  'secure_connect_bundle': 'secure-connect.zip'
}

# This token JSON file is autogenerated when you download your token, 
# if yours is different update the file name below
with open("token.json") as f:
    secrets = json.load(f)

CLIENT_ID = secrets["clientId"]
CLIENT_SECRET = secrets["secret"]

auth_provider = PlainTextAuthProvider(CLIENT_ID, CLIENT_SECRET)
cluster = Cluster(['127.0.0.1'], port=9042)
cassandra_session = cluster.connect()
cassandra_session.row_factory = dict_factory # Returning dict from Cassandra
cassandra_session.set_keyspace('ks') # Change to your keyspace

redis_conn = redis.Redis(
    host="...", port=0, #Use your Redis instance host and port
    username="default", # use your Redis user. 
    password="...", # use your Redis password
    decode_responses=True
)

# ------------------- !! Attention !! -------------------
redis_conn.flushall() #Clear Redis database 
# -------------------------------------------------------

# Questão 1
def questao_1_a(users):
    cassandra_session.execute("DROP TABLE IF EXISTS usuarios;")
    query_usuarios = ''' 
        CREATE TABLE usuarios( 
            id int, 
            estado text, 
            cidade text, 
            endereco text, 
            nome text,
            email text,
            interesses list<text>,
            primary key((estado), cidade, endereco, id)
        );
    '''

    cassandra_session.execute(query_usuarios)
    cassandra_session.execute("TRUNCATE usuarios;")
    
    query = """ INSERT INTO usuarios(id, estado, cidade, endereco, nome, email, interesses) VALUES (%s, %s, %s, %s, %s, %s, , %s) """
    for user in users:
        cassandra_session.execute(query, (user['id'], user['estado'], user['cidade'], user['endereco'], user['nome'], user['email'], user['interesses']))
    
    query = """ SELECT AVG(quantidade) FROM usuarios; """
    result = cassandra_session.execute(query).one()
    return result
    

def test_questao_1_a():

    users = [
        {"id":1, "estado": "Minas Gerais", "cidade": "Santa Rita do Sapucaí", "endereco": "Rua A, 45", "nome":"Serafim Amarantes", "email":"samarantes@g.com", "interesses": ["futebol", "pagode", "engraçado", "cerveja", "estética"]},
        {"id":2, "estado": "São Paulo", "cidade": "São Bento do Sapucaí", "endereco": "Rua B, 67", "nome":"Tamara Borges", "email":"tam_borges@g.com", "interesses": ["estética", "jiujitsu", "luta", "academia", "maquiagem"]},
        {"id":3, "estado": "Minas Gerais", "cidade": "Santa Rita do Sapucaí", "endereco": "Rua C, 84", "nome":"Ubiratã Carvalho", "email":"bira@g.com", "interesses": ["tecnologia", "hardware", "games", "culinária", "servers"]},
        {"id":4, "estado": "Minas Gerais", "cidade": "Pouso Alegre", "endereco": "Rua D, 21", "nome":"Valéria Damasco", "email":"valeria_damasco@g.com", "interesses": ["neurociências", "comportamento", "skinner", "laboratório", "pesquisa"]}
    ]

    assert len(users) == questao_1_a(users)

def questao_1_b(products):
    cassandra_session.execute("DROP TABLE IF EXISTS products;")
    query_produtos = ''' 
    CREATE TABLE produtos( 
        id int, 
        categoria text, 
        nome text, 
        custo int, 
        preco int,
        quantidade int,
        primary key((categoria), nome, custo, id)
    );
    '''
    
    cassandra_session.execute(query_produtos)
    cassandra_session.execute("TRUNCATE produtos;")
    
    query = """ INSERT INTO produtos(id, categoria, nome, custo, preco, quantidade) VALUES (%s, %s, %s, %s, %s, %s) """
    for product in products:
        cassandra_session.execute(query, (product['id'], product['categoria'], product['nome'], product['custo'], product['preco'], product['quantidade']))

    query = """ SELECT SUM(quantidade) FROM produtos; """
    result = cassandra_session.execute(query).one()
    return result
    
def teste_questao_1_b():
    products = [
        {"id":1, "categoria": "escritório", "nome":"Cadeira HM conforto", "custo": 2000.00, "preco": 3500.00, "quantidade": 120},
        {"id":2, "categoria": "culinária", "nome":"Tábua de corte Hawk", "custo": 360.00, "preco": 559.90, "quantidade": 40},
        {"id":3, "categoria": "tecnologia", "nome":"Notebook X", "custo": 3000.00, "preco": 4160.99, "quantidade": 76},
        {"id":4, "categoria": "games", "nome":"Headset W", "custo": 265.45, "preco": 422.80, "quantidade": 88},
        {"id":5, "categoria": "tecnologia", "nome":"Smartphone X", "custo": 2000.00, "preco": 3500.00, "quantidade": 120},
        {"id":6, "categoria": "games", "nome":"Gamepad Y", "custo": 256.00, "preco": 519.99, "quantidade": 40},
        {"id":7, "categoria": "estética", "nome":"Base Ismusquim", "custo": 50.00, "preco": 120.39, "quantidade": 76},
        {"id":8, "categoria": "cerveja", "nome":"Gutten Bier IPA 600ml", "custo": 65.45, "preco": 122.80, "quantidade": 88}
    ]

    total_cost = 765559.20
    
    assert total_cost == questao_1_b(products)

# Questão 2
def questao_2(state):
    query = f""" SELECT * FROM usuarios WHERE estado = {state} ALLOW FILTERING; """
    result = cassandra_session.execute(query).all()
    results = []
    if result is not None:
        for r in result:
            redis_conn.hmset(f'id:{r['id']}', r)
            results.append(redis_conn.hgetall(f"id:{result['id']}"))
    
    return results


def test_questao_2():

    state = "Minas Gerais"

    users = [
        {"id":'1', "estado": "Minas Gerais", "cidade": "Santa Rita do Sapucaí", "endereco": "Rua A, 45", "nome":"Serafim Amarantes", "email":"samarantes@g.com", "interesses": ["futebol", "pagode", "engraçado", "cerveja", "estética"]},
        {"id":'3', "estado": "Minas Gerais", "cidade": "Santa Rita do Sapucaí", "endereco": "Rua C, 84", "nome":"Ubiratã Carvalho", "email":"bira@g.com", "interesses": ["tecnologia", "hardware", "games", "culinária", "servers"]},
        {"id":'4', "estado": "Minas Gerais", "cidade": "Pouso Alegre", "endereco": "Rua D, 21", "nome":"Valéria Damasco", "email":"valeria_damasco@g.com", "interesses": ["neurociências", "comportamento", "skinner", "laboratório", "pesquisa"]}
    ]

    assert users == sorted(questao_2(state), key=lambda d: d['id'])


# Questão 3
def questao_3(user_id):
    interests = redis_conn.zrange(f"id:{user_id}:interests", 0, -1, withscores=True)
    query = """ SELECT * FROM produtos ALLOW FILTERING; """
    produtos = cassandra_session.execute(query).all()
    
    produto_score = []
    for produto in produtos:
        produto_keywords = produto["categoria"].split(", ")
        score = sum([score for keyword, score in interests if keyword in produto_keywords])
        produto_score.append((score, produto["conteudo"]))
    
    produto_score.sort(reverse=True, key=lambda x: x[0])
    filtered_produtos = [produto for score, produto in produto_score]
    print(filtered_produtos)
    return filtered_produtos

def test_questao_3():

    user_id = 3

    products = [
        {"id":2, "nome":"Tábua de corte Hawk", "preco": 559.90},
        {"id":3, "nome":"Notebook X", "preco": 4160.99},
        {"id":4, "nome":"Headset W", "preco": 422.80},
        {"id":5, "nome":"Smartphone X", "preco": 3500.00},
        {"id":6, "nome":"Gamepad Y", "preco": 519.99}
    ]

    assert products == sorted(questao_3(user_id), key=lambda d: d['id'])


# Questão 4
def questao_4(user_id, cart):
    pass

def test_questao_4():

    user_id = 3
    
    cart = [
        {"id":'4', "nome":"Headset W", "preco": '422.80', "quantidade": '1'},
        {"id":'6', "categoria": "games", "nome":"Gamepad Y", "preco": '519.99', "quantidade": '2'},
    ]

    assert cart == sorted(questao_4(user_id, cart), key=lambda d: d["id"])

# Questão 5
def questao_5(user_id):
    pass

def test_questao_5():

    user_id = 3
    date_time = datetime.now()

    sales = [{"usuario": 'bira@g.com', 'hora': date_time.strftime("%H:%M"), 'valor': 1462.78}]

    assert sales == questao_5(user_id, date_time)


# cassandra_session.shutdown()
# redis_conn.close()