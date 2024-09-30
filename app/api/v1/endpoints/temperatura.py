import asyncio
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.database import get_db
from app.models.temperaturaModel import TemperatureCreate
from app.schemas.Temperatura import Temperature as TemperatureModel
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from contextlib import asynccontextmanager


router = APIRouter()

executor = ThreadPoolExecutor(max_workers=1)

# Função para salvar no banco de dados
async def save_to_db(value, session: AsyncSession):
    try:
        # Remover o timezone do timestamp para evitar erros na inserção
        timestamp = datetime.utcnow().replace(tzinfo=None)
        db_temperature = TemperatureModel(value=value, timestamp=timestamp)
        session.add(db_temperature)
        await session.commit()
        await session.refresh(db_temperature)
        print(f"Valor {value} salvo no banco de dados com sucesso.")
    except Exception as e:
        print(f"Erro ao salvar no banco de dados: {e}")
        await session.rollback()

# Criar uma função que retorna um "async context manager" para get_db
@asynccontextmanager
async def get_db_session():
    db_session = get_db()
    async for session in db_session:
        try:
            yield session
        finally:
            await session.close()

# Função intermediária para pegar a sessão do banco e chamar save_to_db
async def save_to_db_middleware(value):
    async with get_db_session() as session:
        print("Salvando no banco de dados via MQTT...")
        await save_to_db(value, session)

# Função que será chamada quando uma mensagem MQTT for recebida
def on_message(client, userdata, msg):
    try:
        print(f"Mensagem recebida no tópico: {msg.topic}")
        payload = json.loads(msg.payload.decode("utf-8"))
        value = payload.get("value", None)
        if value is not None:
            print(f"Received temperature: {value}")
            # Rodar a operação de banco de dados em um thread separado
            loop = asyncio.get_event_loop()
            loop.run_in_executor(executor, asyncio.run, save_to_db_middleware(value))

        else:
            print("Nenhum valor encontrado na mensagem MQTT.")

    except json.JSONDecodeError:
        print("Erro ao decodificar a mensagem.")
    except Exception as e:
        print(f"Erro ao processar a mensagem: {e}")

# Configura o cliente MQTT para conectar ao broker e assinar o tópico
def mqtt_client_setup():
    client = mqtt.Client()
    client.on_message = on_message
    client.connect("localhost", 1883, 60)
    client.subscribe("sensor/temperatura")
    client.loop_start()
    print("Cliente MQTT iniciado e aguardando mensagens...")
    return client

# Inicializa o cliente MQTT quando a aplicação inicia
@router.on_event("startup")
async def startup_event():
    mqtt_client_setup()

# Endpoint FastAPI para publicar a temperatura no broker MQTT
@router.post("/publish-temperature")
async def publish_temperature(temperature: TemperatureCreate, db: AsyncSession = Depends(get_db)):
    mqtt_client = mqtt_client_setup()
    payload = {"value": temperature.value}
    mqtt_client.publish("sensor/temperatura", json.dumps(payload))
    print(f"Temperatura {temperature.value} publicada no tópico MQTT.")

    # Corrigir o timestamp para remover o timezone ao salvar no banco via API
    timestamp = datetime.utcnow().replace(tzinfo=None)
    db_temperature = TemperatureModel(value=temperature.value, timestamp=timestamp)
    db.add(db_temperature)
    await db.commit()
    await db.refresh(db_temperature)

    print("Temperatura salva no banco de dados via API.")

    return {"message": "Temperatura enviada e armazenada com sucesso", "data": db_temperature}
