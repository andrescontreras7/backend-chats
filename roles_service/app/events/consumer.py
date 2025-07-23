import aio_pika
import json
from controllers.role_controller import assign_default_role

RABBITMQ_URL = "amqp://admin:admin@rabbitmq/"

async def consume_user_created():
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    channel = await connection.channel()
    queue = await channel.declare_queue("user.created", durable=True)

    async with queue.iterator() as queue_iter:
        async for message in queue_iter:
            async with message.process():
                body = json.loads(message.body)
                user_id = body.get("user_id")
                if user_id:
                    await assign_default_role(user_id)
