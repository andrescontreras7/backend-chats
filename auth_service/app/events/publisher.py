import asyncio
import json
import aio_pika
import os
from typing import Dict

# Configuración de RabbitMQ
RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")

async def publish_user_created(user_data: Dict):
    """Publicar evento cuando se crea un usuario"""
    try:
        # Conectar a RabbitMQ
        connection = await aio_pika.connect_robust(RABBITMQ_URL)
        
        async with connection:
            # Crear canal
            channel = await connection.channel()
            
            # Declarar exchange
            exchange = await channel.declare_exchange(
                "user_events", 
                aio_pika.ExchangeType.FANOUT,
                durable=True
            )
            
            # Crear mensaje
            message = aio_pika.Message(
                json.dumps(user_data).encode(),
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            )
            
            # Publicar mensaje
            await exchange.publish(message, routing_key="user.created")
            
            print(f"✅ Evento user_created publicado: {user_data['user_id']}")
            
    except Exception as e:
        # En caso de error, no fallar la creación del usuario
        print(f"⚠️ Error publicando evento user_created: {e}")
        # No hacer raise para que el registro del usuario continúe
