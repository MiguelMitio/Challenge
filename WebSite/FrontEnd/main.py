from flask import Flask, render_template, url_for, session, request, redirect
import requests
import pandas as pd
import json
import random as rd
import uuid
from flask_cors import CORS
app = Flask(__name__)

# Chave secreta para o Flask trabalhar com sessões
key = 'c12390udsanc]~,kj.ç~/p;09~[65+6821323,dsdje]d~[""210o3i"ds/*-]/;.,~[==-009()((&%T¨¨$&*!@$¨#*&]))'

# Configurações de sessão
app.config['SECRET_KEY'] = key

# Caminho para o arquivo Excel
EXCEL_PATH = "sessions_data.xlsx"

state,city = '',''

# Global variable to store the result of the request
result = ''

def save_to_excel(data, type):
    """Salva os dados da sessão em um arquivo Excel."""
    try:
        # Se o arquivo já existir, leia-o
        df = pd.read_excel(EXCEL_PATH, engine='openpyxl')
    except FileNotFoundError:
        # Se o arquivo não existir, crie um novo DataFrame
        df = pd.DataFrame(columns=["session_id", "state", "city", "deficiencies", "list_sports", "list_aptitude"])

    if type == 'aptitude':
        # Crie um registro que armazenará os dados da sessão atual
        new_row = pd.DataFrame([data])  # Converta o dicionário de dados em um DataFrame
        df = pd.concat([df, new_row], ignore_index=True)
    else:
        print('Entrou')
        # Atualize o registro que armazenará os dados da sessão atual com o estado e cidade
        df.loc[df['session_id'] == data['session_id'], ['state', 'city']] = data['state'], data['city']

    # Salve o DataFrame atualizado no arquivo Excel
    df.to_excel(EXCEL_PATH, index=False, engine='openpyxl')


# Rotas
@app.route('/')
def sobre():
    session.clear()
    return render_template('formulario.html')

@app.route('/institutos')
def institutos():
    return render_template('institutos.html')

@app.route('/mapa')
def mapa():
    # Coordenadas de exemplo
    center_coords = [-23.550520, -46.633308]  # São Paulo

    markerLocations = [
    {"coords": [-23.550520, -46.633308], 
     "description": "<h3 style='font-size: 1.5em; font-weight: bold;'>Academia para tênis de mesa</h3><p>Email: exemplo@academia.com</p>Rua:Santa Teresa, 187<p>Contato: (11) 1234-5678</p>"},
    {"coords": [-22.906847, -43.172896], 
     "description": "<h3 style='font-size: 1.5em; font-weight: bold;'>Ginásio de Judô</h3><p>Email: judo@ginasio.com</p><p>Rua:Av. Pres. Antônio Carlos, 100<p>Contato: (21) 9876-5432</p>"}]

    return render_template('mapa.html', center=center_coords, markers=markerLocations)

@app.route('/central')
def central():
    global result
    
    for sport in result:
        sport["gif_path"] = f"FrontEnd/migs/{sport['name']}.gif"

    return render_template('central.html', resultado=result)

@app.route('/verificar', methods=['POST'])
def verificar():

    session['uid'] = str(uuid.uuid4())

    deficiency = request.form.getlist('deficiency')

    session['deficiencies'] = deficiency

    try:
        req = requests.get('https://backendcds.azurewebsites.net/' + '/'.join(map(str, deficiency)))
        req.raise_for_status()  # Raises an exception for 4xx and 5xx status codes

        global result
        # Convert the response text to a list of dictionaries
        result = json.loads(req.text)
        print(req.text)

        # Salve os dados da sessão no Excel
        session_data = {
            "session_id": session['uid'],
            "deficiencies": ', '.join(deficiency),
            "list_sports": ', '.join([sport["name"] for sport in result]),
            "list_aptitude": ', '.join([sport["aptitude"] for sport in result])
        }
        save_to_excel(session_data, 'aptitude')

        return redirect(url_for('central'))
    
    except requests.exceptions.RequestException as e:
        return "Error: Unable to fetch data from the server. Details: " + str(e)


@app.route('/state', methods=['GET'])
def set_state():
    session['state'] = request.args.get('state')
    session['city'] = request.args.get('city')
    
    # Salve os dados da sessão no Excel
    session_data = {
        "session_id": session['uid'],
        "state": session['state'],
        "city": session['city']
    }

    print(session_data)

    save_to_excel(session_data, '')

    return redirect(url_for('mapa'))

    
CORS(app, resources={r"/*": {"origins": "frontendcds.azurewebsites.net"}})

# Botão iniciar do sobre 
@app.route('/iniciar', methods=['GET'])
def iniciar():
    return redirect(url_for('formulario'))

if __name__ == '__main__':
    app.run(debug=True)
