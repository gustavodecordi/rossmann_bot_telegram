import pandas as pd
import json
import requests
from flask import Flask, request, Response
import os

# Token do Bot no Telegram
TOKEN = '6261340710:AAEv_50R7DVnvd1aNmLmZ9c2Bh9brBVMrKs'

# # Info about the Bot
# https://api.telegram.org/bot6261340710:AAEv_50R7DVnvd1aNmLmZ9c2Bh9brBVMrKs/getMe
        
# # get updates
# https://api.telegram.org/bot6261340710:AAEv_50R7DVnvd1aNmLmZ9c2Bh9brBVMrKs/getUpdates
        
# # send message
# https://api.telegram.org/bot6261340710:AAEv_50R7DVnvd1aNmLmZ9c2Bh9brBVMrKs/sendMessage?chat_id=6105587379&text=Hi Gustavo, I am doing good, tks!

# # Webhook
# https://api.telegram.org/bot6261340710:AAEv_50R7DVnvd1aNmLmZ9c2Bh9brBVMrKs/setWebhook?url=

def send_message( chat_id, text ):
    url = 'https://api.telegram.org/bot{}/'.format( TOKEN )
    url = url + 'sendMessage?chat_id={}'.format( chat_id )
    
    # API request using POST method 
    r = requests.post( url, json = {'text': text} )
    print( 'Status Code {}'.format( r.status_code ) )
    
    return None
      
def load_dataset( store_id ):
    # loading test dataset
    df10 = pd.read_csv( 'test.csv', low_memory = False )
    df_store_raw = pd.read_csv( 'store.csv', low_memory = False )

    # merge test dataset + store (para ter as mesmas features usadas para fazer as predicoes)
    df_test = pd.merge( df10, df_store_raw, how = 'left', on = 'Store' )

    # escolha uma loja 
    df_test = df_test[df_test['Store'] == store_id ]
    
    if not df_test.empty:
        # somente as lojas que estao abertas
        df_test = df_test[df_test['Open'] == 1]
        # lojas sem dados faltantes na coluna 'Open'
        df_test = df_test[ ~df_test['Open'].isnull() ]
        # retira a coluna 'Id' 
        df_test = df_test.drop( 'Id', axis = 1 )
    
        # converte o DataFrame em json para o envio via API
        data = json.dumps( df_test.to_dict( orient = 'records' ) )
    
    else:
        data = 'error'
        
    return data

def predict( data ):
    # Chamada para a API
    url = 'https://teste-rossmann-api-ojfz.onrender.com/rossmann/predict'
    # indica para a API o tipo de requisicao que estamos fazendo
    header = {'Content-type' : 'application/json'}
    # dado enviado
    data = data

    # requisicao
    r = requests.post( url, data = data, headers = header )
    print( 'Status Code {}'.format( r.status_code ) )

    # cria um objeto DataFrame a partir da lista de dicionarios
    d1 = pd.DataFrame( r.json(), columns = r.json()[0].keys() )
    
    return d1

def parse_message( message ):
    chat_id = message['message']['chat']['id']
    store_id = message['message']['text']
    
    store_id = store_id.replace( '/', '' )
    
    try:
        store_id = int( store_id )
        
    except ValueError:
        store_id = 'error'
        
    return chat_id, store_id

# API initialize
app = Flask( __name__ )

@app.route( '/', methods = ['GET', 'POST'] )
def index():
    if request.method == 'POST':
        message = request.get_json()
        chat_id, store_id = parse_message( message )
        
        if store_id != 'error':
            # loading data
            data = load_dataset( store_id )
            
            if data != 'error':
                # prediction
                d1 = predict( data )

                # Calculation
                # DataFrame que contem a soma das previsoes de vendas por loja
                d2 = d1[['store','prediction']].groupby(['store']).sum().reset_index()
                
                msg = 'Store number {} will sell R${:,.2f} in the next six weeks'.format(
                                                                                         d2['store'].values[0],
                                                                                         d2['prediction'].values[0]
                                                                                        )
                send_message( chat_id, msg )
                return Response( 'Ok', status = 200 )
            
            else: 
                send_message( chat_id, 'Store Not Available' )
                return Response( 'Ok', status = 200 )
        
        else:
            send_message( chat_id, 'Store ID Wrong' )
            return Response( 'Ok', status = 200 ) 
        
    else:
        return '<h1> Rossmann Telegram BOT </h1>'
    
    
if __name__ == '__main__':
    # o servidor Flask eh iniciado para escutar a API
    port = os.environ.get( 'PORT', 5000 )
    app.run( host='0.0.0.0', port=port )